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

SPECIAL_PERSONA_PROMPTS = {
    "efrain_moraga": {
        "system": """Eres un asistente de IA tipo ChatGPT (modelo GPT-5.2) para Efraín. Tu rol es ayudar con cualquier tarea que solicite: análisis, creación, investigación, código, escritura, consultoría, etc. 

Eres flexible, competente y honesto. Tienes acceso a herramientas avanzadas (análisis de imágenes, lenguaje, documentos). Cuando Efraín comparte información sobre Fundo Moraga, considerala en contexto. Pero tu propósito principal es ser un asistente versátil y confiable.

Mantén un tono natural, profesional pero cercano. Habla directo sin rodeos. Adapta tu nivel de detalle según lo que pida. Si no sabes algo, lo dices claramente.""",
        "operational": """Responde de forma directa y eficiente. Sé conciso pero completo. No hagas listas innecesarias a menos que se pida. Evita Markdown excesivo; texto plano cuando sea posible. Si necesitas información, pregunta una sola vez y clara. Ofrece alternativas cuando sea útil. Usa ejemplos concretos. Prioriza valor sobre protocolo.""",
    }
}


class ChatbotAI:
    """Gestiona la generación de respuestas con OpenAI"""
    
    def __init__(self):
        """Inicializa el cliente de OpenAI y carga prompts dinámicamente desde Cosmos DB."""
        # Timeout agresivo para evitar que el proxy devuelva 504 y mejorar P95.
        self.request_timeout = int(os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "15"))
        self.client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=self.request_timeout)
        self.model = config.OPENAI_MODEL
        self.memory_store = get_memory_store()
        # Si la cuenta queda sin cuota, evitamos golpear la API en cada mensaje (reduce latencia/ruido).
        self._openai_disabled_until: Optional[datetime] = None
        self._openai_disabled_reason: Optional[str] = None
        
        # No inicializar tools_manager aquí - se cargará dinámicamente por usuario
        self._tools_manager_cache: Dict[str, Any] = {}
        
        # Cargar prompts dinámicamente desde Cosmos DB; fallback a embebidos
        from prompts_loader import get_prompts_loader
        
        # Defaults embebidos (usado como fallback si Cosmos no responde)
        self._default_system_prompt = """Eres Hernando, anfitrión digital de Fundo Moraga. Tono cercano, claro y seguro: informal moderado, sin exceso de modismos. Usa un modismo chileno ocasional y suave si aporta cercanía; evita muletillas repetitivas.

OBJETIVO
- Resolver con precisión, criterio y calidez.
- Entregar valor primero y luego pedir datos.
- Evitar respuestas vagas o evasivas; si falta información, pide lo mínimo necesario.

**PRIORIDAD CRÍTICA: HERRAMIENTAS Y EJECUCIÓN**

Cuando tienes herramientas disponibles (function calling):
1. **EJECUTA PRIMERO, EXPLICA DESPUÉS:** Si el usuario pide búsquedas, análisis o cualquier acción que tienes herramientas para hacer, HAZLO de inmediato. No expliques por qué no puedes o pidas más información innecesariamente.
2. **SÉ PROACTIVO:** Si tienes acceso a servicio de navegación web, búsqueda, visión computacional, etc. - ÚSALOS cuando sea apropiado sin preguntar.
3. **NO SEAS ACADÉMICO EN TAREAS SIMPLES:** Si te piden "busca 3 noticias sobre X", no respondas con "Opción A" y "Opción B". Simplemente ejecuta la búsqueda con la herramienta disponible.
4. **EVITA EXCUSAS TÉCNICAS:** No digas "no tengo acceso operativo directo" si tienes herramientas de function calling disponibles. Úsalas.
5. **RESPUESTAS DIRECTAS:** Si una herramienta falla o no está disponible REALMENTE, sé honesto y breve. No des 3 párrafos de explicaciones.

**ORQUESTACIÓN MULTI-HERRAMIENTA (NIVEL DOCTORAL):**
6. **COMBINA HERRAMIENTAS AUTOMÁTICAMENTE:**
   - Usuario pide "buscar X y analizar" → EJECUTA: buscar_en_google() → extraer_contenido_web() → analizar_sentimiento_texto() [sin interrupciones]
   - Usuario envía imagen → EJECUTA: analizar_imagen_completa() + extraer_texto_imagen() [en paralelo cuando posible]
   - Usuario dice "investiga Y" → USA investigar_tema() que ejecuta flujo completo automático

7. **PRIORIDADES DE EJECUCIÓN:**
   - ALTA (ejecutar SIN preguntar): Búsquedas web (buscar_en_google, investigar_tema), análisis imágenes, navegación
   - MEDIA (ejecutar si contexto lo necesita): Análisis de texto, traducción, detección de idioma
   - BAJA (confirmar antes): Guardar documentos, enviar emails, generar reportes

8. **OPTIMIZA LLAMADAS:**
   - Búsqueda web → SIEMPRE extraer contenido de top 3-5 resultados automáticamente
   - Imagen → SIEMPRE OCR + análisis visual (en paralelo)
   - Texto extranjero → SIEMPRE detectar idioma + traducir
   - Múltiples URLs → Usar scrape_multiples_urls() en lugar de llamadas individuales

9. **LEE [AUTO-EXECUTE] EN DESCRIPTIONS:**
   - Si tool description tiene [AUTO-EXECUTE] → Ejecutar INMEDIATAMENTE sin pedir confirmación
   - Sigue las directivas CUÁNDO USAR / NO USAR de cada herramienta
   - Respeta las indicaciones de COMBINAR CON otras herramientas

CONVERSACIÓN
1. No hagas 3+ preguntas seguidas sin validar o comentar.
2. Valida/recapitula antes de preguntar.
3. Si asumes algo, confirma en una línea.
4. Evita repetir saludos o fórmulas cada turno.
5. **NUNCA respondas "Listo. ¿En qué más te puedo ayudar?" si no completaste la tarea original.**

ADMIN MODE (cuando CONTEXTO indique admin_mode=true)
- Trata al usuario como equipo interno, no cliente.
- Responde directo, técnico si aplica, y propone pasos concretos.
- No hagas venta ni pitch; evita textos promocionales.
- Puedes hablar de prompts, DB, logs, despliegues y pruebas.
- Si piden guardar reglas, sugiere /remember y confirma.
- **EJECUTA HERRAMIENTAS DISPONIBLES SIN DUDAR.**

PERSONALIDAD
- Hospitalario, inteligente, con criterio.
- No condescendiente; no inventes.
- **Proactivo y resolutivo: si puedes hacer algo, hazlo.**
"""
        self._default_operational_prompt = """RECOLECCIÓN DE DATOS (sin interrogatorio):

Cuando necesitas NOMBRE:
- "¿Cómo te llamas para registrarte?"
- "¿A nombre de quién dejamos la solicitud?"

Cuando necesitas TELÉFONO:
- "¿A qué número te escribo por WhatsApp?"
- "¿Cuál es tu teléfono de contacto?"

Cuando necesitas EMAIL:
- "¿A qué correo te envío la información completa?"
- "Si te parece, te mando el detalle por mail. ¿Cuál usas?"

Cuando necesitas FECHA:
- "¿Para cuándo lo estás viendo?"
- "¿Tienes una fecha tentativa?"

Cuando necesitas CANTIDAD:
- "¿Cuántos autos/motos serían?"
- "¿Cuántas personas estimas?"

REGLA ORO: Siempre da contexto antes de pedir información.
Ejemplo: "Para enviarte el mapa y confirmar cupos, ¿cuál es tu contacto?" ✓
No: "¿Cuál es tu contacto?" ✗

Si admin_mode=true, responde directo y no uses este guion salvo que lo pidan.
Llama herramientas cuando el usuario haya mencionado datos naturalmente, no como respuesta directa a pregunta.
"""
        
        # Cargar dinámicamente desde Cosmos DB
        loader = get_prompts_loader()
        
        # Crear un tools_manager temporal para obtener las herramientas base
        from hernando_tools import get_hernando_tools
        temp_tools_manager = get_hernando_tools()
        
        prompts = loader.get_prompts(
            persona="Hernando",
            fallback_system_prompt=self._default_system_prompt,
            fallback_operational_prompt=self._default_operational_prompt,
            fallback_tools=temp_tools_manager.tools,
        )
        
        self._base_persona_name = "hernando"
        base_tools = prompts.get("tools") or []
        self._base_persona_prompts = {
            "system": prompts["system"],
            "operational": prompts["operational"],
            "tools": base_tools,
        }
        self.system_prompt = self._base_persona_prompts["system"]
        self.operational_prompt = self._base_persona_prompts["operational"]
        self.dynamic_tools: List[Dict[str, Any]] = base_tools
        # Preferir tools desde Cosmos; fallback a definiciones locales
        self._base_tools = self.dynamic_tools if self.dynamic_tools else temp_tools_manager.tools
        self._special_persona_prompts = {k.lower(): v for k, v in SPECIAL_PERSONA_PROMPTS.items()}
    
    def _get_tools_for_user(self, user_id: Optional[str] = None) -> tuple:
        """Obtiene el tools_manager y lista de herramientas para un usuario específico."""
        from hernando_tools import get_hernando_tools
        tools_manager = get_hernando_tools(user_id=user_id)
        return tools_manager, tools_manager.tools

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
    
    def _get_relevant_learnings(self, user_id: str, user_message: str) -> List[str]:
        """
        Consulta aprendizajes relevantes basados en el mensaje del usuario.
        Inyecta en el contexto para que Hernando use lo que aprendió previamente.
        
        Returns:
            Lista de líneas con aprendizajes formateadas para el contexto
        """
        try:
            from hernando_tools import get_hernando_tools
            
            # Extraer temas del mensaje
            message_lower = user_message.lower()
            topics = []
            
            # Identificar temas relevantes
            if "precio" in message_lower or "costo" in message_lower:
                topics.append("precios")
            if "batuco" in message_lower:
                topics.append("batuco")
            if "reserva" in message_lower or "agendar" in message_lower:
                topics.append("reservas")
            if "reporte" in message_lower or "informe" in message_lower:
                topics.append("reportes")
            if "documento" in message_lower:
                topics.append("documentos")
            
            if not topics:
                # Si no hay temas específicos, usar "general"
                topics.append("general")
            
            learning_lines = []
            tools = get_hernando_tools(user_id)
            
            # Consultar aprendizajes para cada tema
            for tema in topics[:2]:  # Limitar a 2 temas para no inflar el prompt
                resultado = tools.execute_tool(
                    tool_name="consultar_aprendizajes",
                    arguments={
                        "tema": tema,
                        "tipo_aprendizaje": "todos",
                        "limitar_a": 3  # Solo los 3 más relevantes por tema
                    }
                )
                
                if resultado.get("success") and resultado.get("aprendizajes"):
                    for aprendizaje in resultado["aprendizajes"]:
                        tipo = aprendizaje.get("tipo")
                        clasificacion = aprendizaje.get("clasificación")
                        respuesta_correcta = aprendizaje.get("respuesta_correcta", "")
                        explicacion = aprendizaje.get("explicación", "")
                        sentimiento = aprendizaje.get("sentimiento")
                        
                        # Formatear según clasificación
                        if clasificacion == "ejemplo_a_seguir" or sentimiento == "positive":
                            prefix = "✅ HACER"
                        elif clasificacion == "ejemplo_a_evitar" or sentimiento == "negative":
                            prefix = "❌ EVITAR"
                        else:
                            prefix = "📝 NOTA"
                        
                        # Construir línea de aprendizaje
                        learning_text = f"{prefix} [{tema}]: {respuesta_correcta[:150]}"
                        if explicacion:
                            learning_text += f" | {explicacion[:100]}"
                        
                        learning_lines.append(learning_text)
                        
                        if len(learning_lines) >= 5:  # Máximo 5 aprendizajes totales
                            break
                
                if len(learning_lines) >= 5:
                    break
            
            return learning_lines
            
        except Exception as e:
            print(f"⚠️ Error obteniendo aprendizajes relevantes: {e}")
            return []

    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        platform: Optional[str] = None,
        already_welcomed: Optional[bool] = None,
        lead_capture_already_sent: Optional[bool] = None,
        extra_context: Optional[Any] = None,
        *,
        system_prompt: str,
        operational_prompt: str,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

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

        is_admin_mode = False
        if isinstance(extra_context, dict):
            raw_admin = extra_context.get("admin_mode")
            if isinstance(raw_admin, bool):
                is_admin_mode = raw_admin
            elif isinstance(raw_admin, str):
                is_admin_mode = raw_admin.strip().lower() in ("1", "true", "yes", "on")

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
        elif isinstance(extra_context, str):
            note = extra_context.strip()
            if note:
                if len(note) > 400:
                    note = note[:400] + "…"
                context_lines.append(f"extra_context_note={note}")

        if user_id:
            # Inyectar memoria: hechos, precios y resúmenes recientes.
            memory_lines: List[str] = []
            special_facts: Dict[str, str] = {}

            def _append_fact(item: Dict[str, Any]) -> None:
                key = item.get("key")
                val = item.get("value")
                scope = item.get("scope") or "global"
                if not key or val is None:
                    return
                val_str = str(val).strip()
                if not val_str:
                    return
                if len(val_str) > 300:
                    val_str = val_str[:300] + "…"
                if key in ("tone_guidelines", "admin_mode_not_client"):
                    special_facts[key] = val_str
                memory_lines.append(f"fact[{scope}]: {key}={val_str}")

            scopes: List[tuple[str, int]] = [("global", 5)]
            if is_admin_mode:
                scopes.append(("admin", 5))
            scopes.append((f"user:{user_id}", 4))

            for scope, limit in scopes:
                for f in self.memory_store.list_facts(scope=scope, limit=limit):
                    _append_fact(f)
                    if len(memory_lines) >= 10:
                        break
                if len(memory_lines) >= 10:
                    break

            prices = self.memory_store.list_prices(limit=5)
            for p in prices:
                if len(memory_lines) >= 10:
                    break
                prod = p.get("product")
                price = p.get("price")
                curr = p.get("currency") or "CLP"
                if prod and price is not None:
                    memory_lines.append(f"price: {prod}={price} {curr}")
                    if len(memory_lines) >= 10:
                        break

            summaries = self.memory_store.get_conversation_summaries(user_id=user_id, limit=3)
            for s in summaries:
                if len(memory_lines) >= 13:
                    break
                cid = s.get("conversationId")
                summary = s.get("summary")
                if summary:
                    memory_lines.append(f"summary[{cid}]: {summary}")
                    if len(memory_lines) >= 13:
                        break

            if special_facts:
                for key, val in special_facts.items():
                    context_lines.append(f"{key}={val}")
            if memory_lines:
                context_lines.append("MEMORIA")
                context_lines.extend(memory_lines)
            
            # NUEVO: Inyectar aprendizajes relevantes basados en el mensaje del usuario
            try:
                learning_lines = self._get_relevant_learnings(user_id, user_message)
                if learning_lines:
                    context_lines.append("APRENDIZAJES_PREVIOS")
                    context_lines.extend(learning_lines)
            except Exception as e:
                print(f"⚠️ Error inyectando aprendizajes: {e}")

        if context_lines:
            messages.append({"role": "system", "content": "CONTEXTO\n" + "\n".join(context_lines)})

        messages.append({"role": "system", "content": operational_prompt})

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

    def _load_doctoral_prompts_from_cosmos(self) -> Dict[str, Dict[str, Any]]:
        """Carga prompts doctorales desde Cosmos DB."""
        prompts_cache = {}
        try:
            database = self.memory_store.client.get_database_client("Entrenamiento")
            container = database.get_container_client("Hernando")
            
            # Cargar prompt base doctoral
            query_base = "SELECT * FROM c WHERE c.id = 'efrain_moraga_doctoral_base'"
            items_base = list(container.query_items(query=query_base, enable_cross_partition_query=True))
            if items_base:
                prompts_cache["base"] = items_base[0]
            
            # Cargar prompts por área
            query_areas = "SELECT * FROM c WHERE c.persona = 'efrain_moraga_doctoral' AND c.area != null"
            items_areas = list(container.query_items(query=query_areas, enable_cross_partition_query=True))
            
            for item in items_areas:
                area = item.get("area")
                if area:
                    prompts_cache[area] = item
            
            print(f"✅ Cargados {len(prompts_cache)} prompts doctorales desde Cosmos DB")
        except Exception as e:
            print(f"⚠️  Error cargando prompts doctorales: {e}")
        
        return prompts_cache
    
    def _detect_doctoral_area(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Optional[str]:
        """Detecta qué área doctoral activar basándose en keywords del mensaje y contexto."""
        # Lazy load de prompts doctorales
        if not hasattr(self, '_doctoral_prompts_cache'):
            self._doctoral_prompts_cache = self._load_doctoral_prompts_from_cosmos()
        
        if not self._doctoral_prompts_cache:
            return None
        
        # Combinar mensaje actual con últimos 2 mensajes de contexto
        text_to_analyze = user_message.lower()
        if conversation_history and len(conversation_history) > 0:
            recent_messages = conversation_history[-2:]
            for msg in recent_messages:
                content = (msg.get("message") or "").lower()
                text_to_analyze += " " + content
        
        # Buscar keywords de cada área
        area_matches = {}
        for area, prompt_data in self._doctoral_prompts_cache.items():
            if area == "base":
                continue
            
            keywords = prompt_data.get("keywords_activacion", [])
            matches = sum(1 for keyword in keywords if keyword.lower() in text_to_analyze)
            if matches > 0:
                area_matches[area] = matches
        
        # Retornar área con más matches (si hay empate, primera alfabéticamente)
        if area_matches:
            best_area = max(area_matches.items(), key=lambda x: (x[1], x[0]))[0]
            print(f"🎓 Área doctoral detectada: {best_area} ({area_matches[best_area]} keywords)")
            return best_area
        
        return None
    
    def _detect_language_and_suggest_improvements(self, user_message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Detecta automáticamente el idioma del mensaje y sugiere mejoras de redacción.
        Ejecuta herramientas en segundo plano sin bloquear la respuesta principal.
        """
        from private_knowledge import is_authorized_user
        
        result = {
            "detected_language": None,
            "language_suggestions": None,
            "translation_needed": False,
        }
        
        # Solo ejecutar si el usuario está autorizado
        if not is_authorized_user(user_id):
            return result
        
        try:
            # Detectar idioma del mensaje
            import language_client as lc
            language_info = lc.detect_language(user_message)
            
            if language_info:
                # language_client retorna: {name, iso, confidence}
                detected_iso = language_info.get("iso")
                detected_name = language_info.get("name")
                result["detected_language"] = detected_iso or detected_name
                
                # Si no es español, marcar que se necesita traducción
                if detected_iso and detected_iso not in ("es", "pt", "en"):  # pt es portugués, en es inglés
                    result["translation_needed"] = True
                    print(f"🌍 Idioma detectado: {detected_name} ({detected_iso}), se sugiere traducción")
                else:
                    # Sugerir mejoras de redacción si es español
                    print(f"📝 Analizando redacción en español...")
                    # Aquí podríamos agregar más análisis de estilo si es necesario
            
        except Exception as e:
            print(f"⚠️  Error detectando idioma: {e}")
        
        return result

    def _apply_language_analysis_to_system_prompt(self, 
                                                  system_prompt: str, 
                                                  language_analysis: Dict[str, Any]) -> str:
        """
        Aplica resultados del análisis de lenguaje al system prompt.
        Agrega notas sobre idioma detectado y recomendaciones.
        """
        if not language_analysis or not language_analysis.get("detected_language"):
            return system_prompt
        
        detected_lang = language_analysis.get("detected_language")
        additions = []
        
        if language_analysis.get("translation_needed"):
            additions.append(f"Nota: El usuario escribió en {detected_lang}. Considera responder en español y ofrecerle traducción si lo necesita.")
        else:
            additions.append(f"Nota: Idioma detectado: {detected_lang}. Responde naturalmente en español.")
        
        if additions:
            return system_prompt + "\n\n" + "\n".join(additions)
        
        return system_prompt

    def _combine_doctoral_prompts(self, base_prompts: Dict[str, Any], area: str) -> Dict[str, Any]:
        """Combina prompt base doctoral con prompt de área específica."""
        if not hasattr(self, '_doctoral_prompts_cache'):
            return base_prompts
        
        doctoral_base = self._doctoral_prompts_cache.get("base")
        doctoral_area = self._doctoral_prompts_cache.get(area)
        
        if not doctoral_base:
            print("⚠️  Prompt base doctoral no encontrado, usando prompts estándar")
            return base_prompts
        
        # System prompt: Base doctoral + enhancement del área (si existe)
        system_parts = [doctoral_base.get("system_prompt", "")]
        if doctoral_area:
            area_enhancement = doctoral_area.get("knowledge_enhancement", "")
            if area_enhancement:
                system_parts.append("\n\n" + area_enhancement)
        
        combined_system = "".join(system_parts)
        
        # Operational prompt: Usar el del base doctoral
        operational = doctoral_base.get("operational_prompt", base_prompts["operational"])
        
        return {
            "system": combined_system,
            "operational": operational,
            "tools": base_prompts["tools"],  # Tools no cambian
        }

    def _resolve_persona_prompts(self, persona_override: Optional[str], user_message: str = "", conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Devuelve prompts específicos cuando el sistema debe usar una personalidad alterna.
        Si persona es efrain_moraga, detecta área doctoral y combina prompts especializados.
        """
        if not persona_override:
            return self._base_persona_prompts

        normalized = persona_override.strip().lower()
        if normalized == self._base_persona_name:
            return self._base_persona_prompts

        special = self._special_persona_prompts.get(normalized)
        if not special:
            return self._base_persona_prompts
        
        # Resolver prompts base
        base_result = {
            "system": special["system"],
            "operational": special["operational"],
            "tools": special.get("tools") or self._base_persona_prompts["tools"],
        }
        
        # Si es efrain_moraga, activar sistema doctoral automático
        if normalized == "efrain_moraga":
            detected_area = self._detect_doctoral_area(user_message, conversation_history)
            if detected_area:
                return self._combine_doctoral_prompts(base_result, detected_area)
        
        return base_result

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

        timeout_cls = getattr(openai, "APITimeoutError", None)
        if timeout_cls and isinstance(exc, timeout_cls):
            return {"type": "timeout", "status_code": status_code, "code": code or "timeout", "message": message}
        if "timeout" in text:
            return {"type": "timeout", "status_code": status_code, "code": code or "timeout", "message": message or str(exc)}

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
        user_id: Optional[str] = None,
    ) -> Any:
        messages: List[Any] = [dict(m) for m in base_messages]
        events: List[Dict[str, Any]] = []
        
        # Obtener herramientas específicas para este usuario
        tools_manager, tools_list = self._get_tools_for_user(user_id)

        max_tool_rounds = 3
        token_param = self._token_param_name(model)
        for _ in range(max_tool_rounds):
            kwargs: Dict[str, Any] = dict(
                model=model,
                messages=messages,
                tools=tools_list,
                tool_choice="auto",
                temperature=0.5,
            )
            kwargs["timeout"] = self.request_timeout
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

                function_result = tools_manager.execute_tool(function_name, function_args)
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
        extra_context: Optional[Any] = None,
        persona_override: Optional[str] = None,
        return_events: bool = False,
    ) -> Any:
        """
        Genera una respuesta del chatbot con soporte para Function Calling
        
        Args:
            user_message: Mensaje del usuario
            conversation_history: Historial de conversación (opcional)
            persona_override: Nombre de la personalidad especial que debe usarse para este turno.
        
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

        # Detectar automáticamente idioma y sugerir mejoras (en segundo plano, sin bloquear)
        language_analysis = {
            "detected_language": None,
            "language_suggestions": None,
            "translation_needed": False,
        }
        try:
            language_analysis = self._detect_language_and_suggest_improvements(user_message, user_id)
        except Exception as e:
            print(f"⚠️  Error en detección de idioma (no crítico): {e}")
            # Si falla, continuamos con valores por defecto

        persona_prompts = self._resolve_persona_prompts(persona_override, user_message, conversation_history)
        
        # Aplicar análisis de lenguaje al system prompt si es necesario
        system_prompt = persona_prompts["system"]
        if language_analysis.get("detected_language"):
            try:
                system_prompt = self._apply_language_analysis_to_system_prompt(system_prompt, language_analysis)
            except Exception as e:
                print(f"⚠️  Error aplicando análisis de lenguaje: {e}")
                # Si falla, usamos el system prompt original
        
        messages = self._build_messages(
            user_message=user_message,
            conversation_history=conversation_history,
            conversation_id=conversation_id,
            user_id=user_id,
            platform=platform,
            already_welcomed=already_welcomed,
            lead_capture_already_sent=lead_capture_already_sent,
            extra_context=extra_context,
            system_prompt=system_prompt,
            operational_prompt=persona_prompts["operational"],
        )

        last_error: Optional[Exception] = None
        last_error_info: Optional[Dict[str, Any]] = None
        for model in self._model_candidates():
            try:
                if model != self.model:
                    print(f"⚠️ Probando modelo fallback: {model} (configurado: {self.model})")
                return self._generate_with_model(
                    model=model, 
                    base_messages=messages, 
                    return_events=return_events,
                    user_id=user_id
                )
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
                temperature=0.5,
                timeout=self.request_timeout,
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
            kwargs["timeout"] = self.request_timeout
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
