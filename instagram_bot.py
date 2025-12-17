"""
Bot principal de Instagram para Fundo Moraga
Integra Cosmos DB para memoria y OpenAI para respuestas
"""
import requests
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta, date, time
import config
from cosmos_client import get_conversation_store
from openai_client import get_chatbot_ai
from resend_client import get_resend_client
import json
import re
from zoneinfo import ZoneInfo
from html import escape

from google_calendar_client import CalendarEventRequest, get_google_calendar_client
from payment_inbox_client import get_payment_inbox_client


class InstagramBot:
    """Chatbot de Instagram con memoria en Cosmos DB"""
    
    def __init__(self):
        """Inicializa el bot"""
        self.conversation_store = get_conversation_store()
        self.chatbot_ai = get_chatbot_ai()
        self.resend_client = get_resend_client()
        self.calendar_client = get_google_calendar_client()
        self.payment_inbox = get_payment_inbox_client()
        # Instagram (opcional). Si no está configurado, el chat web sigue funcionando.
        self.access_token = config.INSTAGRAM_ACCESS_TOKEN
        self.page_id = config.INSTAGRAM_PAGE_ID

    def is_instagram_configured(self) -> bool:
        return bool(self.access_token)

    def _sanitize_user_response(self, text: str) -> str:
        """
        El chat del sitio no debe mostrar asteriscos/Markdown. Remueve asteriscos y normaliza espacios.
        """
        if not isinstance(text, str):
            return text
        # Quitar markdown básico (evita **bold**, *italics*, y `code`)
        sanitized = text.replace("*", "").replace("`", "")
        # Normalizaciones suaves
        sanitized = re.sub(r"[ \t]{2,}", " ", sanitized)
        sanitized = re.sub(r" ?\n ?", "\n", sanitized)
        return sanitized.strip()
    
    def process_message(
        self,
        user_id: str,
        message_text: str,
        *,
        platform: str = "web",
        source: str = "widget",
    ) -> str:
        """
        Procesa un mensaje entrante del usuario
        
        Args:
            user_id: ID del usuario de Instagram
            message_text: Texto del mensaje
        
        Returns:
            Respuesta generada para el usuario
        """
        try:
            platform_key = (platform or "web").strip().lower()
            platform_label = "Instagram" if platform_key == "instagram" else "Web"
            print(f"📥 Mensaje de {user_id} ({platform_label}): {message_text}")
            
            # 1. Obtener ID de conversación actual o crear nueva
            conversation_id = self.conversation_store.get_latest_conversation_id(user_id)
            if not conversation_id:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            # 2. Guardar mensaje del usuario en Cosmos DB
            self.conversation_store.save_message(
                user_id=user_id,
                role="user",
                message=message_text,
                conversation_id=conversation_id,
                metadata={"platform": platform_key, "source": source}
            )
            
            # 3. Recuperar historial de conversación
            conversation_history = self.conversation_store.get_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=config.MAX_CONVERSATION_HISTORY
            )

            platform = platform_label
            lead_context = self._build_lead_context(conversation_history, conversation_id)

            # 4. Flujo determinístico de agendamiento (no depende del modelo)
            booking_response = self._handle_booking_flow(
                user_id=user_id,
                conversation_id=conversation_id,
                message_text=message_text,
                conversation_history=conversation_history,
                platform=platform,
            )
            if booking_response:
                booking_response = self._sanitize_user_response(booking_response)
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message=booking_response,
                    conversation_id=conversation_id,
                    metadata={"platform": platform_key, "source": "booking_flow"},
                )
                self._maybe_auto_lead_capture(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    platform=platform,
                    lead_context=lead_context,
                )
                return booking_response

            # 4.25 Respuesta determinística para fecha/día (evita errores del modelo)
            date_response = self._handle_date_questions(message_text)
            if date_response:
                date_response = self._sanitize_user_response(date_response)
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message=date_response,
                    conversation_id=conversation_id,
                    metadata={"platform": platform_key, "source": "date_flow"},
                )
                self._maybe_auto_lead_capture(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    platform=platform,
                    lead_context=lead_context,
                )
                return date_response

            # 4.3 Flujo determinístico para eventos/producciones (coordinar con equipo)
            admin_response = self._handle_admin_coordination(message_text)
            if admin_response:
                admin_response = self._sanitize_user_response(admin_response)
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message=admin_response,
                    conversation_id=conversation_id,
                    metadata={"platform": platform_key, "source": "admin_flow"},
                )
                self._maybe_auto_lead_capture(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    platform=platform,
                    lead_context=lead_context,
                )
                return admin_response

            # 4.5 Respuesta determinística para tarifas públicas (evita respuestas genéricas del modelo)
            pricing_response = self._handle_public_pricing(message_text)
            if pricing_response:
                pricing_response = self._sanitize_user_response(pricing_response)
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message=pricing_response,
                    conversation_id=conversation_id,
                    metadata={"platform": platform_key, "source": "pricing_flow"},
                )
                self._maybe_auto_lead_capture(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    platform=platform,
                    lead_context=lead_context,
                )
                return pricing_response
            
            # 5. Generar respuesta con OpenAI usando el contexto
            already_welcomed = any(
                (msg.get("metadata") or {}).get("type") == "welcome"
                or (msg.get("role") == "assistant" and (msg.get("message") or "").strip())
                for msg in (conversation_history or [])
            )
            lead_capture_already_sent = any(
                (msg.get("metadata") or {}).get("type") == "lead_capture" for msg in (conversation_history or [])
            )

            ai_result = self.chatbot_ai.generate_response(
                user_message=message_text,
                conversation_history=conversation_history,
                conversation_id=conversation_id,
                platform=platform,
                already_welcomed=already_welcomed,
                lead_capture_already_sent=lead_capture_already_sent,
                extra_context=lead_context,
                return_events=True,
            )

            response_text = ai_result.get("text") if isinstance(ai_result, dict) else ai_result
            response_text = self._sanitize_user_response(response_text)
            events = ai_result.get("events", []) if isinstance(ai_result, dict) else []
            model_used = ai_result.get("model_used") if isinstance(ai_result, dict) else None
            model_requested = config.OPENAI_MODEL
            model_to_store = model_used or model_requested
            
            # 6. Guardar respuesta del asistente en Cosmos DB
            self.conversation_store.save_message(
                user_id=user_id,
                role="assistant",
                message=response_text,
                conversation_id=conversation_id,
                metadata={
                    "platform": platform_key,
                    "model": model_to_store,
                    "model_requested": model_requested,
                }
            )

            # 7. Si el modelo ejecutó herramientas de captura/formulario, enviar email y marcar conversación
            lead_handled = False
            if events:
                lead_handled = self._handle_post_ai_events(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    latest_message=message_text,
                    platform=platform,
                    events=events,
                )

            if not lead_handled:
                self._maybe_auto_lead_capture(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    platform=platform,
                    lead_context=lead_context,
                )
            
            print(f"📤 Respuesta: {response_text}")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente."

    def _handle_public_pricing(self, message_text: str) -> Optional[str]:
        """
        Maneja preguntas típicas sobre tarifas públicas (en especial off-road),
        para asegurar respuestas consistentes sin derivar a contacto.
        """
        t = (message_text or "").lower()
        if not t:
            return None

        # Detectores de pregunta de precio/tarifa
        price_markers = (
            "precio",
            "precios",
            "tarifa",
            "tarifas",
            "valor",
            "cuánto",
            "cuanto",
            "cuesta",
            "sale",
            "$",
        )
        offroad_markers = (
            "offroad",
            "off-road",
            "4x4",
            "enduro",
            "moto",
            "motos",
            "auto",
            "autos",
            "vehículo",
            "vehiculo",
            "batuco",
        )
        weekend_markers = ("sábado", "sabado", "fin de semana", "domingo")

        looks_like_price = any(m in t for m in price_markers)
        looks_like_offroad = any(m in t for m in offroad_markers) or any(m in t for m in weekend_markers)

        if not looks_like_price:
            return None

        if not looks_like_offroad:
            return (
                "¿Te refieres a las actividades **off-road** (auto/moto) o a un **evento/producción**?\n\n"
                "Si es off-road, las tarifas públicas son:\n"
                "• Lunes a viernes (09:00 a 17:00): $15.000 automóviles / $10.000 motos.\n"
                "• Sábado (solo grupos): $200.000 el día.\n"
                "• Domingo: no se agenda.\n\n"
                "¿Qué es lo que te gustaría hacer? (auto/moto off-road, evento, visita, producción)"
            )

        return (
            "¡Claro! Para las actividades off-road (Batuco Off Road) las tarifas públicas son:\n"
            "• Lunes a viernes (09:00 a 17:00): $15.000 automóviles / $10.000 motos.\n"
            "• Sábado (solo grupos): $200.000 el día.\n"
            "• Domingo: no se agenda.\n\n"
            "Si quieres, lo dejamos coordinado al tiro: ¿qué fecha y a qué hora te gustaría llegar (entre 09:00 y 17:00)? "
            "¿Vienes en auto o moto, y cuántos?\n\n"
            "Y si prefieres que el equipo te contacte para coordinar, déjame tu nombre y un correo o WhatsApp y lo derivo."
        )

    def _handle_date_questions(self, message_text: str) -> Optional[str]:
        """
        Responde preguntas típicas sobre la fecha/día actual o la fecha de un día de la semana.
        Zona horaria: Chile (config.GOOGLE_CALENDAR_TIMEZONE).
        """
        raw = (message_text or "").strip()
        if not raw:
            return None

        t = raw.lower()
        # Preguntas por fecha/día de hoy
        asks_today = any(
            k in t
            for k in (
                "qué fecha es hoy",
                "que fecha es hoy",
                "fecha de hoy",
                "día de hoy",
                "dia de hoy",
                "qué día es hoy",
                "que dia es hoy",
                "que día es hoy",
                "hoy qué día es",
                "hoy que dia es",
                "hoy qué fecha es",
                "hoy que fecha es",
            )
        )

        weekday_hint = self._parse_weekday_name_es(t)
        asks_weekday_date = (
            weekday_hint is not None
            and any(k in t for k in ("qué fecha", "que fecha", "qué día", "que dia", "cuándo cae", "cuando cae"))
        )

        if not asks_today and not asks_weekday_date:
            return None

        today = self._today_local_date()
        today_weekday = self._day_name_es(today)

        if asks_today and not asks_weekday_date:
            return (
                f"Hoy es **{today_weekday} {today.isoformat()}** (Chile). "
                "¿Te gustaría coordinar una visita/actividad para hoy o para otro día?"
            )

        # Pregunta por fecha de un día de la semana (ej: "¿qué fecha es este viernes?")
        if not weekday_hint:
            return None

        today_option, next_option = self._weekday_date_options(weekday_hint, base_date=today)
        if today_option and next_option:
            # Si hoy ya es ese día, entregamos ambas opciones (hoy vs próximo).
            return (
                f"Hoy es **{today_weekday} {today.isoformat()}**. "
                f"Si te refieres a **hoy {weekday_hint}**, es **{today_option.isoformat()}**; "
                f"si es el **próximo {weekday_hint}**, es **{next_option.isoformat()}**. "
                "¿Cuál de los dos te sirve?"
            )

        if next_option:
            return (
                f"El próximo **{weekday_hint}** cae **{next_option.isoformat()}** (Chile). "
                "Si quieres, lo coordinamos: ¿a qué hora te gustaría llegar? (09:00–17:00)"
            )

        return None

    def _handle_admin_coordination(self, message_text: str) -> Optional[str]:
        """
        Consultas que requieren coordinación formal con el equipo (eventos, producciones, prensa, etc.).
        """
        t = (message_text or "").strip().lower()
        if not t:
            return None

        markers = (
            "evento",
            "matrimonio",
            "cumple",
            "cumpleaños",
            "fiesta",
            "corporativo",
            "empresa",
            "team building",
            "teambuilding",
            "producción",
            "produccion",
            "filmación",
            "filmacion",
            "grabación",
            "grabacion",
            "rodaje",
            "fotografía",
            "fotografia",
            "sesión",
            "sesion",
            "comercial",
            "videoclip",
            "película",
            "pelicula",
            "serie",
            "prensa",
            "periodista",
            "nota",
            "medio",
            "locación",
            "locacion",
            "cotizar",
            "cotización",
            "cotizacion",
        )

        if not any(m in t for m in markers):
            return None

        # Si es claramente off-road (tarifas públicas), no forzamos derivación aquí.
        offroad_markers = (
            "offroad",
            "off-road",
            "4x4",
            "enduro",
            "batuco",
            "moto",
            "motos",
            "auto",
            "autos",
            "vehículo",
            "vehiculo",
        )
        if any(m in t for m in offroad_markers):
            return None

        return (
            "¡Bacán! Eso lo coordinamos directo con el equipo de Fundo Moraga, porque depende de la fecha, el tipo de actividad "
            "y los requerimientos.\n\n"
            "📧 Email: contacto@fundomoraga.com\n"
            "📱 WhatsApp: +5694 1242609\n\n"
            "Si quieres, te ahorro un paso: cuéntame en una frase qué quieres hacer y para qué fecha tentativamente, "
            "y déjame un correo o WhatsApp para que te contacten.\n\n"
            "¿Para qué fecha lo estás pensando?"
        )

    def _handle_post_ai_events(
        self,
        user_id: str,
        conversation_id: str,
        conversation_history: list,
        latest_message: str,
        platform: str,
        events: list,
    ) -> bool:
        lead_capture_already_sent = any(
            (msg.get("metadata") or {}).get("type") == "lead_capture" for msg in (conversation_history or [])
        )

        if lead_capture_already_sent:
            return True

        for event in events:
            tool = (event or {}).get("tool")
            args = (event or {}).get("args") or {}
            if tool == "capturar_informacion_usuario":
                self._send_lead_email(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    latest_message=latest_message,
                    platform=platform,
                    nombre=args.get("nombre"),
                    interes=args.get("interes"),
                    contacto=args.get("contacto"),
                )
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message="",
                    conversation_id=conversation_id,
                    metadata={"platform": (platform or "web").lower(), "type": "lead_capture", "source": "tool", "args": args},
                )
                return True

            if tool == "enviar_formulario_contacto":
                nombre = args.get("nombre")
                email = args.get("email")
                telefono = args.get("telefono")
                tipo = args.get("tipo_solicitud")
                mensaje = args.get("mensaje")
                fecha = args.get("fecha_tentativa")
                interes = f"Formulario contacto ({tipo}): {mensaje}".strip()
                if fecha:
                    interes += f" | Fecha tentativa: {fecha}"
                contacto = " / ".join([x for x in [email, telefono] if x]) or None

                self._send_lead_email(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    latest_message=latest_message,
                    platform=platform,
                    nombre=nombre,
                    interes=interes,
                    contacto=contacto,
                )
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message="",
                    conversation_id=conversation_id,
                    metadata={"platform": (platform or "web").lower(), "type": "lead_capture", "source": "tool_form", "args": args},
                )
                return True

        return False

    def _build_lead_context(self, conversation_history: list, conversation_id: str) -> Dict[str, str]:
        """
        Construye un set compacto de señales para el modelo (evita preguntas repetidas y guía el siguiente paso).
        """
        lead_capture_present = any(
            (m.get("metadata") or {}).get("type") == "lead_capture" for m in (conversation_history or [])
        )

        booking_state = self._get_booking_state(conversation_history, conversation_id) or {}
        booking_details = (booking_state.get("details") or {}) if isinstance(booking_state, dict) else {}

        user_messages = [
            (m.get("message") or "")
            for m in (conversation_history or [])
            if m.get("role") == "user" and (m.get("message") or "").strip()
        ]
        joined = " \n".join(user_messages[-12:])

        # Nombre
        known_name = (booking_details.get("full_name") or "").strip() if isinstance(booking_details, dict) else ""
        if not known_name:
            m = re.search(
                r"\b(me llamo|soy)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+){0,4})\b",
                joined,
                re.IGNORECASE,
            )
            if m:
                known_name = m.group(2).strip(" .,!¿?;:")

        # Contacto
        emails = []
        phones = []
        if isinstance(booking_details, dict):
            if booking_details.get("email"):
                emails.append(str(booking_details.get("email")).strip())
            if booking_details.get("phone"):
                phones.append(str(booking_details.get("phone")).strip())

        emails.extend(re.findall(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", joined, re.IGNORECASE))
        phones.extend(re.findall(r"(\+?\d[\d\s\-()]{7,}\d)", joined))

        # De-dup preservando orden
        def _dedup(values: list[str]) -> list[str]:
            seen = set()
            out: list[str] = []
            for v in values:
                vv = (v or "").strip()
                if not vv:
                    continue
                key = vv.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(vv)
            return out

        emails = _dedup(emails)
        phones = _dedup(phones)
        known_contact = " / ".join([*emails[:2], *phones[:2]]).strip()

        missing_name = "false" if known_name else "true"
        missing_contact = "false" if known_contact else "true"

        intent = "general"
        if booking_state:
            intent = "agendamiento"
        else:
            lower = joined.lower()
            if any(k in lower for k in ("offroad", "off-road", "4x4", "enduro", "batuco")):
                intent = "offroad"
            if any(k in lower for k in ("evento", "producción", "produccion", "filmación", "filmacion", "matrimonio", "corporativo")):
                intent = "evento_produccion"

        ctx: Dict[str, str] = {
            "lead_capture_present": "true" if lead_capture_present else "false",
            "missing_name": missing_name,
            "missing_contact": missing_contact,
            "lead_intent": intent,
        }

        if known_name:
            ctx["known_name"] = known_name
        if known_contact:
            ctx["known_contact"] = known_contact

        if booking_state:
            for k in ("stage", "visit_date", "visit_day"):
                v = booking_state.get(k)
                if v:
                    ctx[f"booking_{k}"] = str(v)
            if isinstance(booking_details, dict):
                for k in ("arrival_time", "cars_count", "motos_count"):
                    v = booking_details.get(k)
                    if v is not None and v != "":
                        ctx[f"booking_{k}"] = str(v)

        return ctx

    def _build_conversation_snippet(self, conversation_history: list, *, max_messages: int = 12) -> str:
        lines: list[str] = []
        for msg in (conversation_history or [])[-max_messages:]:
            metadata = msg.get("metadata") or {}
            if metadata.get("type") in ("booking_state", "lead_capture", "conversation_summary"):
                continue
            role = msg.get("role") or "user"
            content = (msg.get("message") or "").strip()
            if not content:
                continue
            lines.append(f"{role}: {content}")
        return "\n".join(lines).strip()

    def _interest_from_booking_state(self, state: Dict) -> str:
        details = (state.get("details") or {}) if isinstance(state, dict) else {}
        visit_day = state.get("visit_day") or ""
        visit_date = state.get("visit_date") or ""
        arrival = details.get("arrival_time") or ""
        cars = details.get("cars_count")
        motos = details.get("motos_count")
        stage = state.get("stage") or ""

        parts = ["Intención: agendar visita/actividad off-road"]
        if visit_day or visit_date:
            parts.append(f"Fecha: {visit_day} {visit_date}".strip())
        if arrival:
            parts.append(f"Hora llegada: {arrival} (09:00–17:00)")
        if cars is not None or motos is not None:
            parts.append(f"Vehículos: autos={cars if cars is not None else 'N/A'}, motos={motos if motos is not None else 'N/A'}")
        if stage:
            parts.append(f"Estado: {stage}")
        return " | ".join(parts)

    def _maybe_auto_lead_capture(
        self,
        *,
        user_id: str,
        conversation_id: str,
        conversation_history: list,
        platform: str,
        lead_context: Dict[str, str],
    ) -> None:
        """
        Captura automática de lead (sin depender de tool-calls) cuando ya existe contacto en la conversación.
        Envía email solo una vez por conversación.
        """
        try:
            if not self.resend_client.is_configured():
                return

            if any((m.get("metadata") or {}).get("type") == "lead_capture" for m in (conversation_history or [])):
                return

            known_contact = (lead_context.get("known_contact") or "").strip()
            if not known_contact:
                return

            known_name = (lead_context.get("known_name") or "").strip() or "No proporcionado"

            booking_state = self._get_booking_state(conversation_history, conversation_id)
            if booking_state:
                interest = self._interest_from_booking_state(booking_state)
                booking_details = (booking_state.get("details") or {}) if isinstance(booking_state, dict) else None
            else:
                # Evitar emails "vacíos" (solo contacto, sin interés). Si no hay contenido útil, no enviamos aún.
                user_text = " \n".join(
                    (m.get("message") or "")
                    for m in (conversation_history or [])
                    if m.get("role") == "user" and (m.get("message") or "").strip()
                )
                scrubbed = re.sub(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", "", user_text, flags=re.IGNORECASE)
                scrubbed = re.sub(r"(\+?\d[\d\s\-()]{7,}\d)", "", scrubbed)
                scrubbed = re.sub(r"\s+", " ", scrubbed).strip()
                if len(scrubbed) < 12 and lead_context.get("lead_intent") in (None, "", "general"):
                    return

                snippet = self._build_conversation_snippet(conversation_history, max_messages=12)
                # Aprovecha GPT-5.2 para resumir sin inventar.
                interest = self.chatbot_ai.summarize_lead_interest(
                    conversation_snippet=snippet,
                    known_name=(lead_context.get("known_name") or None),
                    known_contact=known_contact,
                    booking_details=None,
                )
                booking_details = None

            if not interest:
                interest = "No especificado"

            send_result = self.resend_client.send_conversation_summary(
                user_name=known_name,
                user_interest=interest,
                user_contact=known_contact,
                conversation_id=conversation_id,
                platform=platform,
            )

            self.conversation_store.save_message(
                user_id=user_id,
                role="assistant",
                message="",
                conversation_id=conversation_id,
                metadata={
                    "platform": (platform or "web").lower(),
                    "type": "lead_capture",
                    "source": "auto",
                    "args": {"nombre": known_name, "interes": interest, "contacto": known_contact, "booking": booking_details},
                    "sent": bool(send_result.get("success")),
                    "error": send_result.get("error"),
                },
            )
        except Exception as e:
            print(f"❌ Error en auto lead capture: {e}")

    def finalize_conversation(self, user_id: str, reason: str = "end") -> None:
        """
        Compila información extraída de la conversación (nombre/contacto/interés/reserva)
        y envía un resumen final por correo. Se ejecuta una sola vez por conversación.
        """
        try:
            conversation_id = self.conversation_store.get_latest_conversation_id(user_id)
            if not conversation_id:
                return

            history = self.conversation_store.get_conversation_history(
                user_id=user_id, conversation_id=conversation_id, limit=100
            )

            # Evitar duplicados
            if any((m.get("metadata") or {}).get("type") == "conversation_summary" for m in (history or [])):
                return

            summary = self._compile_conversation_summary(
                user_id=user_id, conversation_id=conversation_id, history=history, reason=reason
            )

            subject = f"Resumen conversación ({reason}) - {conversation_id}"
            send_result = self.resend_client.send_conversation_end_summary(
                subject=subject,
                summary_text=summary,
                conversation_id=conversation_id,
                user_id=user_id,
                platform="Web",
            )

            self.conversation_store.save_message(
                user_id=user_id,
                role="assistant",
                message="",
                conversation_id=conversation_id,
                metadata={
                    "platform": "web",
                    "type": "conversation_summary",
                    "reason": reason,
                    "sent": bool(send_result.get("success")),
                    "error": send_result.get("error"),
                },
            )
        except Exception as e:
            print(f"❌ Error finalizando conversación: {e}")

    def _compile_conversation_summary(self, user_id: str, conversation_id: str, history: list, reason: str) -> str:
        # Preferir info explícita capturada por tool
        lead_args = None
        latest_booking_state = None
        user_messages: list[str] = []

        for msg in history or []:
            metadata = msg.get("metadata") or {}
            if metadata.get("type") == "lead_capture" and isinstance(metadata.get("args"), dict):
                lead_args = metadata.get("args")  # el último gana
            if metadata.get("type") == "booking_state" and isinstance(metadata.get("state"), dict):
                latest_booking_state = metadata.get("state")
            if msg.get("role") == "user" and msg.get("message"):
                user_messages.append(str(msg.get("message")))

        nombre = (lead_args or {}).get("nombre") if lead_args else None
        interes = (lead_args or {}).get("interes") if lead_args else None
        contacto = (lead_args or {}).get("contacto") if lead_args else None

        # Fallbacks desde booking state
        booking_details = (latest_booking_state or {}).get("details") or {}
        if not nombre:
            nombre = booking_details.get("full_name")
        booking_contact_parts = [booking_details.get("email"), booking_details.get("phone")]
        booking_contact = " / ".join([p for p in booking_contact_parts if p])
        if not contacto:
            contacto = booking_contact or None

        # Fallbacks desde texto
        if not nombre:
            joined = " \n".join(user_messages[-10:])
            m = re.search(
                r"\b(me llamo|soy)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+){0,4})\b",
                joined,
                re.IGNORECASE,
            )
            if m:
                nombre = m.group(2).strip(" .,!¿?;:")

        emails = re.findall(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", " \n".join(user_messages), re.IGNORECASE)
        phones = re.findall(r"(\+?\d[\d\s\-()]{7,}\d)", " \n".join(user_messages))
        extra_contact = " / ".join([*emails, *phones]).strip() or None
        if not contacto and extra_contact:
            contacto = extra_contact

        if not interes:
            interes = " | ".join([m.strip() for m in user_messages[-5:] if m.strip()]) or None

        lines = []
        lines.append(f"Motivo cierre: {reason}")
        lines.append(f"Nombre: {nombre or 'No identificado'}")
        lines.append(f"Contacto: {contacto or 'No identificado'}")
        lines.append(f"Interés/objetivo: {interes or 'No identificado'}")

        # Reserva (si aplica)
        if latest_booking_state:
            visit_date = latest_booking_state.get("visit_date")
            visit_day = latest_booking_state.get("visit_day")
            stage = latest_booking_state.get("stage")
            arrival_time = booking_details.get("arrival_time")
            cars = booking_details.get("cars_count")
            motos = booking_details.get("motos_count")
            people = booking_details.get("people_count")
            price_clp = latest_booking_state.get("price_clp")
            lines.append("")
            lines.append("Reserva:")
            lines.append(f"- Estado: {stage}")
            lines.append(f"- Día/fecha: {visit_day or 'N/A'} {visit_date or ''}".strip())
            lines.append(f"- Hora llegada: {arrival_time or 'N/A'}")
            lines.append(f"- Autos: {cars if cars is not None else 'N/A'} | Motos: {motos if motos is not None else 'N/A'} | Personas: {people if people is not None else 'N/A'}")
            if price_clp is not None:
                try:
                    lines.append(f"- Tarifa: ${int(price_clp):,} CLP".replace(",", "."))
                except Exception:
                    lines.append(f"- Tarifa: {price_clp}")

        lines.append("")
        lines.append("Mensajes usuario (últimos 8):")
        for m in user_messages[-8:]:
            lines.append(f"- {m.strip()}")

        # Evitar HTML injection en mail (la plantilla usa white-space: pre-wrap)
        return escape("\n".join(lines))

    def start_web_conversation(self, user_id: str) -> str:
        """
        Registra un mensaje de bienvenida para sesiones web.
        Esto ayuda a evitar el "doble saludo": el widget muestra este saludo al cargar
        y el modelo debe continuar directo cuando el usuario escriba.
        """
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"

        greeting = self._sanitize_user_response(
            "¡Hola! Soy Hernando, tu anfitrión en el Fundo Moraga. ¿En qué puedo ayudarte?"
        )

        self.conversation_store.save_message(
            user_id=user_id,
            role="assistant",
            message=greeting,
            conversation_id=conversation_id,
            metadata={"platform": "web", "source": "widget", "type": "welcome"},
        )

        return greeting

    # ============= BOOKING FLOW (WEB) =============

    def _handle_booking_flow(
        self,
        user_id: str,
        conversation_id: str,
        message_text: str,
        conversation_history: list,
        platform: str,
    ) -> Optional[str]:
        """Maneja un flujo de agendamiento con verificación de transferencia.

        Reglas:
        - Se agenda de lunes a viernes (09:00–17:00) con tarifa por autos/motos.
        - Sábado es solo grupos: $200.000 el día.
        - Domingo: no se agenda.
        - La reserva se confirma (email + Google Calendar) solo tras recibir el correo del banco.
        - Si el usuario no transfiere en 10 minutos desde que confirma que transferirá, se cierra el chat.
        """
        state = self._get_booking_state(conversation_history, conversation_id) or {}
        stage = state.get("stage")

        if stage == "awaiting_transfer" and state.get("transfer_deadline"):
            try:
                deadline = datetime.fromisoformat(state["transfer_deadline"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > deadline:
                    state["stage"] = "closed"
                    self._save_booking_state(user_id, conversation_id, state, platform=platform)
                    close_token = " [[CLOSE_CHAT]]" if (platform or "").lower() == "web" else ""
                    return (
                        "Se cumplió el plazo de 10 minutos sin confirmación de transferencia, así que cierro esta solicitud. "
                        f"Si quieres intentarlo de nuevo, escríbeme nuevamente.{close_token}"
                    )
            except Exception:
                pass

        if stage == "awaiting_day":
            visit_date = self._parse_visit_date(message_text)
            # Si venimos de una pregunta tipo "¿hoy o próximo viernes?", elegimos según la respuesta.
            if not visit_date:
                picked = self._pick_suggested_date_from_state(message_text, state)
                if picked:
                    # Limpiar sugerencias múltiples una vez elegida.
                    state.pop("suggested_date_today", None)
                    state.pop("suggested_date_next", None)
                    visit_date = picked
            # Confirmación simple (ej: "sí") cuando ya propusimos una fecha
            t_lower = (message_text or "").strip().lower()
            if not visit_date and any(x in t_lower for x in ("sí", "si", "dale", "ok", "de acuerdo", "confirmo")):
                suggested_iso = state.get("suggested_date")
                if suggested_iso:
                    visit_date = self._safe_date_from_iso(suggested_iso)

            if not visit_date:
                # Si el usuario dijo un día de la semana (ej: "viernes"), proponemos la próxima fecha.
                visit_day_hint = self._parse_weekday_name_es(message_text)
                if visit_day_hint:
                    today = self._today_local_date()
                    today_option, next_option = self._weekday_date_options(visit_day_hint, base_date=today)

                    # Caso especial: si hoy YA es ese día, ofrecemos 2 opciones (hoy vs próximo).
                    if today_option and next_option:
                        tl = t_lower
                        chosen = None
                        if "hoy" in tl:
                            chosen = today_option
                        elif any(x in tl for x in ("próximo", "proximo", "siguiente", "la otra", "otra semana", "próxima semana", "proxima semana")):
                            chosen = next_option

                        arrival_time = self._parse_arrival_time(message_text)
                        if not chosen:
                            state.pop("suggested_date", None)
                            state["suggested_day"] = visit_day_hint
                            state["suggested_date_today"] = today_option.isoformat()
                            state["suggested_date_next"] = next_option.isoformat()
                            self._save_booking_state(user_id, conversation_id, state, platform=platform)

                            time_part = ""
                            if arrival_time:
                                time_part = f" a las **{arrival_time}**"

                            return (
                                f"¡Buenísimo! Para **{visit_day_hint}**{time_part}, ¿te refieres a **hoy** ({today_option.isoformat()}) "
                                f"o al **próximo {visit_day_hint}** ({next_option.isoformat()})? (dime “hoy” o “próximo”)"
                            )

                        # Elegido explícitamente: guardamos y seguimos normal.
                        state["suggested_date"] = chosen.isoformat()
                        state["suggested_day"] = visit_day_hint
                        self._save_booking_state(user_id, conversation_id, state, platform=platform)
                        suggested = chosen
                    else:
                        suggested = self._next_weekday_date(visit_day_hint, base_date=today)
                        # Guardar sugerencia para que un "sí" posterior la confirme
                        state["suggested_date"] = suggested.isoformat() if suggested else None
                        state["suggested_day"] = visit_day_hint
                        self._save_booking_state(user_id, conversation_id, state, platform=platform)

                    suggested_txt = suggested.isoformat() if suggested else "YYYY-MM-DD"

                    # Si el usuario ya dio hora en el mismo mensaje, avanzamos al siguiente paso.
                    arrival_time = self._parse_arrival_time(message_text)
                    if arrival_time and suggested:
                        state = {
                            "stage": "collecting_details",
                            "visit_date": suggested.isoformat(),
                            "visit_day": visit_day_hint,
                            "details": {"arrival_time": arrival_time},
                        }
                        self._save_booking_state(user_id, conversation_id, state, platform=platform)
                        return (
                            f"¡Perfecto! Entonces **{visit_day_hint} {suggested.isoformat()}** a las **{arrival_time}**. "
                            "Para dejarlo coordinado, ¿vienes en auto o moto (¿cuántos)? "
                            "Y si te acomoda, déjame tu nombre completo y un teléfono/correo para confirmación."
                        )

                    return (
                        f"¡Buenísimo! ¿Te refieres a este **{visit_day_hint}** ({suggested_txt}) u otra fecha? "
                        "Y para coordinar, ¿a qué hora te gustaría llegar? (entre 09:00 y 17:00)"
                    )

                return "¡Buenísimo! ¿Qué fecha te gustaría venir para agendar? (ideal: YYYY-MM-DD) ¿Y a qué hora te gustaría llegar? (09:00–17:00)"

            visit_day = self._day_name_es(visit_date)
            if visit_day == "domingo":
                state["stage"] = "closed"
                self._save_booking_state(user_id, conversation_id, state, platform=platform)
                close_token = " [[CLOSE_CHAT]]" if (platform or "").lower() == "web" else ""
                return f"Los domingos no estamos agendando. ¿Te acomoda lunes a sábado?{close_token}"

            arrival_time = self._parse_arrival_time(message_text)
            details = {"arrival_time": arrival_time} if arrival_time else {}

            state = {
                "stage": "collecting_details",
                "visit_date": visit_date.isoformat(),
                "visit_day": visit_day,
                "details": details,
            }
            self._save_booking_state(user_id, conversation_id, state, platform=platform)
            return self._booking_details_prompt(visit_day, visit_date, arrival_time=arrival_time)

        if stage == "collecting_details":
            visit_day = state.get("visit_day") or "por confirmar"
            visit_date = self._safe_date_from_iso(state.get("visit_date"))
            details = state.get("details") or {}
            awaiting_field = (state.get("awaiting_field") or "").strip()
            raw = (message_text or "").strip()

            # Si acabamos de preguntar por una cantidad específica (autos/motos),
            # una respuesta tipo "2" debe interpretarse como cantidad, no como hora.
            if awaiting_field in ("cars_count", "motos_count") and re.fullmatch(r"\d{1,3}", raw):
                count = self._parse_int(raw)
                if count is not None:
                    details[awaiting_field] = count
                    # Normalizar señal de tipo de vehículo para prompts posteriores.
                    if awaiting_field == "cars_count":
                        details.setdefault("vehicle_kind", "auto")
                    if awaiting_field == "motos_count":
                        details.setdefault("vehicle_kind", "moto")
            else:
                details.update(self._parse_booking_details(message_text))
            state["details"] = details

            # Normalizar vehículos: si solo se reporta uno, el otro se asume 0.
            if details.get("cars_count") is None and details.get("motos_count") is not None:
                details["cars_count"] = 0
            if details.get("motos_count") is None and details.get("cars_count") is not None:
                details["motos_count"] = 0

            missing = []
            if not details.get("arrival_time"):
                missing.append("arrival_time")

            if details.get("cars_count") is None and details.get("motos_count") is None:
                missing.append("vehicles")

            if details.get("full_name") is None:
                missing.append("full_name")
            if details.get("phone") is None:
                missing.append("phone")
            if details.get("email") is None:
                missing.append("email")

            if missing:
                state["awaiting_field"] = self._infer_booking_awaiting_field(missing, details)
                self._save_booking_state(user_id, conversation_id, state, platform=platform)
                return self._booking_missing_prompt(visit_day, missing, details=details)

            cars_count = int(details.get("cars_count") or 0)
            motos_count = int(details.get("motos_count") or 0)
            price_clp = self._calculate_price(visit_day, cars_count, motos_count)
            state["price_clp"] = price_clp
            state["stage"] = "confirm_transfer"
            state.pop("awaiting_field", None)
            self._save_booking_state(user_id, conversation_id, state, platform=platform)

            return self._transfer_prompt(visit_day, visit_date, price_clp, details)

        if stage == "confirm_transfer":
            t = (message_text or "").strip().lower()
            if any(x in t for x in ("sí", "si", "dale", "ok", "haré", "hare", "voy a", "ya")):
                now = datetime.now(timezone.utc)
                state["stage"] = "awaiting_transfer"
                state["transfer_started_at"] = now.isoformat().replace("+00:00", "Z")
                state["transfer_deadline"] = (now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
                self._save_booking_state(user_id, conversation_id, state, platform=platform)
                return "Perfecto. Avísame cuando la hayas completado (por ejemplo: “listo, transferí”) y reviso el correo del banco."

            if any(x in t for x in ("no", "nop", "después", "despues")):
                state["stage"] = "closed"
                self._save_booking_state(user_id, conversation_id, state, platform=platform)
                close_token = " [[CLOSE_CHAT]]" if (platform or "").lower() == "web" else ""
                return f"Entendido. La reserva solo queda válida con transferencia, así que cierro esta solicitud.{close_token}"

            return "¿Harás la transferencia ahora? Responde “sí” o “no”, por favor."

        if stage == "awaiting_transfer":
            t = (message_text or "").lower()
            if any(x in t for x in ("listo", "transfer", "hecho", "pagado", "enviado")):
                since_iso = state.get("transfer_started_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                if not self.payment_inbox.is_configured():
                    return (
                        "Estoy listo para confirmar, pero aún no tengo acceso configurado a la bandeja de pagos. "
                        "Por ahora, envía el comprobante a `contacto@fundomoraga.com` y te confirmamos por ese medio."
                    )

                check = self.payment_inbox.find_payment_email(since_iso=since_iso)
                if not check.found:
                    return "Aún no me aparece el correo del banco. Dame 1–2 minutos y vuelve a escribirme “listo” para revisar de nuevo (dentro de los 10 minutos)."

                visit_day = state.get("visit_day") or "por confirmar"
                visit_date = self._safe_date_from_iso(state.get("visit_date"))
                details = state.get("details") or {}
                price_clp = int(state.get("price_clp") or 0)

                send_result = self.resend_client.send_booking_request(
                    visit_date=(visit_date.isoformat() if visit_date else "por confirmar"),
                    visit_day=visit_day,
                    full_name=details.get("full_name", "No proporcionado"),
                    phone=details.get("phone", "No proporcionado"),
                    email=details.get("email", "No proporcionado"),
                    cars_count=int(details.get("cars_count") or 0),
                    motos_count=int(details.get("motos_count") or 0),
                    people_count=int(details.get("people_count") or 0),
                    price_clp=price_clp,
                    conversation_id=conversation_id,
                    platform=platform,
                    additional_notes=(
                        f"Hora llegada: {details.get('arrival_time')}. "
                        f"Pago verificado por inbox. From: {check.from_email} Subject: {check.subject}"
                    ),
                )

                calendar_ok = False
                calendar_error = None
                try:
                    if visit_date:
                        start_iso, end_iso = self._event_times(visit_date)
                        description = self._calendar_description(conversation_id, details, price_clp, check)
                        req = CalendarEventRequest(
                            summary=f"Reserva Fundo Moraga ({visit_day}) - {details.get('full_name','')}".strip(),
                            description=description,
                            start_iso=start_iso,
                            end_iso=end_iso,
                            timezone=config.GOOGLE_CALENDAR_TIMEZONE,
                            attendees=[
                                "efrainantoniomoraga@gmail.com",
                                "pierinabertoni@gmail.com",
                                "contacto@fundomoraga.com",
                            ],
                        )
                        self.calendar_client.create_event(req)
                        calendar_ok = True
                except Exception as e:
                    calendar_error = str(e)

                state["stage"] = "confirmed" if send_result.get("success") else "error"
                state["confirmed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self._save_booking_state(user_id, conversation_id, state, platform=platform)

                if send_result.get("success"):
                    cal_msg = "y agendé Google Calendar" if calendar_ok else f"pero no pude agendar Calendar ({calendar_error})"
                    return (
                        f"¡Listo! Recibí el correo del banco: tu reserva quedó confirmada para **{visit_day}** "
                        f"de **09:00 a 17:00**. Ya envié el formulario a `contacto@fundomoraga.com` {cal_msg}."
                    )

                return "Recibí el correo del banco, pero tuve un problema enviando el formulario. Intenta nuevamente en unos minutos."

            return "Quedo atento: cuando completes la transferencia, dime “listo, transferí” y reviso el correo del banco."

        if stage in ("confirmed", "closed", "error"):
            return None

        # Iniciar flujo si detectamos intención de agendar/reservar
        if self._is_booking_intent(message_text):
            visit_date = self._parse_visit_date(message_text)
            if visit_date:
                visit_day = self._day_name_es(visit_date)
                if visit_day == "domingo":
                    state["stage"] = "closed"
                    self._save_booking_state(user_id, conversation_id, state, platform=platform)
                    close_token = " [[CLOSE_CHAT]]" if (platform or "").lower() == "web" else ""
                    return f"Los domingos no estamos agendando. ¿Te acomoda lunes a sábado?{close_token}"

                arrival_time = self._parse_arrival_time(message_text)
                details = {"arrival_time": arrival_time} if arrival_time else {}
                state = {
                    "stage": "collecting_details",
                    "visit_date": visit_date.isoformat(),
                    "visit_day": visit_day,
                    "details": details,
                }
                self._save_booking_state(user_id, conversation_id, state, platform=platform)
                return self._booking_details_prompt(visit_day, visit_date, arrival_time=arrival_time)

            # Si el usuario dijo un día de la semana, proponemos la próxima fecha.
            visit_day_hint = self._parse_weekday_name_es(message_text)
            if visit_day_hint:
                today = self._today_local_date()
                today_option, next_option = self._weekday_date_options(visit_day_hint, base_date=today)
                t_lower = (message_text or "").strip().lower()
                arrival_time = self._parse_arrival_time(message_text)

                # Si hoy es ese día, ofrecer dos opciones
                if today_option and next_option:
                    chosen = None
                    if "hoy" in t_lower:
                        chosen = today_option
                    elif any(x in t_lower for x in ("próximo", "proximo", "siguiente", "la otra", "otra semana", "próxima semana", "proxima semana")):
                        chosen = next_option

                    if not chosen:
                        state = {
                            "stage": "awaiting_day",
                            "suggested_day": visit_day_hint,
                            "suggested_date_today": today_option.isoformat(),
                            "suggested_date_next": next_option.isoformat(),
                        }
                        self._save_booking_state(user_id, conversation_id, state, platform=platform)

                        time_part = f" a las **{arrival_time}**" if arrival_time else ""
                        return (
                            f"¡Buenísimo! Para **{visit_day_hint}**{time_part}, ¿te refieres a **hoy** ({today_option.isoformat()}) "
                            f"o al **próximo {visit_day_hint}** ({next_option.isoformat()})? (dime “hoy” o “próximo”)"
                        )

                    # Ya eligió explícitamente: avanzamos.
                    if arrival_time:
                        state = {
                            "stage": "collecting_details",
                            "visit_date": chosen.isoformat(),
                            "visit_day": visit_day_hint,
                            "details": {"arrival_time": arrival_time},
                        }
                        self._save_booking_state(user_id, conversation_id, state, platform=platform)
                        return (
                            f"¡Perfecto! Entonces **{visit_day_hint} {chosen.isoformat()}** a las **{arrival_time}**. "
                            "Para dejarlo coordinado, ¿vienes en auto o moto, y cuántos?"
                        )

                    state = {
                        "stage": "awaiting_day",
                        "suggested_day": visit_day_hint,
                        "suggested_date": chosen.isoformat(),
                    }
                    self._save_booking_state(user_id, conversation_id, state, platform=platform)
                    return (
                        f"¡Buenísimo! ¿Te refieres a este **{visit_day_hint}** ({chosen.isoformat()}) u otra fecha? "
                        "Y para coordinar, ¿a qué hora te gustaría llegar? (09:00–17:00)"
                    )

                # Caso normal: proponemos próxima fecha única y la guardamos
                suggested = self._next_weekday_date(visit_day_hint, base_date=today)
                state = {"stage": "awaiting_day", "suggested_day": visit_day_hint, "suggested_date": suggested.isoformat() if suggested else None}
                self._save_booking_state(user_id, conversation_id, state, platform=platform)
                suggested_txt = suggested.isoformat() if suggested else "YYYY-MM-DD"
                return (
                    f"¡Buenísimo! ¿Te acomoda este **{visit_day_hint}** ({suggested_txt}) u otra fecha? "
                    "Y para coordinar, ¿a qué hora te gustaría llegar? (09:00–17:00)"
                )

            state = {"stage": "awaiting_day"}
            self._save_booking_state(user_id, conversation_id, state, platform=platform)
            return "¡Buenísimo! ¿Qué fecha te gustaría venir para agendar? (ideal: YYYY-MM-DD) ¿Y a qué hora te gustaría llegar? (09:00–17:00)"

        return None

    def _get_booking_state(self, conversation_history: list, conversation_id: str) -> Optional[Dict]:
        for msg in reversed(conversation_history or []):
            metadata = msg.get("metadata") or {}
            if msg.get("conversationId") != conversation_id:
                continue
            if metadata.get("type") == "booking_state" and isinstance(metadata.get("state"), dict):
                return metadata["state"]
        return None

    def _save_booking_state(self, user_id: str, conversation_id: str, state: Dict, *, platform: str = "web") -> None:
        self.conversation_store.save_message(
            user_id=user_id,
            role="assistant",
            message="",
            conversation_id=conversation_id,
            metadata={"platform": (platform or "web").lower(), "type": "booking_state", "state": state},
        )

    def _is_booking_intent(self, text: str) -> bool:
        t = (text or "").lower().strip()
        if not t:
            return False

        keywords = [
            "agendar",
            "agenda",
            "reservar",
            "reserva",
            "agend",
            "quiero ir",
            "quiero venir",
            "quiero visitar",
            "quiero pasar",
            "me gustaría ir",
            "me gustaria ir",
            "me gustaría venir",
            "me gustaria venir",
            "se puede ir",
            "puedo ir",
            "podemos ir",
            "ir el ",
            "venir el ",
        ]
        if any(k in t for k in keywords):
            return True

        # Si el usuario responde solo con una fecha, también lo interpretamos como intención de agendar.
        if re.search(r"\b\d{4}-\d{2}-\d{2}\b", t):
            return True
        if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", t):
            return True

        # Señales suaves de agendamiento: día/fecha + intención de visitar (o hora).
        has_weekday = self._parse_weekday_name_es(t) is not None
        has_relative_day = any(x in t for x in ("hoy", "mañana", "manana", "pasado mañana", "pasado manana"))
        has_time = self._parse_arrival_time(t) is not None

        price_markers = ("precio", "precios", "tarifa", "tarifas", "valor", "cuánto", "cuanto", "cuesta", "$")

        visit_markers = (
            "ir",
            "venir",
            "visitar",
            "pasar",
            "llegar",
            "entrada",
            "ingreso",
            "entrar",
            "ingresar",
        )
        has_visit_intent = any(re.search(rf"\b{re.escape(v)}\b", t) for v in visit_markers)

        if (has_weekday or has_relative_day) and (has_visit_intent or has_time):
            return True

        # Respuestas cortas tipo "viernes" suelen ser continuación de una coordinación.
        if has_weekday and len(t.split()) <= 3 and not any(p in t for p in price_markers):
            return True

        return False

    def _parse_visit_day(self, text: str) -> Optional[str]:
        t = (text or "").lower()
        if "viernes" in t:
            return "viernes"
        if "sábado" in t or "sabado" in t:
            return "sábado"
        if "domingo" in t:
            return "domingo"
        if "lunes" in t:
            return "lunes"
        if "martes" in t:
            return "martes"
        if "miércoles" in t or "miercoles" in t:
            return "miércoles"
        if "jueves" in t:
            return "jueves"

        date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?)\b", t)
        if date_match:
            return date_match.group(1)

        iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        if iso_match:
            return iso_match.group(1)

        return None

    def _parse_visit_date(self, text: str) -> Optional[date]:
        t = (text or "").strip()
        if not t:
            return None

        tl = t.lower()
        today = self._today_local_date()

        if "pasado mañana" in tl or "pasado manana" in tl:
            return today + timedelta(days=2)
        if "mañana" in tl or "manana" in tl:
            return today + timedelta(days=1)
        if "hoy" in tl:
            return today

        # "este viernes", "el viernes", etc.
        weekday_hint = self._parse_weekday_name_es(tl)
        if weekday_hint:
            # Si hoy ya es ese día y no está explícito "hoy/próximo", evitamos asumir: el caller ofrecerá opciones.
            if self._day_name_es(today) == weekday_hint:
                if "hoy" in tl:
                    return today
                if any(x in tl for x in ("próximo", "proximo", "siguiente", "la otra", "otra semana", "próxima semana", "proxima semana")):
                    return today + timedelta(days=7)
                return None
            return self._next_weekday_date(weekday_hint, base_date=today)

        iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        if iso_match:
            try:
                return date.fromisoformat(iso_match.group(1))
            except Exception:
                return None

        dmy_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", t)
        if dmy_match:
            dd = int(dmy_match.group(1))
            mm = int(dmy_match.group(2))
            yyyy = int(dmy_match.group(3))
            if yyyy < 100:
                yyyy += 2000
            try:
                return date(yyyy, mm, dd)
            except Exception:
                return None

        return None

    def _parse_arrival_time(self, text: str) -> Optional[str]:
        """
        Extrae hora de llegada en formato HH:MM desde frases como:
        - "10:30"
        - "a las 9"
        - "9am" / "9 am"
        """
        raw = (text or "").lower().strip()
        if not raw:
            return None

        m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", raw)
        if m:
            return f"{int(m.group(1)):02d}:{m.group(2)}"

        # "a las 9" / "a las 9:30"
        m = re.search(r"\ba\s+las\s+([01]?\d|2[0-3])(?:[:.]([0-5]\d))?\b", raw)
        if m:
            hour = int(m.group(1))
            minute = m.group(2) or "00"
            return f"{hour:02d}:{minute}"

        # "9am" / "9 pm"
        m = re.search(r"\b([01]?\d|2[0-3])\s*(am|pm)\b", raw)
        if m:
            hour = int(m.group(1))
            mer = m.group(2)
            if mer == "pm" and hour < 12:
                hour += 12
            if mer == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:00"

        # Respuesta corta (solo número): solo si el mensaje es EXACTAMENTE el número.
        m = re.fullmatch(r"([01]?\d|2[0-3])", raw)
        if not m:
            return None

        hour = int(m.group(1))
        return f"{hour:02d}:00"

    def _parse_weekday_name_es(self, text: str) -> Optional[str]:
        t = (text or "").lower()
        if "lunes" in t:
            return "lunes"
        if "martes" in t:
            return "martes"
        if "miércoles" in t or "miercoles" in t:
            return "miércoles"
        if "jueves" in t:
            return "jueves"
        if "viernes" in t:
            return "viernes"
        if "sábado" in t or "sabado" in t:
            return "sábado"
        if "domingo" in t:
            return "domingo"
        return None

    def _today_local_date(self) -> date:
        tz_name = getattr(config, "GOOGLE_CALENDAR_TIMEZONE", None) or "America/Santiago"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        return datetime.now(tz).date()

    def _next_weekday_date(
        self, weekday_es: str, *, base_date: Optional[date] = None, include_today: bool = False
    ) -> Optional[date]:
        names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        if weekday_es not in names:
            return None
        target = names.index(weekday_es)
        today = base_date or self._today_local_date()
        days_ahead = (target - today.weekday()) % 7
        if days_ahead == 0 and not include_today:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    def _weekday_date_options(self, weekday_es: str, *, base_date: Optional[date] = None) -> tuple[Optional[date], Optional[date]]:
        base = base_date or self._today_local_date()
        today_option = base if self._day_name_es(base) == weekday_es else None
        next_option = self._next_weekday_date(weekday_es, base_date=base, include_today=False)
        return today_option, next_option

    def _day_name_es(self, d: date) -> str:
        names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return names[d.weekday()]

    def _safe_date_from_iso(self, iso_str: Optional[str]) -> Optional[date]:
        if not iso_str:
            return None
        try:
            return date.fromisoformat(iso_str)
        except Exception:
            return None

    def _pick_suggested_date_from_state(self, message_text: str, state: Dict) -> Optional[date]:
        t = (message_text or "").strip().lower()
        today_iso = state.get("suggested_date_today")
        next_iso = state.get("suggested_date_next")
        if not (today_iso and next_iso):
            return None

        if any(x in t for x in ("hoy", "hoy mismo", "ahora", "ya")):
            return self._safe_date_from_iso(today_iso)
        if any(x in t for x in ("próximo", "proximo", "siguiente", "la otra", "otra semana", "próxima semana", "proxima semana")):
            return self._safe_date_from_iso(next_iso)
        return None

    def _calculate_price(self, visit_day: str, cars_count: int, motos_count: int) -> int:
        if visit_day == "sábado":
            return 200000
        return int(cars_count) * 15000 + int(motos_count) * 10000

    def _parse_booking_details(self, text: str) -> Dict:
        raw = (text or "").strip()
        if not raw:
            return {}

        details: Dict = {}
        raw_l = raw.lower()

        # Parse key:value lines (recommended format)
        for line in raw.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            k = key.strip().lower()
            v = value.strip()
            if not v:
                continue
            if k in ("nombre", "nombres", "nombre y apellido", "nombre y apellidos", "nombres y apellidos"):
                details["full_name"] = v
            elif k in ("apellido", "apellidos"):
                details["full_name"] = (details.get("full_name", "") + " " + v).strip()
            elif k in ("teléfono", "telefono", "celular", "móvil", "movil"):
                details["phone"] = v
            elif k in ("email", "correo", "correo electrónico", "correo electronico"):
                details["email"] = v
            elif k in ("hora", "hora de llegada", "hora llegada", "hora visita", "hora de visita"):
                details["arrival_time"] = v
            elif k in ("autos", "automóviles", "automoviles", "vehículos", "vehiculos"):
                details["cars_count"] = self._parse_int(v)
            elif k in ("motos", "moto"):
                details["motos_count"] = self._parse_int(v)
            elif k in ("personas", "asistentes", "pasajeros"):
                details["people_count"] = self._parse_int(v)

        # Fallback extractions
        if "email" not in details:
            email_match = re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", raw, re.IGNORECASE)
            if email_match:
                details["email"] = email_match.group(1)

        if "phone" not in details:
            phone_match = re.search(r"(\+?\d[\d\s\-()]{7,}\d)", raw)
            if phone_match:
                details["phone"] = phone_match.group(1).strip()

        if "full_name" not in details:
            name_match = re.search(r"\b(me llamo|soy)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+){1,4})\b", raw, re.IGNORECASE)
            if name_match:
                details["full_name"] = name_match.group(2).strip(" .,!¿?;:")

        if "cars_count" not in details or details.get("cars_count") is None:
            m = re.search(r"\b(\d+)\s*(autos|auto|autom[oó]viles|veh[ií]culos)\b", raw, re.IGNORECASE)
            if m:
                details["cars_count"] = int(m.group(1))

        if "motos_count" not in details or details.get("motos_count") is None:
            m = re.search(r"\b(\d+)\s*(motos|moto)\b", raw, re.IGNORECASE)
            if m:
                details["motos_count"] = int(m.group(1))

        if "people_count" not in details or details.get("people_count") is None:
            m = re.search(r"\b(\d+)\s*(personas|asistentes|pasajeros)\b", raw, re.IGNORECASE)
            if m:
                details["people_count"] = int(m.group(1))

        if "arrival_time" not in details:
            parsed = self._parse_arrival_time(raw)
            if parsed:
                details["arrival_time"] = parsed

        # Tipo de vehículo (sin cantidad) para preguntar más natural.
        if "vehicle_kind" not in details:
            has_auto = re.search(r"\b(auto|autos|autom[oó]vil|autom[oó]viles|veh[ií]culo|veh[ií]culos|4x4)\b", raw_l)
            has_moto = re.search(r"\b(moto|motos)\b", raw_l)
            if has_auto and not has_moto:
                details["vehicle_kind"] = "auto"
            elif has_moto and not has_auto:
                details["vehicle_kind"] = "moto"

        return details

    def _parse_int(self, value: str) -> Optional[int]:
        try:
            digits = re.sub(r"[^\d]", "", value)
            return int(digits) if digits else None
        except Exception:
            return None

    def _infer_booking_awaiting_field(self, missing: list, details: Optional[Dict] = None) -> str:
        """
        Infere qué campo estamos esperando para interpretar respuestas cortas (ej: "2").
        """
        next_key = missing[0] if missing else ""
        if next_key == "vehicles":
            kind = (details or {}).get("vehicle_kind")
            if kind == "auto":
                return "cars_count"
            if kind == "moto":
                return "motos_count"
            return "vehicles"
        return next_key

    def _booking_details_prompt(self, visit_day: str, visit_date: date, arrival_time: Optional[str] = None) -> str:
        if arrival_time:
            return (
                f"¡Perfecto! Entonces sería **{visit_day} {visit_date.isoformat()}** a las **{arrival_time}** "
                "(recuerda: horario 09:00 a 17:00). "
                "¿Vienes en auto o moto, y cuántos?"
            )

        return (
            f"¡Buenísimo! Entonces sería **{visit_day} {visit_date.isoformat()}** (horario 09:00 a 17:00). "
            "¿A qué hora te gustaría llegar?"
        )

    def _booking_missing_prompt(self, visit_day: str, missing: list, details: Optional[Dict] = None) -> str:
        # Pedimos 1 cosa a la vez para que suene natural (no interrogatorio).
        next_key = missing[0] if missing else None

        if next_key == "arrival_time":
            return "Perfecto. ¿A qué hora te gustaría llegar? (entre 09:00 y 17:00)"

        if next_key == "vehicles":
            kind = (details or {}).get("vehicle_kind")
            if kind == "auto":
                return "Perfecto, ¿cuántos autos vienen?"
            if kind == "moto":
                return "Perfecto, ¿cuántas motos vienen?"
            return "¿Vienes en auto o moto, y cuántos?"

        if next_key == "full_name":
            return "Genial. ¿Me dejas tu nombre y apellido para la reserva?"

        if next_key == "phone":
            return "¿Me compartes un teléfono de contacto, por favor?"

        if next_key == "email":
            return "¿Me compartes un correo de contacto, por favor?"

        # Fallback
        return f"Para dejarlo listo para **{visit_day}**, ¿me compartes un dato más?"

    def _transfer_prompt(self, visit_day: str, visit_date: Optional[date], price_clp: int, details: Dict) -> str:
        date_txt = visit_date.isoformat() if visit_date else "por confirmar"
        price_txt = f"${price_clp:,}".replace(",", ".")
        extra = " (sábado es tarifa por grupo)" if visit_day == "sábado" else ""
        arrival_time = (details or {}).get("arrival_time") or "por confirmar"

        return (
            f"Perfecto 😊 Para **{visit_day} {date_txt}**, llegada **{arrival_time}** (dentro de 09:00–17:00), la tarifa es **{price_txt} CLP**{extra}.\n\n"
            "Para dejarlo reservado, la visita queda válida una vez realizada la transferencia. "
            "¿Harás la transferencia ahora?\n\n"
            "Datos para transferir:\n"
            "SOCIEDAD FUNDO MORAGA SpA\n"
            "RUT: 78.178.465-6\n"
            "Banco de Chile\n"
            "Cuenta FAN Emprende\n"
            "00-023-87252-10\n"
            "Correo: contacto@fundomoraga.com"
        )

    def _event_times(self, visit_date: date) -> tuple[str, str]:
        tz = ZoneInfo(config.GOOGLE_CALENDAR_TIMEZONE)
        start_dt = datetime.combine(visit_date, time(9, 0), tzinfo=tz)
        end_dt = datetime.combine(visit_date, time(17, 0), tzinfo=tz)
        return start_dt.isoformat(), end_dt.isoformat()

    def _calendar_description(self, conversation_id: str, details: Dict, price_clp: int, payment_check) -> str:
        price_txt = f"${int(price_clp):,}".replace(",", ".")
        return (
            "Reserva generada por Hernando.\n\n"
            f"Nombre: {details.get('full_name')}\n"
            f"Teléfono: {details.get('phone')}\n"
            f"Email: {details.get('email')}\n"
            f"Hora llegada: {details.get('arrival_time')}\n"
            f"Autos: {details.get('cars_count')}\n"
            f"Motos: {details.get('motos_count')}\n"
            f"Personas: {details.get('people_count')}\n"
            f"Tarifa: {price_txt} CLP\n"
            f"Conversación ID: {conversation_id}\n\n"
            f"Pago verificado: {getattr(payment_check, 'received_at', None) or 'sí'}\n"
            f"From: {getattr(payment_check, 'from_email', '')}\n"
            f"Subject: {getattr(payment_check, 'subject', '')}\n"
        )
    
    def _send_lead_email(
        self,
        user_id: str,
        conversation_id: str,
        conversation_history: list,
        latest_message: str,
        platform: str,
        nombre: Optional[str] = None,
        interes: Optional[str] = None,
        contacto: Optional[str] = None,
    ):
        """
        Envía email con resumen de lead cuando se captura información del usuario
        
        Args:
            user_id: ID del usuario
            conversation_id: ID de la conversación
            conversation_history: Historial completo de mensajes
            latest_message: Último mensaje del usuario
            platform: Plataforma de origen (Instagram/Web)
        """
        try:
            # Extraer información del historial (si no viene desde el tool)
            nombre = (nombre or "").strip() if isinstance(nombre, str) else ""
            interes = (interes or "").strip() if isinstance(interes, str) else ""
            contacto = (contacto or "").strip() if isinstance(contacto, str) else ""

            if not nombre:
                nombre = "No proporcionado"
            if not contacto:
                contacto = "No proporcionado"
            
            # Construir el interés a partir de los mensajes del usuario
            mensajes_usuario = []
            for msg in conversation_history:
                if msg.get("role") == "user":
                    mensajes_usuario.append(msg.get("message", ""))
            
            # Agregar el mensaje actual
            mensajes_usuario.append(latest_message)
            
            # El interés es un resumen de lo que el usuario ha consultado (si no viene desde el tool)
            if not interes:
                interes = " | ".join(mensajes_usuario[-5:])  # Últimos 5 mensajes del usuario
            
            # Intentar extraer nombre y contacto de los mensajes (solo si faltan)
            if nombre == "No proporcionado" or contacto == "No proporcionado":
                for msg_content in mensajes_usuario:
                    msg_lower = msg_content.lower()

                    if nombre == "No proporcionado":
                        # Detectar nombre si menciona "soy", "me llamo", etc.
                        if any(phrase in msg_lower for phrase in ["soy ", "me llamo ", "mi nombre es "]):
                            for phrase in ["soy ", "me llamo ", "mi nombre es "]:
                                if phrase in msg_lower:
                                    idx = msg_lower.find(phrase)
                                    potential_name = msg_content[idx + len(phrase):].split()[0:3]
                                    if potential_name:
                                        nombre = " ".join(potential_name).strip(".,!?")
                                        break

                    # Detectar email
                    if "@" in msg_content and "." in msg_content:
                        words = msg_content.split()
                        for word in words:
                            if "@" in word and "." in word:
                                if contacto == "No proporcionado":
                                    contacto = word.strip(".,!?")
                                else:
                                    contacto += f" / {word.strip('.,!?')}"

                    # Detectar teléfono (patrones simples)
                    if any(digit in msg_content for digit in "0123456789"):
                        import re
                        phones = re.findall(r"[\+\d][\d\s\-\(\)]{7,}", msg_content)
                        for phone in phones:
                            if contacto == "No proporcionado":
                                contacto = phone.strip()
                            else:
                                contacto += f" / {phone.strip()}"
            
            # Enviar email con Resend
            result = self.resend_client.send_conversation_summary(
                user_name=nombre,
                user_interest=interes,
                user_contact=contacto,
                conversation_id=conversation_id,
                platform=platform
            )
            
            if result["success"]:
                print(f"✅ Email de lead enviado exitosamente para {conversation_id}")
            else:
                print(f"⚠️ Error enviando email de lead: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error en _send_lead_email: {str(e)}")
    
    def send_instagram_message(self, recipient_id: str, message_text: str) -> bool:
        """
        Envía un mensaje a través de la API de Instagram
        
        Args:
            recipient_id: ID del destinatario (IGID)
            message_text: Texto del mensaje a enviar
        
        Returns:
            True si se envió correctamente, False si hubo error
        """
        try:
            if not self.is_instagram_configured():
                print("⚠️ Instagram no configurado: falta INSTAGRAM_ACCESS_TOKEN")
                return False

            # URL de la API de Instagram Messaging
            url = f"https://graph.facebook.com/v18.0/me/messages"

            headers = {
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_type": "RESPONSE",
                "recipient": {"id": recipient_id},
                "message": {"text": message_text},
            }

            response = requests.post(
                url,
                params={"access_token": self.access_token},
                json=payload,
                headers=headers,
                timeout=15,
            )

            if response.status_code == 200:
                print(f"✅ Mensaje enviado a {recipient_id}")
                return True
            else:
                print(f"❌ Error enviando mensaje: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en send_instagram_message: {e}")
            return False

    def _extract_instagram_inbound_texts(self, webhook_data: Dict) -> list[tuple[str, str]]:
        """
        Extrae (sender_id, text) desde payloads de webhooks de Instagram.
        Soporta formato tipo Messenger (entry[].messaging[]) y formato tipo Graph (entry[].changes[]).
        """
        extracted: list[tuple[str, str]] = []

        for entry in webhook_data.get("entry") or []:
            # Formato tipo Messenger (Instagram Messaging API / Messenger Platform)
            for messaging_event in entry.get("messaging") or []:
                sender_id = (messaging_event.get("sender") or {}).get("id")
                if not sender_id:
                    continue

                if "message" in messaging_event:
                    message = messaging_event.get("message") or {}
                    if message.get("is_echo"):
                        continue

                    text = (message.get("text") or "").strip()
                    if not text:
                        quick_payload = ((message.get("quick_reply") or {}).get("payload") or "").strip()
                        if quick_payload:
                            text = quick_payload

                    if not text and message.get("attachments"):
                        text = "[adjunto]"

                    if text:
                        extracted.append((str(sender_id), text))
                        continue

                if "postback" in messaging_event:
                    postback = messaging_event.get("postback") or {}
                    payload = (postback.get("payload") or postback.get("title") or "").strip()
                    if payload:
                        extracted.append((str(sender_id), payload))

            # Formato tipo Graph (entry[].changes[])
            for change in entry.get("changes") or []:
                value = change.get("value") or {}

                sender_id = (
                    (value.get("sender") or {}).get("id")
                    or (value.get("from") or {}).get("id")
                    or value.get("sender_id")
                    or value.get("from_id")
                )
                if not sender_id:
                    continue

                text = ""
                message_value = value.get("message")
                if isinstance(message_value, dict):
                    text = (message_value.get("text") or "").strip()
                elif isinstance(message_value, str):
                    text = message_value.strip()

                if not text:
                    text = (value.get("text") or value.get("message_text") or "").strip()

                if text:
                    extracted.append((str(sender_id), text))

        return extracted
    
    def handle_webhook_message(self, webhook_data: Dict) -> None:
        """
        Maneja mensajes recibidos del webhook de Instagram
        
        Args:
            webhook_data: Datos recibidos del webhook
        """
        try:
            if not self.is_instagram_configured():
                print("⚠️ Webhook recibido pero Instagram no está configurado (falta INSTAGRAM_ACCESS_TOKEN).")
                return

            # Extraer información del webhook
            # Estructura de webhook de Instagram: 
            # https://developers.facebook.com/docs/messenger-platform/webhooks
            
            if "entry" not in webhook_data:
                return

            inbound_texts = self._extract_instagram_inbound_texts(webhook_data)
            if not inbound_texts:
                object_type = webhook_data.get("object")
                print(
                    "⚠️ Webhook recibido sin mensajes de texto procesables "
                    f"(object={object_type}, keys={list(webhook_data.keys())})"
                )
                return

            for sender_id, message_text in inbound_texts:
                if message_text == "[adjunto]":
                    response = "Recibí un adjunto. ¿Me puedes contar en texto qué necesitas o qué te gustaría coordinar?"
                else:
                    ig_user_id = f"ig_{sender_id}"
                    # Procesar mensaje y obtener respuesta
                    response = self.process_message(
                        ig_user_id,
                        message_text,
                        platform="instagram",
                        source="instagram_webhook",
                    )

                # Enviar respuesta al usuario
                self.send_instagram_message(sender_id, response)
        
        except Exception as e:
            print(f"❌ Error manejando webhook: {e}")
    
    def start_conversation(self, user_id: str) -> str:
        """
        Inicia una nueva conversación con un saludo
        
        Args:
            user_id: ID del usuario de Instagram
        
        Returns:
            Mensaje de bienvenida
        """
        welcome_message = self._sanitize_user_response(
            "¡Hola! Soy Hernando, tu anfitrión en el Fundo Moraga. ¿En qué puedo ayudarte?"
        )
        
        # Crear nueva conversación
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        self.conversation_store.save_message(
            user_id=user_id,
            role="assistant",
            message=welcome_message,
            conversation_id=conversation_id,
            metadata={"platform": "instagram", "type": "welcome"}
        )
        
        return welcome_message


def main():
    """Función de ejemplo para probar el bot localmente"""
    config.validate_config()
    
    bot = InstagramBot()
    
    print(f"\n🤖 {config.BOT_NAME} iniciado")
    print("=" * 50)
    print("Modo de prueba - Simula conversaciones")
    print("Escribe 'salir' para terminar\n")
    
    # Usuario de prueba
    test_user_id = "test_user_12345"
    
    # Mensaje de bienvenida
    welcome = bot.start_conversation(test_user_id)
    print(f"Bot: {welcome}\n")
    
    # Loop de conversación
    while True:
        user_input = input("Tú: ").strip()
        
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n👋 ¡Hasta luego!")
            break
        
        if not user_input:
            continue
        
        response = bot.process_message(test_user_id, user_input)
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()
