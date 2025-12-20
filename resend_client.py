"""
Cliente de email (SMTP o Resend) para envío de mensajes.
Maneja el envío de resúmenes de conversación y reservas.
"""

import os
import re
import smtplib
from dotenv import load_dotenv
try:
    import resend
except Exception:
    resend = None
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from datetime import datetime
from typing import Dict, Optional

# Cargar variables de entorno
load_dotenv()

class ResendClient:
    """Cliente singleton para gestionar envíos de email (SMTP o Resend)"""
    
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
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in (
            "1",
            "true",
            "yes",
            "y",
            "si",
        )
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "").lower() in (
            "1",
            "true",
            "yes",
            "y",
            "si",
        )
        if self.smtp_port == 465 and not os.getenv("SMTP_USE_SSL"):
            self.smtp_use_ssl = True

        self.from_email = (
            os.getenv("SMTP_FROM_EMAIL")
            or os.getenv("RESEND_FROM_EMAIL")
            or self.smtp_user
            or "hernando@fundomoraga.com"
        )
        self.to_email = os.getenv('RESEND_TO_EMAIL', 'contacto@fundomoraga.com')
        self.to_emails = self._parse_to_emails()
        self.use_smtp = bool(self.smtp_user and self.smtp_password)

        # Resend es opcional en deploy: si falta la API key, el bot debe poder arrancar
        # y solo fallar al intentar enviar correos.
        if self.api_key and resend is not None:
            resend.api_key = self.api_key
        self._initialized = True

    def is_configured(self) -> bool:
        return bool(self.use_smtp or self.api_key)

    def _send_email(self, *, to: list[str], subject: str, html: str) -> Dict:
        if self.use_smtp:
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = self.from_email
                msg["To"] = ", ".join(to)
                msg["Subject"] = subject
                msg.attach(MIMEText(html, "html", "utf-8"))

                if self.smtp_use_ssl:
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
                else:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                with server:
                    if self.smtp_use_tls and not self.smtp_use_ssl:
                        server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, to, msg.as_string())

                return {"success": True, "provider": "smtp", "timestamp": datetime.now().isoformat()}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if not self.api_key or resend is None:
            return {"success": False, "error": "Email no configurado (SMTP/Resend)"}

        params = {"from": self.from_email, "to": to, "subject": subject, "html": html}
        response = resend.Emails.send(params)
        return {
            "success": True,
            "provider": "resend",
            "message_id": response.get("id"),
            "timestamp": datetime.now().isoformat(),
        }

    def _parse_to_emails(self) -> list[str]:
        raw = os.getenv("RESEND_TO_EMAILS", "").strip()
        # Defaults requeridos por negocio
        emails: list[str] = [
            "contacto@fundomoraga.com",
            "efrainmoraga@outlook.com",
            "pierinabertoni@gmail.com",
        ]

        if raw:
            for part in re.split(r"[;,]", raw):
                addr = part.strip()
                if addr:
                    emails.append(addr)

        # Backward compatible
        if self.to_email:
            emails.append(self.to_email)

        # De-dup preservando orden
        seen = set()
        unique: list[str] = []
        for e in emails:
            key = e.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)
        return unique
    
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
            if not self.is_configured():
                return {"success": False, "error": "Email no configurado (SMTP/Resend)"}

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
            
            return self._send_email(
                to=self.to_emails,
                subject=subject,
                html=html_content,
            )
            
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
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
            if not self.is_configured():
                return {"success": False, "error": "Email no configurado (SMTP/Resend)"}

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

            return self._send_email(
                to=self.to_emails,
                subject=subject,
                html=html_content,
            )
        except Exception as e:
            print(f"Error enviando solicitud de agendamiento: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_booking_confirmation_to_user(
        self,
        *,
        to_email: str,
        full_name: str,
        visit_date: str,
        visit_day: str,
        arrival_time: str,
        cars_count: int,
        motos_count: int,
        people_count: int,
        price_clp: int,
    ) -> Dict:
        """
        Envía confirmación de reserva al usuario final.
        """
        try:
            if not self.is_configured():
                return {"success": False, "error": "Email no configurado (SMTP/Resend)"}
            if not to_email:
                return {"success": False, "error": "Email de usuario no proporcionado"}

            name_txt = escape(full_name or "Cliente")
            date_txt = escape(visit_date or "por confirmar")
            day_txt = escape(visit_day or "")
            arrival_txt = escape(arrival_time or "por confirmar")
            price_txt = f"${int(price_clp):,} CLP".replace(",", ".") if price_clp else "por confirmar"

            subject = f"Reserva confirmada - Batuco Off Road ({day_txt} {date_txt})".strip()

            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .section {{ margin-bottom: 18px; padding: 14px; background-color: #f5f5f5; border-left: 4px solid #2c5530; }}
                    .label {{ font-weight: bold; color: #2c5530; }}
                    .footer {{ margin-top: 24px; padding: 12px; background-color: #f0f0f0; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>✅ Reserva confirmada</h1>
                </div>
                <div class="content">
                    <p>Hola {name_txt}, ya verificamos tu transferencia. Tu reserva quedó confirmada.</p>
                    <div class="section">
                        <p><span class="label">📅 Fecha:</span> {day_txt} {date_txt}</p>
                        <p><span class="label">🕘 Hora de llegada:</span> {arrival_txt}</p>
                        <p><span class="label">🚗 Autos:</span> {cars_count} | <span class="label">🏍️ Motos:</span> {motos_count}</p>
                        <p><span class="label">👥 Personas:</span> {people_count}</p>
                        <p><span class="label">💵 Tarifa:</span> {escape(price_txt)}</p>
                    </div>
                    <p>Un día antes te enviaremos un recordatorio por este mismo correo.</p>
                    <p>Si necesitas cambios, contáctanos en contacto@fundomoraga.com o WhatsApp +5694 1242609.</p>
                </div>
                <div class="footer">
                    <p>Mensaje automático de Hernando - Fundo Moraga</p>
                </div>
            </body>
            </html>
            """

            return self._send_email(
                to=[to_email],
                subject=subject,
                html=html_content,
            )
        except Exception as e:
            print(f"Error enviando confirmación al usuario: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_booking_reminder_to_user(
        self,
        *,
        to_email: str,
        full_name: str,
        visit_date: str,
        visit_day: str,
        arrival_time: str,
        cars_count: int,
        motos_count: int,
        people_count: int,
        price_clp: int,
    ) -> Dict:
        """
        Envía recordatorio de reserva (1 día antes).
        """
        try:
            if not self.is_configured():
                return {"success": False, "error": "Email no configurado (SMTP/Resend)"}
            if not to_email:
                return {"success": False, "error": "Email de usuario no proporcionado"}

            name_txt = escape(full_name or "Cliente")
            date_txt = escape(visit_date or "por confirmar")
            day_txt = escape(visit_day or "")
            arrival_txt = escape(arrival_time or "por confirmar")
            price_txt = f"${int(price_clp):,} CLP".replace(",", ".") if price_clp else "por confirmar"

            subject = f"Recordatorio de tu reserva - {day_txt} {date_txt}".strip()

            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .section {{ margin-bottom: 18px; padding: 14px; background-color: #f5f5f5; border-left: 4px solid #2c5530; }}
                    .label {{ font-weight: bold; color: #2c5530; }}
                    .footer {{ margin-top: 24px; padding: 12px; background-color: #f0f0f0; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>⏰ Recordatorio de reserva</h1>
                </div>
                <div class="content">
                    <p>Hola {name_txt}, te recordamos tu reserva en Batuco Off Road para mañana.</p>
                    <div class="section">
                        <p><span class="label">📅 Fecha:</span> {day_txt} {date_txt}</p>
                        <p><span class="label">🕘 Hora de llegada:</span> {arrival_txt}</p>
                        <p><span class="label">🚗 Autos:</span> {cars_count} | <span class="label">🏍️ Motos:</span> {motos_count}</p>
                        <p><span class="label">👥 Personas:</span> {people_count}</p>
                        <p><span class="label">💵 Tarifa:</span> {escape(price_txt)}</p>
                    </div>
                    <p>Si necesitas cambiar algo, contáctanos en contacto@fundomoraga.com o WhatsApp +5694 1242609.</p>
                </div>
                <div class="footer">
                    <p>Mensaje automático de Hernando - Fundo Moraga</p>
                </div>
            </body>
            </html>
            """

            return self._send_email(
                to=[to_email],
                subject=subject,
                html=html_content,
            )
        except Exception as e:
            print(f"Error enviando recordatorio al usuario: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_error_notification(self, error_message: str, conversation_id: str):
        """
        Envía una notificación de error al equipo técnico
        
        Args:
            error_message: Descripción del error
            conversation_id: ID de la conversación donde ocurrió el error
        """
        try:
            if not self.is_configured():
                return

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
            
            self._send_email(
                to=self.to_emails,
                subject=subject,
                html=html_content,
            )
            
        except Exception as e:
            print(f"Error enviando notificación de error: {str(e)}")

    def send_conversation_end_summary(
        self,
        *,
        subject: str,
        summary_text: str,
        conversation_id: str,
        user_id: str,
        platform: str = "Web",
    ) -> Dict:
        """
        Envía un resumen final de la conversación (para seguimiento interno).
        """
        try:
            if not self.is_configured():
                return {"success": False, "error": "Email no configurado (SMTP/Resend)"}

            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .section {{ margin-bottom: 20px; padding: 15px; background-color: #f5f5f5; border-left: 4px solid #2c5530; white-space: pre-wrap; }}
                    .label {{ font-weight: bold; color: #2c5530; }}
                    .footer {{ margin-top: 30px; padding: 15px; background-color: #f0f0f0; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🧾 Resumen de conversación - Hernando</h1>
                </div>
                <div class="content">
                    <div class="section">
                        <p><span class="label">🔗 Plataforma:</span> {platform}</p>
                        <p><span class="label">🆔 Conversación:</span> {conversation_id}</p>
                        <p><span class="label">👤 User ID:</span> {user_id}</p>
                        <p><span class="label">📅 Fecha:</span> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                    <div class="section">{summary_text}</div>
                </div>
                <div class="footer">
                    <p>Mensaje generado automáticamente por Hernando.</p>
                </div>
            </body>
            </html>
            """

            return self._send_email(
                to=self.to_emails,
                subject=subject,
                html=html_content,
            )
        except Exception as e:
            print(f"Error enviando resumen final: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_contact_sheet(
        self,
        *,
        user_name: str,
        user_contact: str,
        user_interest: str,
        conversation_id: str,
        platform: str = "Web",
        booking_details: Optional[Dict] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        """
        Envía ficha de contacto al equipo (formato Fundo Moraga).
        """
        try:
            if not self.is_configured():
                return {"success": False, "error": "Email no configurado (SMTP/Resend)"}

            name_txt = escape(user_name or "No identificado")
            contact_txt = escape(user_contact or "No identificado")
            interest_txt = escape(user_interest or "No identificado")
            notes_txt = escape(notes or "").strip()

            booking_html = ""
            if booking_details:
                visit_day = escape(str(booking_details.get("visit_day") or "N/A"))
                visit_date = escape(str(booking_details.get("visit_date") or ""))
                arrival = escape(str(booking_details.get("arrival_time") or "N/A"))
                cars = escape(str(booking_details.get("cars_count") if booking_details.get("cars_count") is not None else "N/A"))
                motos = escape(str(booking_details.get("motos_count") if booking_details.get("motos_count") is not None else "N/A"))
                people = escape(str(booking_details.get("people_count") if booking_details.get("people_count") is not None else "N/A"))
                price = booking_details.get("price_clp")
                if price is not None:
                    try:
                        price_txt = f"${int(price):,} CLP".replace(",", ".")
                    except Exception:
                        price_txt = str(price)
                else:
                    price_txt = "N/A"

                booking_html = f"""
                <div class="section">
                    <p><span class="label">📅 Reserva:</span></p>
                    <p>Día/fecha: {visit_day} {visit_date}</p>
                    <p>Hora llegada: {arrival}</p>
                    <p>Autos: {cars} | Motos: {motos} | Personas: {people}</p>
                    <p>Tarifa: {escape(price_txt)}</p>
                </div>
                """

            notes_html = ""
            if notes_txt:
                notes_html = f"""
                <div class="section" style="white-space: pre-wrap;">
                    <p><span class="label">📝 Notas:</span></p>
                    {notes_txt}
                </div>
                """

            subject = f"Ficha de contacto - {name_txt}"
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
                    <h1>🌿 Ficha de Contacto - Fundo Moraga</h1>
                </div>
                <div class="content">
                    <div class="section">
                        <p><span class="label">👤 Nombre:</span> {name_txt}</p>
                        <p><span class="label">📞 Contacto:</span> {contact_txt}</p>
                        <p><span class="label">🎯 Interés:</span> {interest_txt}</p>
                        <p><span class="label">🔗 Plataforma:</span> {escape(platform)}</p>
                        <p><span class="label">🆔 ID Conversación:</span> {escape(conversation_id)}</p>
                        <p><span class="label">📅 Fecha:</span> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                    {booking_html}
                    {notes_html}
                </div>
                <div class="footer">
                    <p>Mensaje generado automáticamente por Hernando.</p>
                </div>
            </body>
            </html>
            """

            return self._send_email(
                to=self.to_emails,
                subject=subject,
                html=html_content,
            )
        except Exception as e:
            print(f"Error enviando ficha de contacto: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
_resend_client_instance = None

def get_resend_client() -> ResendClient:
    """Obtiene la instancia singleton del cliente de email"""
    global _resend_client_instance
    if _resend_client_instance is None:
        _resend_client_instance = ResendClient()
    return _resend_client_instance
