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
            
            # 4. Generar respuesta con OpenAI usando el contexto
            response_text = self.chatbot_ai.generate_response(
                user_message=message_text,
                conversation_history=conversation_history
            )
            
            # 5. Guardar respuesta del asistente en Cosmos DB
            self.conversation_store.save_message(
                user_id=user_id,
                role="assistant",
                message=response_text,
                conversation_id=conversation_id,
                metadata={"platform": "web", "model": config.OPENAI_MODEL}
            )
            
            # 6. Detectar si se capturó información del usuario y enviar email
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
