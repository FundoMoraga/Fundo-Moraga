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
        # self.access_token = config.INSTAGRAM_ACCESS_TOKEN
        # self.page_id = config.INSTAGRAM_PAGE_ID
    
    def process_message(self, user_id: str, message_text: str) -> str:
        """
        Procesa un mensaje entrante del usuario
        
        Args:
            user_id: ID del usuario de Instagram
            message_text: Texto del mensaje
        
        Returns:
            Respuesta generada para el usuario
        """
        try:
            print(f"📥 Mensaje de {user_id}: {message_text}")
            
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
                metadata={"platform": "web", "source": "widget"}
            )
            
            # 3. Recuperar historial de conversación
            conversation_history = self.conversation_store.get_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=config.MAX_CONVERSATION_HISTORY
            )

            platform = "Web"

            # 4. Flujo determinístico de agendamiento (no depende del modelo)
            booking_response = self._handle_booking_flow(
                user_id=user_id,
                conversation_id=conversation_id,
                message_text=message_text,
                conversation_history=conversation_history,
                platform=platform,
            )
            if booking_response:
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message=booking_response,
                    conversation_id=conversation_id,
                    metadata={"platform": "web", "source": "booking_flow"},
                )
                return booking_response

            # 4.5 Respuesta determinística para tarifas públicas (evita respuestas genéricas del modelo)
            pricing_response = self._handle_public_pricing(message_text)
            if pricing_response:
                self.conversation_store.save_message(
                    user_id=user_id,
                    role="assistant",
                    message=pricing_response,
                    conversation_id=conversation_id,
                    metadata={"platform": "web", "source": "pricing_flow"},
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
                return_events=True,
            )

            response_text = ai_result.get("text") if isinstance(ai_result, dict) else ai_result
            events = ai_result.get("events", []) if isinstance(ai_result, dict) else []
            
            # 6. Guardar respuesta del asistente en Cosmos DB
            self.conversation_store.save_message(
                user_id=user_id,
                role="assistant",
                message=response_text,
                conversation_id=conversation_id,
                metadata={"platform": "web", "model": config.OPENAI_MODEL}
            )

            # 7. Si el modelo ejecutó herramientas de captura/formulario, enviar email y marcar conversación
            if events:
                self._handle_post_ai_events(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    latest_message=message_text,
                    platform=platform,
                    events=events,
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

    def _handle_post_ai_events(
        self,
        user_id: str,
        conversation_id: str,
        conversation_history: list,
        latest_message: str,
        platform: str,
        events: list,
    ) -> None:
        lead_capture_already_sent = any(
            (msg.get("metadata") or {}).get("type") == "lead_capture" for msg in (conversation_history or [])
        )

        if lead_capture_already_sent:
            return

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
                    metadata={"platform": "web", "type": "lead_capture", "source": "tool", "args": args},
                )
                return

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
                    metadata={"platform": "web", "type": "lead_capture", "source": "tool_form", "args": args},
                )
                return

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

        greeting = "¡Hola! Soy Hernando, tu anfitrión en el Fundo Moraga. ¿En qué puedo ayudarte?"

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
                    self._save_booking_state(user_id, conversation_id, state)
                    return (
                        "Se cumplió el plazo de 10 minutos sin confirmación de transferencia, así que cierro esta solicitud. "
                        "Si quieres intentarlo de nuevo, escríbeme nuevamente. [[CLOSE_CHAT]]"
                    )
            except Exception:
                pass

        if stage == "awaiting_day":
            visit_date = self._parse_visit_date(message_text)
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
                    suggested = self._next_weekday_date(visit_day_hint)
                    suggested_txt = suggested.isoformat() if suggested else "YYYY-MM-DD"
                    # Guardar sugerencia para que un "sí" posterior la confirme
                    state["suggested_date"] = suggested.isoformat() if suggested else None
                    state["suggested_day"] = visit_day_hint
                    self._save_booking_state(user_id, conversation_id, state)

                    # Si el usuario ya dio hora en el mismo mensaje, avanzamos al siguiente paso.
                    arrival_time = self._parse_arrival_time(message_text)
                    if arrival_time and suggested:
                        state = {
                            "stage": "collecting_details",
                            "visit_date": suggested.isoformat(),
                            "visit_day": visit_day_hint,
                            "details": {"arrival_time": arrival_time},
                        }
                        self._save_booking_state(user_id, conversation_id, state)
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
                self._save_booking_state(user_id, conversation_id, state)
                return "Los domingos no estamos agendando. ¿Te acomoda lunes a sábado? [[CLOSE_CHAT]]"

            arrival_time = self._parse_arrival_time(message_text)
            details = {"arrival_time": arrival_time} if arrival_time else {}

            state = {
                "stage": "collecting_details",
                "visit_date": visit_date.isoformat(),
                "visit_day": visit_day,
                "details": details,
            }
            self._save_booking_state(user_id, conversation_id, state)
            return self._booking_details_prompt(visit_day, visit_date, arrival_time=arrival_time)

        if stage == "collecting_details":
            visit_day = state.get("visit_day") or "por confirmar"
            visit_date = self._safe_date_from_iso(state.get("visit_date"))
            details = state.get("details") or {}
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
                self._save_booking_state(user_id, conversation_id, state)
                return self._booking_missing_prompt(visit_day, missing, details=details)

            cars_count = int(details.get("cars_count") or 0)
            motos_count = int(details.get("motos_count") or 0)
            price_clp = self._calculate_price(visit_day, cars_count, motos_count)
            state["price_clp"] = price_clp
            state["stage"] = "confirm_transfer"
            self._save_booking_state(user_id, conversation_id, state)

            return self._transfer_prompt(visit_day, visit_date, price_clp, details)

        if stage == "confirm_transfer":
            t = (message_text or "").strip().lower()
            if any(x in t for x in ("sí", "si", "dale", "ok", "haré", "hare", "voy a", "ya")):
                now = datetime.now(timezone.utc)
                state["stage"] = "awaiting_transfer"
                state["transfer_started_at"] = now.isoformat().replace("+00:00", "Z")
                state["transfer_deadline"] = (now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
                self._save_booking_state(user_id, conversation_id, state)
                return "Perfecto. Avísame cuando la hayas completado (por ejemplo: “listo, transferí”) y reviso el correo del banco."

            if any(x in t for x in ("no", "nop", "después", "despues")):
                state["stage"] = "closed"
                self._save_booking_state(user_id, conversation_id, state)
                return "Entendido. La reserva solo queda válida con transferencia, así que cierro esta solicitud. [[CLOSE_CHAT]]"

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
                self._save_booking_state(user_id, conversation_id, state)

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
                    self._save_booking_state(user_id, conversation_id, state)
                    return "Los domingos no estamos agendando. ¿Te acomoda lunes a sábado? [[CLOSE_CHAT]]"

                arrival_time = self._parse_arrival_time(message_text)
                details = {"arrival_time": arrival_time} if arrival_time else {}
                state = {
                    "stage": "collecting_details",
                    "visit_date": visit_date.isoformat(),
                    "visit_day": visit_day,
                    "details": details,
                }
                self._save_booking_state(user_id, conversation_id, state)
                return self._booking_details_prompt(visit_day, visit_date, arrival_time=arrival_time)

            # Si el usuario dijo un día de la semana, proponemos la próxima fecha.
            visit_day_hint = self._parse_weekday_name_es(message_text)
            if visit_day_hint:
                suggested = self._next_weekday_date(visit_day_hint)
                state = {"stage": "awaiting_day"}
                self._save_booking_state(user_id, conversation_id, state)
                suggested_txt = suggested.isoformat() if suggested else "YYYY-MM-DD"
                return (
                    f"¡Buenísimo! ¿Te acomoda este **{visit_day_hint}** ({suggested_txt}) u otra fecha? "
                    "Y para coordinar, ¿a qué hora te gustaría llegar? (09:00–17:00)"
                )

            state = {"stage": "awaiting_day"}
            self._save_booking_state(user_id, conversation_id, state)
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

    def _save_booking_state(self, user_id: str, conversation_id: str, state: Dict) -> None:
        self.conversation_store.save_message(
            user_id=user_id,
            role="assistant",
            message="",
            conversation_id=conversation_id,
            metadata={"platform": "web", "type": "booking_state", "state": state},
        )

    def _is_booking_intent(self, text: str) -> bool:
        t = (text or "").lower()
        keywords = [
            "agendar",
            "agenda",
            "reservar",
            "reserva",
            "agend",
            "quiero ir",
            "quiero venir",
            "ir el ",
            "venir el ",
            "viernes",
            "sábado",
            "sabado",
            "domingo",
            "fin de semana",
        ]
        if any(k in t for k in keywords):
            return True

        # Si el usuario responde solo con una fecha, también lo interpretamos como intención de agendar.
        if re.search(r"\b\d{4}-\d{2}-\d{2}\b", t):
            return True
        if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", t):
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
        tz = ZoneInfo(config.GOOGLE_CALENDAR_TIMEZONE)
        today = datetime.now(tz).date()

        if "pasado mañana" in tl or "pasado manana" in tl:
            return today + timedelta(days=2)
        if "mañana" in tl or "manana" in tl:
            return today + timedelta(days=1)
        if "hoy" in tl:
            return today

        # "este viernes", "el viernes", etc.
        weekday_hint = self._parse_weekday_name_es(tl)
        if weekday_hint:
            return self._next_weekday_date(weekday_hint)

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
        raw = (text or "").lower()
        if not raw:
            return None

        m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", raw)
        if m:
            return f"{int(m.group(1)):02d}:{m.group(2)}"

        m = re.search(r"\b(?:a\s+las\s+)?([01]?\d|2[0-3])\s*(am|pm)?\b", raw)
        if not m:
            return None

        hour = int(m.group(1))
        mer = m.group(2)
        if mer == "pm" and hour < 12:
            hour += 12
        if mer == "am" and hour == 12:
            hour = 0
        if 0 <= hour <= 23:
            return f"{hour:02d}:00"
        return None

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

    def _next_weekday_date(self, weekday_es: str) -> Optional[date]:
        names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        if weekday_es not in names:
            return None
        target = names.index(weekday_es)
        tz = ZoneInfo(config.GOOGLE_CALENDAR_TIMEZONE)
        today = datetime.now(tz).date()
        days_ahead = (target - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

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
            # URL de la API de Instagram Messaging
            url = f"https://graph.facebook.com/v18.0/me/messages"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message_text},
                "access_token": self.access_token
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ Mensaje enviado a {recipient_id}")
                return True
            else:
                print(f"❌ Error enviando mensaje: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en send_instagram_message: {e}")
            return False
    
    def handle_webhook_message(self, webhook_data: Dict) -> None:
        """
        Maneja mensajes recibidos del webhook de Instagram
        
        Args:
            webhook_data: Datos recibidos del webhook
        """
        try:
            # Extraer información del webhook
            # Estructura de webhook de Instagram: 
            # https://developers.facebook.com/docs/messenger-platform/webhooks
            
            if "entry" not in webhook_data:
                return
            
            for entry in webhook_data["entry"]:
                if "messaging" not in entry:
                    continue
                
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event.get("sender", {}).get("id")
                    
                    # Verificar que es un mensaje de texto
                    if "message" in messaging_event:
                        message = messaging_event["message"]
                        
                        # Ignorar mensajes del propio bot
                        if message.get("is_echo"):
                            continue
                        
                        message_text = message.get("text", "")
                        
                        if sender_id and message_text:
                            # Procesar mensaje y obtener respuesta
                            response = self.process_message(sender_id, message_text)
                            
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
        welcome_message = (
            f"¡Hola! Soy el asistente virtual de {config.BOT_NAME}. "
            "Estoy aquí para ayudarte con información sobre nuestros productos, "
            "precios y pedidos. ¿En qué puedo ayudarte hoy? 🍒🍎"
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
