"""
Bot principal de Instagram para Fundo Moraga
Integra Cosmos DB para memoria y OpenAI para respuestas
"""
import requests
from typing import Dict, Optional
from datetime import datetime
import config
from cosmos_client import get_conversation_store
from openai_client import get_chatbot_ai
from resend_client import get_resend_client
import json
import re


class InstagramBot:
    """Chatbot de Instagram con memoria en Cosmos DB"""
    
    def __init__(self):
        """Inicializa el bot"""
        self.conversation_store = get_conversation_store()
        self.chatbot_ai = get_chatbot_ai()
        self.resend_client = get_resend_client()
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

            # 4. Flujo determinístico de agendamiento (no depende del modelo)
            booking_response = self._handle_booking_flow(
                user_id=user_id,
                conversation_id=conversation_id,
                message_text=message_text,
                conversation_history=conversation_history,
                platform="Web",
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
            
            # 5. Generar respuesta con OpenAI usando el contexto
            response_text = self.chatbot_ai.generate_response(
                user_message=message_text,
                conversation_history=conversation_history
            )
            
            # 6. Guardar respuesta del asistente en Cosmos DB
            self.conversation_store.save_message(
                user_id=user_id,
                role="assistant",
                message=response_text,
                conversation_id=conversation_id,
                metadata={"platform": "web", "model": config.OPENAI_MODEL}
            )
            
            # 7. Detectar si se capturó información del usuario y enviar email
            if "he registrado tu consulta" in response_text.lower() or "información capturada" in response_text.lower():
                self._send_lead_email(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history,
                    latest_message=message_text,
                    platform="Web"
                )
            
            print(f"📤 Respuesta: {response_text}")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente."

    # ============= BOOKING FLOW (WEB) =============

    def _handle_booking_flow(
        self,
        user_id: str,
        conversation_id: str,
        message_text: str,
        conversation_history: list,
        platform: str,
    ) -> Optional[str]:
        """
        Maneja un flujo simple de agendamiento:
        1) Pregunta día de visita
        2) Si el usuario dice viernes (o un día), solicita datos
        3) Compila y envía por Resend a contacto@fundomoraga.com
        """
        state = self._get_booking_state(conversation_history, conversation_id) or {}
        stage = state.get("stage")

        if stage == "awaiting_day":
            visit_day = self._parse_visit_day(message_text)
            if not visit_day:
                return "¡Perfecto! ¿Qué día te gustaría venir para agendarlo? (por ejemplo: viernes, sábado, domingo o una fecha)."

            state = {"stage": "collecting_details", "visit_day": visit_day, "details": {}}
            self._save_booking_state(user_id, conversation_id, state)
            return self._booking_details_prompt(visit_day)

        if stage == "collecting_details":
            visit_day = state.get("visit_day") or "por confirmar"
            details = state.get("details") or {}
            details.update(self._parse_booking_details(message_text))
            state["details"] = details

            missing = [k for k in ("full_name", "phone", "email", "vehicles") if not details.get(k)]
            if missing:
                self._save_booking_state(user_id, conversation_id, state)
                return self._booking_missing_prompt(visit_day, missing)

            send_result = self.resend_client.send_booking_request(
                visit_day=visit_day,
                full_name=details["full_name"],
                phone=details["phone"],
                email=details["email"],
                vehicles=details["vehicles"],
                conversation_id=conversation_id,
                platform=platform,
            )

            state["stage"] = "sent" if send_result.get("success") else "error"
            state["sent_at"] = datetime.now().isoformat()
            self._save_booking_state(user_id, conversation_id, state)

            if send_result.get("success"):
                return (
                    f"¡Listo! Ya dejé tu solicitud para **{visit_day}** y la envié a nuestro equipo en "
                    f"`contacto@fundomoraga.com`. En breve te contactarán para confirmar."
                )

            return (
                "Pude registrar tus datos, pero tuve un problema al enviar el correo. "
                "¿Me confirmas tu email y teléfono nuevamente, por favor?"
            )

        if stage in ("sent", "error"):
            return None

        # Iniciar flujo si detectamos intención de agendar/reservar
        if self._is_booking_intent(message_text):
            visit_day = self._parse_visit_day(message_text)
            if visit_day:
                state = {"stage": "collecting_details", "visit_day": visit_day, "details": {}}
                self._save_booking_state(user_id, conversation_id, state)
                return self._booking_details_prompt(visit_day)

            state = {"stage": "awaiting_day"}
            self._save_booking_state(user_id, conversation_id, state)
            return "¡Buenísimo! ¿Qué día te gustaría venir para agendarlo? (por ejemplo: viernes, sábado, domingo o una fecha)."

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
        return any(k in t for k in keywords)

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

    def _parse_booking_details(self, text: str) -> Dict[str, str]:
        raw = (text or "").strip()
        if not raw:
            return {}

        details: Dict[str, str] = {}

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
            elif k in ("vehículos", "vehiculos", "vehiculo", "vehículo", "autos", "motos"):
                details["vehicles"] = v

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

        return details

    def _booking_details_prompt(self, visit_day: str) -> str:
        return (
            f"¡Perfecto! Para agendar **{visit_day}**, ¿me compartes estos datos en un solo mensaje?\n"
            "• Nombres y apellidos\n"
            "• Teléfono\n"
            "• Email\n"
            "• Número y tipo de vehículos (ej: 2 autos 4x4 + 1 moto)\n\n"
            "Si quieres, responde en este formato:\n"
            "Nombre y apellidos: ...\n"
            "Teléfono: ...\n"
            "Email: ...\n"
            "Vehículos: ..."
        )

    def _booking_missing_prompt(self, visit_day: str, missing: list) -> str:
        labels = {
            "full_name": "nombres y apellidos",
            "phone": "teléfono",
            "email": "email",
            "vehicles": "número y tipo de vehículos",
        }
        missing_text = ", ".join(labels[m] for m in missing if m in labels)
        return (
            f"¡Gracias! Para dejarlo agendado para **{visit_day}** me falta: {missing_text}.\n"
            "¿Me lo compartes, por favor?"
        )
    
    def _send_lead_email(
        self,
        user_id: str,
        conversation_id: str,
        conversation_history: list,
        latest_message: str,
        platform: str
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
            # Extraer información del historial
            nombre = "No proporcionado"
            interes = ""
            contacto = "No proporcionado"
            
            # Construir el interés a partir de los mensajes del usuario
            mensajes_usuario = []
            for msg in conversation_history:
                if msg.get("role") == "user":
                    mensajes_usuario.append(msg.get("message", ""))
            
            # Agregar el mensaje actual
            mensajes_usuario.append(latest_message)
            
            # El interés es un resumen de lo que el usuario ha consultado
            interes = " | ".join(mensajes_usuario[-5:])  # Últimos 5 mensajes del usuario
            
            # Intentar extraer nombre y contacto de los mensajes
            for msg_content in mensajes_usuario:
                msg_lower = msg_content.lower()
                
                # Detectar nombre si menciona "soy", "me llamo", etc.
                if any(phrase in msg_lower for phrase in ["soy ", "me llamo ", "mi nombre es "]):
                    # Extraer lo que viene después
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
                    # Buscar secuencias de números (simplificado)
                    import re
                    phones = re.findall(r'[\+\d][\d\s\-\(\)]{7,}', msg_content)
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
