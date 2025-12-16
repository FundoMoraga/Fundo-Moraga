"""
Cliente de Resend para envío de emails
Maneja el envío de resúmenes de conversación al equipo de ventas
"""

import os
from dotenv import load_dotenv
import resend
from datetime import datetime
from typing import Dict, Optional

# Cargar variables de entorno
load_dotenv()

class ResendClient:
    """Cliente singleton para gestionar envíos de email con Resend"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResendClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'hernando@fundomoraga.com')
        self.to_email = os.getenv('RESEND_TO_EMAIL', 'contacto@fundomoraga.com')
        
        if not self.api_key:
            raise ValueError("RESEND_API_KEY no está configurada en las variables de entorno")
        
        # Configurar Resend
        resend.api_key = self.api_key
        self._initialized = True
    
    def send_conversation_summary(
        self,
        user_name: str,
        user_interest: str,
        user_contact: str,
        conversation_id: str,
        platform: str = "Instagram"
    ) -> Dict:
        """
        Envía un resumen de conversación al equipo de ventas
        
        Args:
            user_name: Nombre del usuario extraído naturalmente
            user_interest: Qué quería el usuario (con detalles)
            user_contact: Contacto del usuario (móvil/correo)
            conversation_id: ID de la conversación en Cosmos DB
            platform: Plataforma origen (Instagram/Web)
        
        Returns:
            Dict con resultado del envío
        """
        try:
            # Construir el email
            subject = f"Nuevo Lead de {platform} - {user_name}"
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .section {{ margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-left: 4px solid #2c5530; }}
                    .label {{ font-weight: bold; color: #2c5530; }}
                    .footer {{ margin-top: 30px; padding: 15px; background-color: #f0f0f0; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🌿 Nuevo Lead - Fundo Moraga</h1>
                </div>
                <div class="content">
                    <p>Hernando ha tenido una conversación con un potencial cliente. Aquí está el resumen:</p>
                    
                    <div class="section">
                        <p><span class="label">👤 Nombre:</span> {user_name}</p>
                    </div>
                    
                    <div class="section">
                        <p><span class="label">📝 Interés/Consulta:</span></p>
                        <p>{user_interest}</p>
                    </div>
                    
                    <div class="section">
                        <p><span class="label">📞 Contacto:</span> {user_contact}</p>
                    </div>
                    
                    <div class="section">
                        <p><span class="label">🔗 Plataforma:</span> {platform}</p>
                        <p><span class="label">🆔 ID Conversación:</span> {conversation_id}</p>
                        <p><span class="label">📅 Fecha:</span> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Este mensaje fue generado automáticamente por Hernando, el asistente virtual de Fundo Moraga.</p>
                    <p>Para ver la conversación completa, revisa el registro en Cosmos DB con el ID proporcionado.</p>
                </div>
            </body>
            </html>
            """
            
            # Enviar email
            params = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            
            return {
                "success": True,
                "message_id": response.get('id'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error enviando email con Resend: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def send_booking_request(
        self,
        visit_date: str,
        visit_day: str,
        full_name: str,
        phone: str,
        email: str,
        cars_count: int,
        motos_count: int,
        people_count: int,
        price_clp: int,
        conversation_id: str,
        platform: str = "Web",
        additional_notes: Optional[str] = None,
    ) -> Dict:
        """
        Envía una solicitud de agendamiento/reserva al equipo de Fundo Moraga.
        """
        try:
            subject = f"Solicitud de agendamiento ({visit_day} {visit_date}) - {full_name}"
            price_formatted = f"{int(price_clp):,}".replace(",", ".")

            notes_html = ""
            if additional_notes:
                notes_html = f"""
                <div class="section">
                    <p><span class="label">🗒️ Notas:</span></p>
                    <p>{additional_notes}</p>
                </div>
                """

            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .section {{ margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-left: 4px solid #2c5530; }}
                    .label {{ font-weight: bold; color: #2c5530; }}
                    .footer {{ margin-top: 30px; padding: 15px; background-color: #f0f0f0; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📅 Solicitud de Agendamiento - Fundo Moraga</h1>
                </div>
                <div class="content">
                    <div class="section">
                        <p><span class="label">🗓️ Día solicitado:</span> {visit_day} ({visit_date})</p>
                        <p><span class="label">🕘 Horario:</span> 09:00 - 17:00</p>
                        <p><span class="label">👤 Nombres y apellidos:</span> {full_name}</p>
                        <p><span class="label">📞 Teléfono:</span> {phone}</p>
                        <p><span class="label">✉️ Email:</span> {email}</p>
                        <p><span class="label">👥 Personas:</span> {people_count}</p>
                        <p><span class="label">🚗 Automóviles:</span> {cars_count}</p>
                        <p><span class="label">🏍️ Motos:</span> {motos_count}</p>
                        <p><span class="label">💵 Tarifa:</span> ${price_formatted} CLP</p>
                    </div>

                    {notes_html}

                    <div class="section">
                        <p><span class="label">🔗 Plataforma:</span> {platform}</p>
                        <p><span class="label">🆔 ID Conversación:</span> {conversation_id}</p>
                        <p><span class="label">📅 Fecha:</span> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Este mensaje fue generado automáticamente por Hernando.</p>
                </div>
            </body>
            </html>
            """

            params = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_content,
            }

            response = resend.Emails.send(params)

            return {
                "success": True,
                "message_id": response.get("id"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error enviando solicitud de agendamiento con Resend: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_error_notification(self, error_message: str, conversation_id: str):
        """
        Envía una notificación de error al equipo técnico
        
        Args:
            error_message: Descripción del error
            conversation_id: ID de la conversación donde ocurrió el error
        """
        try:
            subject = f"⚠️ Error en Hernando - {conversation_id}"
            
            html_content = f"""
            <html>
            <body>
                <h2>Error en el Sistema</h2>
                <p><strong>Conversación ID:</strong> {conversation_id}</p>
                <p><strong>Error:</strong> {error_message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_content,
            }
            
            resend.Emails.send(params)
            
        except Exception as e:
            print(f"Error enviando notificación de error: {str(e)}")


# Singleton instance
_resend_client_instance = None

def get_resend_client() -> ResendClient:
    """Obtiene la instancia singleton del cliente de Resend"""
    global _resend_client_instance
    if _resend_client_instance is None:
        _resend_client_instance = ResendClient()
    return _resend_client_instance
