"""
Cliente de OpenAI para generar respuestas del chatbot
Con soporte para Function Calling (herramientas)
"""
from openai import OpenAI
import openai
from typing import Any, Dict, List, Optional
import config
import json
import os
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from cosmos_client import get_memory_store


class ChatbotAI:
    """Gestiona la generación de respuestas con OpenAI"""
    
    def __init__(self):
        """Inicializa el cliente de OpenAI y carga prompts dinámicamente desde Cosmos DB."""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.memory_store = get_memory_store()
        # Si la cuenta queda sin cuota, evitamos golpear la API en cada mensaje (reduce latencia/ruido).
        self._openai_disabled_until: Optional[datetime] = None
        self._openai_disabled_reason: Optional[str] = None
        
        # Importar herramientas
        from hernando_tools import get_hernando_tools
        self.tools_manager = get_hernando_tools()
        
        # Cargar prompts dinámicamente desde Cosmos DB; fallback a embebidos
        from prompts_loader import get_prompts_loader
        
        # Defaults embebidos (usado como fallback si Cosmos no responde)
        self._default_system_prompt = "Eres Hernando, anfitrión virtual de Fundo Moraga. Ayuda con información sobre actividades, reservas y servicios en español chileno cercano y natural."
        self._default_operational_prompt = "Sé proactivo. Pide datos para reservar (fecha/hora, vehículos, contacto). Llama a herramientas solo cuando sea necesario."
        
        # Cargar dinámicamente desde Cosmos DB
        loader = get_prompts_loader()
        prompts = loader.get_prompts(
            persona="Hernando",
            fallback_system_prompt=self._default_system_prompt,
            fallback_operational_prompt=self._default_operational_prompt,
            fallback_tools=self.tools_manager.tools,
        )
        
        self.system_prompt = prompts["system"]
        self.operational_prompt = prompts["operational"]
        self.dynamic_tools: List[Dict[str, Any]] = prompts.get("tools", [])
        # Preferir tools desde Cosmos; fallback a definiciones locales
        self.tools: List[Dict[str, Any]] = self.dynamic_tools if self.dynamic_tools else self.tools_manager.tools

    def _now_local(self) -> datetime:
        tz_name = getattr(config, "GOOGLE_CALENDAR_TIMEZONE", None) or "America/Santiago"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        return datetime.now(tz)

    def _weekday_es(self, dt: datetime) -> str:
        names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return names[dt.weekday()]

    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        platform: Optional[str] = None,
        already_welcomed: Optional[bool] = None,
        lead_capture_already_sent: Optional[bool] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": self.system_prompt}]

        context_lines = []
        now_local = self._now_local()
        context_lines.append(f"today_date={now_local.date().isoformat()}")
        context_lines.append(f"today_weekday_es={self._weekday_es(now_local)}")
        context_lines.append(f"timezone={getattr(config, 'GOOGLE_CALENDAR_TIMEZONE', 'America/Santiago')}")

        # Excepción comercial: este domingo está abierto con tarifa normal (ver reglas).
        days_ahead = (6 - now_local.weekday()) % 7  # Sunday=6
        special_sun = now_local.date() + timedelta(days=days_ahead)
        context_lines.append(f"special_open_sunday_date={special_sun.isoformat()}")
        context_lines.append("special_open_sunday_hours=10:00-17:00")
        context_lines.append("special_open_sunday_price_vehicle_clp=15000")
        context_lines.append("special_open_sunday_price_moto_clp=10000")
        if conversation_id:
            context_lines.append(f"conversation_id={conversation_id}")
        if platform:
            context_lines.append(f"platform={platform}")
        if already_welcomed is not None:
            context_lines.append(f"already_welcomed={'true' if already_welcomed else 'false'}")
        if lead_capture_already_sent is not None:
            context_lines.append(f"lead_capture_already_sent={'true' if lead_capture_already_sent else 'false'}")

        if extra_context:
            for k, v in extra_context.items():
                if v is None:
                    continue
                key = str(k).strip()
                if not key:
                    continue
                # Limitar tamaño para evitar inflar el prompt con datos enormes
                value = str(v).strip()
                if not value:
                    continue
                if len(value) > 400:
                    value = value[:400] + "…"
                context_lines.append(f"{key}={value}")

        if user_id:
            # Inyectar memoria: hechos, precios y resúmenes recientes.
            memory_lines: List[str] = []
            facts = self.memory_store.list_facts(limit=5)
            for f in facts:
                key = f.get("key")
                val = f.get("value")
                scope = f.get("scope") or "global"
                if key and val:
                    memory_lines.append(f"fact[{scope}]: {key}={val}")
                    if len(memory_lines) >= 5:
                        break

            prices = self.memory_store.list_prices(limit=5)
            for p in prices:
                prod = p.get("product")
                price = p.get("price")
                curr = p.get("currency") or "CLP"
                if prod and price is not None:
                    memory_lines.append(f"price: {prod}={price} {curr}")
                    if len(memory_lines) >= 10:
                        break

            summaries = self.memory_store.get_conversation_summaries(user_id=user_id, limit=3)
            for s in summaries:
                cid = s.get("conversationId")
                summary = s.get("summary")
                if summary:
                    memory_lines.append(f"summary[{cid}]: {summary}")
                    if len(memory_lines) >= 13:
                        break

            if memory_lines:
                context_lines.append("MEMORIA")
                context_lines.extend(memory_lines)

        if context_lines:
            messages.append({"role": "system", "content": "CONTEXTO\n" + "\n".join(context_lines)})

        messages.append({"role": "system", "content": self.operational_prompt})

        if conversation_history:
            for msg in conversation_history[-config.MAX_CONVERSATION_HISTORY :]:
                metadata = msg.get("metadata") or {}
                if metadata.get("type") in ("booking_state", "lead_capture"):
                    continue

                role = msg.get("role", "user")
                content = (msg.get("message") or "").strip()
                if not content:
                    continue

                if role not in ("system", "user", "assistant", "tool"):
                    role = "user"

                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})
        return messages

    def _openai_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _openai_error_payload(self, exc: Exception) -> Dict[str, Any]:
        """
        Intenta extraer el payload estándar de errores de OpenAI:
        {'error': {'message': ..., 'type': ..., 'code': ...}}
        """
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                return err
            # A veces `body` ya viene como dict con claves de error.
            return body
        return {}

    def _classify_openai_exception(self, exc: Exception) -> Dict[str, Any]:
        """
        Clasifica errores para decidir si tiene sentido intentar modelos fallback.
        """
        payload = self._openai_error_payload(exc)
        status_code = getattr(exc, "status_code", None)
        code = (payload.get("code") or payload.get("type") or "").strip()
        message = (payload.get("message") or "").strip()
        text = (str(exc) or "").lower()

        code_l = code.lower()
        msg_l = message.lower()

        # Caso típico: cuenta sin saldo/cuota. Probar otros modelos NO ayuda.
        if (
            "insufficient_quota" in code_l
            or "insufficient_quota" in text
            or "you exceeded your current quota" in msg_l
            or "check your plan and billing details" in msg_l
        ):
            return {"type": "insufficient_quota", "status_code": status_code, "code": code, "message": message}

        if isinstance(exc, openai.AuthenticationError):
            return {"type": "auth_error", "status_code": status_code, "code": code, "message": message}

        if isinstance(exc, openai.PermissionDeniedError):
            return {"type": "permission_denied", "status_code": status_code, "code": code, "message": message}

        # Rate limit real (no cuota): seguir con fallbacks no siempre ayuda, pero no bloquea.
        if isinstance(exc, openai.RateLimitError) or status_code == 429:
            return {"type": "rate_limited", "status_code": status_code, "code": code, "message": message}

        if isinstance(exc, openai.BadRequestError):
            return {"type": "bad_request", "status_code": status_code, "code": code, "message": message}

        if isinstance(exc, openai.APIConnectionError):
            return {"type": "connection_error", "status_code": status_code, "code": code, "message": message}

        if isinstance(exc, openai.APIStatusError):
            return {"type": "api_status_error", "status_code": status_code, "code": code, "message": message}

        return {"type": "unknown", "status_code": status_code, "code": code, "message": message}

    def _should_skip_openai(self) -> Optional[Dict[str, Any]]:
        if not self._openai_disabled_until:
            return None
        if self._openai_now() >= self._openai_disabled_until:
            self._openai_disabled_until = None
            self._openai_disabled_reason = None
            return None
        return {
            "type": self._openai_disabled_reason or "temporarily_disabled",
            "disabled_until": self._openai_disabled_until.isoformat(),
        }

    def _model_candidates(self) -> List[str]:
        """
        Retorna una lista de modelos a intentar en orden.
        - Primero: el modelo configurado (OPENAI_MODEL)
        - Luego: OPENAI_MODEL_FALLBACKS (comma/semicolon-separated)
        - Finalmente: fallbacks razonables para mantener el servicio operativo
        """
        candidates: List[str] = []

        if self.model:
            candidates.append(self.model)

        raw = (os.getenv("OPENAI_MODEL_FALLBACKS") or "").strip()
        if raw:
            for part in re.split(r"[;,]", raw):
                m = part.strip()
                if m:
                    candidates.append(m)

        # Heurística: si el usuario configuró algo tipo "gpt-5.2", intenta variantes comunes.
        if self.model and self.model.startswith("gpt-5"):
            candidates.extend(["gpt-5-mini", "gpt-5"])

        # Fallbacks seguros (si están disponibles en la cuenta).
        candidates.extend(["gpt-4.1-mini", "gpt-4o-mini"])

        # De-dup preservando orden
        seen = set()
        unique: List[str] = []
        for m in candidates:
            k = m.strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            unique.append(m.strip())
        return unique

    def _token_param_name(self, model: str) -> str:
        """
        Algunos modelos (p.ej. gpt-5.*) no aceptan `max_tokens` en Chat Completions y exigen
        `max_completion_tokens`.
        """
        m = (model or "").strip().lower()
        if m.startswith("gpt-5"):
            return "max_completion_tokens"
        if m.startswith(("o1", "o3")):
            return "max_completion_tokens"
        return "max_tokens"

    def _generate_with_model(
        self,
        *,
        model: str,
        base_messages: List[Dict[str, str]],
        return_events: bool,
    ) -> Any:
        messages: List[Any] = [dict(m) for m in base_messages]
        events: List[Dict[str, Any]] = []

        max_tool_rounds = 3
        token_param = self._token_param_name(model)
        for _ in range(max_tool_rounds):
            kwargs: Dict[str, Any] = dict(
                model=model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
            )
            kwargs[token_param] = 800
            response = self.client.chat.completions.create(**kwargs)

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                final_text = response_message.content or ""
                if return_events:
                    return {"text": final_text, "events": events, "model_used": model}
                return final_text

            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments or "{}")

                print(f"🔧 Ejecutando herramienta: {function_name}")
                print(f"   Argumentos: {function_args}")

                function_result = self.tools_manager.execute_tool(function_name, function_args)
                events.append({"tool": function_name, "args": function_args, "result": function_result})

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_result),
                    }
                )

        fallback_text = "Listo. ¿En qué más te puedo ayudar?"
        if return_events:
            return {"text": fallback_text, "events": events, "model_used": model}
        return fallback_text
    
    def generate_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict] = None,
        *,
        conversation_id: Optional[str] = None,
        platform: Optional[str] = None,
        user_id: Optional[str] = None,
        already_welcomed: Optional[bool] = None,
        lead_capture_already_sent: Optional[bool] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        return_events: bool = False,
    ) -> Any:
        """
        Genera una respuesta del chatbot con soporte para Function Calling
        
        Args:
            user_message: Mensaje del usuario
            conversation_history: Historial de conversación (opcional)
        
        Returns:
            Respuesta generada por el modelo
        """
        skipped = self._should_skip_openai()
        if skipped:
            error_text = (
                "Lo siento, hubo un problema al procesar tu mensaje. "
                "Por favor, intenta nuevamente o contáctanos directamente en contacto@fundomoraga.com"
            )
            result = {"text": error_text, "events": [], "model_used": None, "error": skipped}
            return result if return_events else error_text

        messages = self._build_messages(
            user_message=user_message,
            conversation_history=conversation_history,
            conversation_id=conversation_id,
            user_id=user_id,
            platform=platform,
            already_welcomed=already_welcomed,
            lead_capture_already_sent=lead_capture_already_sent,
            extra_context=extra_context,
        )

        last_error: Optional[Exception] = None
        last_error_info: Optional[Dict[str, Any]] = None
        for model in self._model_candidates():
            try:
                if model != self.model:
                    print(f"⚠️ Probando modelo fallback: {model} (configurado: {self.model})")
                return self._generate_with_model(model=model, base_messages=messages, return_events=return_events)
            except Exception as e:
                last_error = e
                last_error_info = self._classify_openai_exception(e)
                print(f"❌ Error generando respuesta con OpenAI (model={model}): {e}")

                # Si es un problema de cuota/auth/permisos, probar otros modelos no resolverá.
                if (last_error_info or {}).get("type") in ("insufficient_quota", "auth_error", "permission_denied"):
                    # Backoff suave para no saturar logs/latencia en cada webhook.
                    cooldown_s = int(os.getenv("OPENAI_DISABLE_COOLDOWN_SECONDS", "600"))
                    self._openai_disabled_until = self._openai_now() + timedelta(seconds=max(30, cooldown_s))
                    self._openai_disabled_reason = (last_error_info or {}).get("type") or "disabled"
                    break

        # Evitar tracebacks largos en casos comunes (cuota agotada, auth, permisos).
        if last_error and (last_error_info or {}).get("type") not in ("insufficient_quota", "auth_error", "permission_denied"):
            import traceback
            traceback.print_exception(type(last_error), last_error, last_error.__traceback__)

        error_text = (
            "Lo siento, hubo un problema al procesar tu mensaje. "
            "Por favor, intenta nuevamente o contáctanos directamente en contacto@fundomoraga.com"
        )
        error_meta = last_error_info or {"type": "unknown"}
        return {"text": error_text, "events": [], "model_used": None, "error": error_meta} if return_events else error_text
    
    def generate_response_with_context(
        self, 
        user_message: str, 
        context: str
    ) -> str:
        """
        Genera una respuesta con contexto adicional (útil para RAG)
        
        Args:
            user_message: Mensaje del usuario
            context: Contexto adicional (ej: información de productos)
        
        Returns:
            Respuesta generada
        """
        try:
            enhanced_prompt = f"{self.system_prompt}\n\nContexto adicional:\n{context}"
            
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                **{self._token_param_name(self.model): 500},
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error generando respuesta con contexto: {e}")
            return "Lo siento, hubo un problema al procesar tu mensaje."

    def summarize_lead_interest(
        self,
        *,
        conversation_snippet: str,
        known_name: Optional[str] = None,
        known_contact: Optional[str] = None,
        booking_details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Genera un resumen corto del interés del usuario para uso interno (email/CRM).
        No debe inventar datos: si algo no está explícito, debe omitirlo.
        """
        try:
            sys = (
                "Eres un asistente que redacta resúmenes internos para el equipo de Fundo Moraga.\n"
                "Reglas:\n"
                "- No inventes datos.\n"
                "- Sé breve (2–4 líneas).\n"
                "- Menciona objetivo del usuario y, si aplica, fecha/hora/vehículos.\n"
                "- No incluyas el contacto dentro del resumen (va aparte).\n"
            )

            known_lines = []
            if known_name:
                known_lines.append(f"Nombre: {known_name}")
            if known_contact:
                known_lines.append(f"Contacto: {known_contact}")
            if booking_details:
                try:
                    known_lines.append("Reserva (parcial): " + json.dumps(booking_details, ensure_ascii=False))
                except Exception:
                    known_lines.append(f"Reserva (parcial): {booking_details}")

            user = (
                "Datos conocidos (pueden venir vacíos):\n"
                + ("\n".join(known_lines) if known_lines else "(ninguno)\n")
                + "\n\n"
                "Conversación (fragmento):\n"
                f"{conversation_snippet}\n\n"
                "Escribe el resumen:"
            )

            kwargs: Dict[str, Any] = dict(
                model=self.model,
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
                temperature=0.2,
            )
            kwargs[self._token_param_name(self.model)] = 200
            response = self.client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"❌ Error generando resumen de lead: {e}")
            # Fallback determinístico
            return (conversation_snippet or "").strip()[:400]


# Singleton instance
_chatbot_ai = None

def get_chatbot_ai() -> ChatbotAI:
    """Obtiene la instancia singleton del ChatbotAI"""
    global _chatbot_ai
    if _chatbot_ai is None:
        _chatbot_ai = ChatbotAI()
    return _chatbot_ai
