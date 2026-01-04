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

try:
    from base64_logos import LOGO_NEGRO, LOGO_BLANCO
except ImportError:
    LOGO_NEGRO = None
    LOGO_BLANCO = None
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
                    server.ehlo()
                    if self.smtp_use_tls and not self.smtp_use_ssl:
                        server.starttls()
                        server.ehlo()
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
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6; 
                        color: #1f2937;
                        background-color: #f9fafb;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{ 
                        background: #000000;
                        color: white; 
                        padding: 32px 24px;
                        text-align: center;
                    }}
                    .header h1 {{
                        font-size: 28px;
                        font-weight: 700;
                        margin: 0;
                        letter-spacing: -0.5px;
                    }}
                    .header .subtitle {{
                        font-size: 14px;
                        opacity: 0.9;
                        margin-top: 8px;
                    }}
                    .content {{ padding: 32px 24px; }}
                    .intro {{
                        font-size: 15px;
                        color: #4b5563;
                        margin-bottom: 28px;
                        padding-bottom: 20px;
                        border-bottom: 2px solid #f3f4f6;
                    }}
                    .card {{ 
                        margin-bottom: 16px; 
                        padding: 20px;
                        background: linear-gradient(to right, #f9fafb 0%, #ffffff 100%);
                        border-radius: 12px;
                        border-left: 4px solid #2c5530;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }}
                    .card-title {{
                        font-size: 13px;
                        font-weight: 600;
                        color: #6b7280;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 8px;
                    }}
                    .card-content {{
                        font-size: 16px;
                        font-weight: 500;
                        color: #1f2937;
                        line-height: 1.5;
                    }}
                    .info-grid {{
                        display: table;
                        width: 100%;
                        margin-top: 24px;
                    }}
                    .info-row {{
                        display: table-row;
                    }}
                    .info-label {{
                        display: table-cell;
                        font-size: 13px;
                        font-weight: 600;
                        color: #6b7280;
                        padding: 8px 0;
                        width: 40%;
                    }}
                    .info-value {{
                        display: table-cell;
                        font-size: 14px;
                        color: #1f2937;
                        padding: 8px 0;
                    }}
                    .footer {{ 
                        background-color: #f9fafb;
                        padding: 24px;
                        text-align: center;
                        border-top: 1px solid #e5e7eb;
                    }}
                    .footer-text {{
                        font-size: 13px;
                        color: #6b7280;
                        line-height: 1.6;
                    }}
                    .footer-brand {{
                        font-weight: 600;
                        color: #2c5530;
                    }}
                    .emoji {{ font-size: 20px; margin-right: 8px; }}
                    .logo {{ 
                        width: 240px;
                        height: auto;
                        margin: 0;
                    }}
                    .header h1, .header .subtitle {{ display: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        {'<img src="' + LOGO_BLANCO + '" alt="Fundo Moraga" class="logo">' if LOGO_BLANCO else ''}
                        <h1><span class="emoji">🌿</span> Nuevo Lead</h1>
                        <div class="subtitle">Fundo Moraga · {platform}</div>
                    </div>
                    
                    <div class="content">
                        <div class="intro">
                            Hernando ha conectado con un potencial cliente. Aquí está el resumen de la conversación:
                        </div>
                        
                        <div class="card">
                            <div class="card-title">👤 Cliente</div>
                            <div class="card-content">{escape(user_name)}</div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">📝 Interés / Consulta</div>
                            <div class="card-content">{escape(user_interest)}</div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">📞 Contacto</div>
                            <div class="card-content">{escape(user_contact)}</div>
                        </div>
                        
                        <div class="info-grid">
                            <div class="info-row">
                                <div class="info-label">Plataforma</div>
                                <div class="info-value">{platform}</div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">ID Conversación</div>
                                <div class="info-value"><code style="font-size: 12px; background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{conversation_id}</code></div>
                            </div>
                            <div class="info-row">
                                <div class="info-label">Fecha/Hora</div>
                                <div class="info-value">{datetime.now().strftime('%d/%m/%Y · %H:%M:%S')}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="footer-text">
                            Mensaje generado automáticamente por <span class="footer-brand">Hernando</span>,<br>
                            el asistente virtual de Fundo Moraga.
                        </div>
                    </div>
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
                <div class="card">
                    <div class="card-title">🗒️ Notas Adicionales</div>
                    <div class="card-content">{escape(additional_notes)}</div>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6; 
                        color: #1f2937;
                        background-color: #f9fafb;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{ 
                        background: #000000;
                        color: white; 
                        padding: 32px 24px;
                        text-align: center;
                    }}
                    .header h1 {{
                        font-size: 28px;
                        font-weight: 700;
                        margin: 0;
                        letter-spacing: -0.5px;
                    }}
                    .header .subtitle {{
                        font-size: 14px;
                        opacity: 0.9;
                        margin-top: 8px;
                    }}
                    .content {{ padding: 32px 24px; }}
                    .highlight-box {{
                        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 24px;
                        border: 2px solid #fbbf24;
                    }}
                    .highlight-date {{
                        font-size: 24px;
                        font-weight: 700;
                        color: #92400e;
                        margin-bottom: 4px;
                    }}
                    .highlight-time {{
                        font-size: 14px;
                        color: #78350f;
                    }}
                    .card {{ 
                        margin-bottom: 16px; 
                        padding: 20px;
                        background: linear-gradient(to right, #f9fafb 0%, #ffffff 100%);
                        border-radius: 12px;
                        border-left: 4px solid #dc2626;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }}
                    .card-title {{
                        font-size: 13px;
                        font-weight: 600;
                        color: #6b7280;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 8px;
                    }}
                    .card-content {{
                        font-size: 16px;
                        font-weight: 500;
                        color: #1f2937;
                        line-height: 1.5;
                    }}
                    .info-grid {{
                        display: table;
                        width: 100%;
                    }}
                    .info-row {{
                        display: table-row;
                    }}
                    .info-label {{
                        display: table-cell;
                        font-size: 14px;
                        font-weight: 600;
                        color: #6b7280;
                        padding: 10px 0;
                        width: 40%;
                    }}
                    .info-value {{
                        display: table-cell;
                        font-size: 15px;
                        color: #1f2937;
                        padding: 10px 0;
                        font-weight: 500;
                    }}
                    .price-box {{
                        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                        border-radius: 12px;
                        padding: 20px;
                        text-align: center;
                        margin: 24px 0;
                        border: 2px solid #10b981;
                    }}
                    .price-label {{
                        font-size: 13px;
                        color: #065f46;
                        font-weight: 600;
                        margin-bottom: 4px;
                    }}
                    .price-amount {{
                        font-size: 32px;
                        font-weight: 700;
                        color: #047857;
                    }}
                    .footer {{ 
                        background-color: #f9fafb;
                        padding: 24px;
                        text-align: center;
                        border-top: 1px solid #e5e7eb;
                    }}
                    .footer-text {{
                        font-size: 13px;
                        color: #6b7280;
                        line-height: 1.6;
                    }}
                    .footer-brand {{
                        font-weight: 600;
                        color: #dc2626;
                    }}
                    .emoji {{ font-size: 20px; margin-right: 8px; }}
                    .logo {{ 
                        width: 240px;
                        height: auto;
                        margin: 0;
                    }}
                    .header h1, .header .subtitle {{ display: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        {'<img src="' + LOGO_BLANCO + '" alt="Fundo Moraga" class="logo">' if LOGO_BLANCO else ''}
                        <h1><span class="emoji">📅</span> Nueva Reserva</h1>
                        <div class="subtitle">Solicitud de Agendamiento · Fundo Moraga</div>
                    </div>
                    
                    <div class="content">
                        <div class="highlight-box">
                            <div class="highlight-date">{visit_day}, {visit_date}</div>
                            <div class="highlight-time">🕘 Horario: 09:00 - 17:00</div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">👤 Información del Cliente</div>
                            <div class="info-grid">
                                <div class="info-row">
                                    <div class="info-label">Nombre</div>
                                    <div class="info-value">{escape(full_name)}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Teléfono</div>
                                    <div class="info-value">{escape(phone)}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Email</div>
                                    <div class="info-value">{escape(email)}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">🚗 Detalles de la Visita</div>
                            <div class="info-grid">
                                <div class="info-row">
                                    <div class="info-label">Personas</div>
                                    <div class="info-value">{people_count} personas</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Automóviles</div>
                                    <div class="info-value">{cars_count} autos</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Motos</div>
                                    <div class="info-value">{motos_count} motos</div>
                                </div>
                            </div>
                        </div>
                        
                        {notes_html}
                        
                        <div class="price-box">
                            <div class="price-label">TARIFA TOTAL</div>
                            <div class="price-amount">${price_formatted} CLP</div>
                        </div>
                        
                        <div class="card" style="border-left-color: #6b7280;">
                            <div class="card-title">📋 Información Técnica</div>
                            <div class="info-grid">
                                <div class="info-row">
                                    <div class="info-label">Plataforma</div>
                                    <div class="info-value">{platform}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">ID Conversación</div>
                                    <div class="info-value" style="font-size: 12px; font-family: monospace;">{conversation_id}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">Fecha/Hora</div>
                                    <div class="info-value">{datetime.now().strftime('%d/%m/%Y · %H:%M:%S')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="footer-text">
                            Mensaje generado automáticamente por <span class="footer-brand">Hernando</span>
                        </div>
                    </div>
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
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6; 
                        color: #1f2937;
                        background-color: #f9fafb;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{ 
                        background: #000000;
                        color: white; 
                        padding: 32px 24px;
                        text-align: center;
                    }}
                    .header h1 {{
                        font-size: 28px;
                        font-weight: 700;
                        margin: 0;
                        letter-spacing: -0.5px;
                    }}
                    .header .subtitle {{
                        font-size: 14px;
                        opacity: 0.9;
                        margin-top: 8px;
                    }}
                    .content {{ padding: 32px 24px; }}
                    .greeting {{
                        font-size: 16px;
                        color: #374151;
                        margin-bottom: 24px;
                        line-height: 1.7;
                    }}
                    .highlight-box {{
                        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 24px;
                        border: 2px solid #10b981;
                        text-align: center;
                    }}
                    .highlight-title {{
                        font-size: 14px;
                        font-weight: 600;
                        color: #065f46;
                        margin-bottom: 8px;
                    }}
                    .highlight-date {{
                        font-size: 24px;
                        font-weight: 700;
                        color: #047857;
                        margin-bottom: 4px;
                    }}
                    .highlight-time {{
                        font-size: 14px;
                        color: #065f46;
                    }}
                    .card {{ 
                        margin-bottom: 16px; 
                        padding: 20px;
                        background: linear-gradient(to right, #f9fafb 0%, #ffffff 100%);
                        border-radius: 12px;
                        border-left: 4px solid #10b981;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }}
                    .card-title {{
                        font-size: 13px;
                        font-weight: 600;
                        color: #6b7280;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 12px;
                    }}
                    .info-grid {{
                        display: table;
                        width: 100%;
                    }}
                    .info-row {{
                        display: table-row;
                    }}
                    .info-label {{
                        display: table-cell;
                        font-size: 14px;
                        font-weight: 600;
                        color: #6b7280;
                        padding: 8px 0;
                        width: 45%;
                    }}
                    .info-value {{
                        display: table-cell;
                        font-size: 15px;
                        color: #1f2937;
                        padding: 8px 0;
                        font-weight: 500;
                    }}
                    .contact-box {{
                        background: #fef3c7;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 24px 0;
                        border: 2px solid #fbbf24;
                    }}
                    .contact-title {{
                        font-size: 14px;
                        font-weight: 600;
                        color: #92400e;
                        margin-bottom: 8px;
                    }}
                    .contact-text {{
                        font-size: 14px;
                        color: #78350f;
                        line-height: 1.6;
                    }}
                    .contact-link {{
                        color: #b45309;
                        text-decoration: none;
                        font-weight: 600;
                    }}
                    .footer {{ 
                        background-color: #f9fafb;
                        padding: 24px;
                        text-align: center;
                        border-top: 1px solid #e5e7eb;
                    }}
                    .footer-text {{
                        font-size: 13px;
                        color: #6b7280;
                        line-height: 1.6;
                    }}
                    .footer-brand {{
                        font-weight: 600;
                        color: #10b981;
                    }}
                    .emoji {{ font-size: 20px; margin-right: 8px; }}
                    .logo {{ 
                        width: 240px;
                        height: auto;
                        margin: 0;
                    }}
                    .header h1, .header .subtitle {{ display: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        {'<img src="' + LOGO_BLANCO + '" alt="Fundo Moraga" class="logo">' if LOGO_BLANCO else ''}
                        <h1><span class="emoji">✅</span> Reserva Confirmada</h1>
                        <div class="subtitle">Tu reserva está lista · Fundo Moraga</div>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">
                            Hola <strong>{name_txt}</strong>, ya verificamos tu transferencia. 🎉<br>
                            ¡Tu reserva quedó confirmada!
                        </div>
                        
                        <div class="highlight-box">
                            <div class="highlight-title">TU VISITA</div>
                            <div class="highlight-date">{day_txt}, {date_txt}</div>
                            <div class="highlight-time">🕘 Llegada: {arrival_txt}</div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">📋 Detalles de tu Reserva</div>
                            <div class="info-grid">
                                <div class="info-row">
                                    <div class="info-label">🚗 Automóviles</div>
                                    <div class="info-value">{cars_count} auto{'s' if cars_count != 1 else ''}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">🏍️ Motos</div>
                                    <div class="info-value">{motos_count} moto{'s' if motos_count != 1 else ''}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">👥 Personas</div>
                                    <div class="info-value">{people_count} persona{'s' if people_count != 1 else ''}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">💵 Tarifa Total</div>
                                    <div class="info-value">{escape(price_txt)}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="contact-box">
                            <div class="contact-title">📞 ¿Necesitas hacer cambios?</div>
                            <div class="contact-text">
                                Contáctanos en <a href="mailto:contacto@fundomoraga.com" class="contact-link">contacto@fundomoraga.com</a><br>
                                o por WhatsApp al <a href="https://wa.me/56941242609" class="contact-link">+56 9 4124 2609</a>
                            </div>
                        </div>
                        
                        <div style="background: #eff6ff; border-radius: 12px; padding: 16px; border-left: 4px solid #3b82f6;">
                            <p style="font-size: 14px; color: #1e40af; margin: 0;">
                                📧 <strong>Recordatorio:</strong> Te enviaremos un correo un día antes de tu visita.
                            </p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="footer-text">
                            Mensaje automático de <span class="footer-brand">Hernando</span> · Fundo Moraga
                        </div>
                    </div>
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
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6; 
                        color: #1f2937;
                        background-color: #f9fafb;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 16px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{ 
                        background: #000000;
                        color: white; 
                        padding: 32px 24px;
                        text-align: center;
                    }}
                    .header h1 {{
                        font-size: 28px;
                        font-weight: 700;
                        margin: 0;
                        letter-spacing: -0.5px;
                    }}
                    .header .subtitle {{
                        font-size: 14px;
                        opacity: 0.9;
                        margin-top: 8px;
                    }}
                    .content {{ padding: 32px 24px; }}
                    .greeting {{
                        font-size: 16px;
                        color: #374151;
                        margin-bottom: 24px;
                        line-height: 1.7;
                    }}
                    .highlight-box {{
                        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                        border-radius: 12px;
                        padding: 24px;
                        margin-bottom: 24px;
                        border: 2px solid #fbbf24;
                        text-align: center;
                    }}
                    .highlight-emoji {{
                        font-size: 48px;
                        margin-bottom: 12px;
                    }}
                    .highlight-title {{
                        font-size: 14px;
                        font-weight: 600;
                        color: #92400e;
                        margin-bottom: 8px;
                    }}
                    .highlight-date {{
                        font-size: 24px;
                        font-weight: 700;
                        color: #b45309;
                        margin-bottom: 4px;
                    }}
                    .highlight-time {{
                        font-size: 14px;
                        color: #78350f;
                    }}
                    .card {{ 
                        margin-bottom: 16px; 
                        padding: 20px;
                        background: linear-gradient(to right, #f9fafb 0%, #ffffff 100%);
                        border-radius: 12px;
                        border-left: 4px solid #f59e0b;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    }}
                    .card-title {{
                        font-size: 13px;
                        font-weight: 600;
                        color: #6b7280;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 12px;
                    }}
                    .info-grid {{
                        display: table;
                        width: 100%;
                    }}
                    .info-row {{
                        display: table-row;
                    }}
                    .info-label {{
                        display: table-cell;
                        font-size: 14px;
                        font-weight: 600;
                        color: #6b7280;
                        padding: 8px 0;
                        width: 45%;
                    }}
                    .info-value {{
                        display: table-cell;
                        font-size: 15px;
                        color: #1f2937;
                        padding: 8px 0;
                        font-weight: 500;
                    }}
                    .contact-box {{
                        background: #dbeafe;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 24px 0 0 0;
                        border: 2px solid #3b82f6;
                    }}
                    .contact-title {{
                        font-size: 14px;
                        font-weight: 600;
                        color: #1e40af;
                        margin-bottom: 8px;
                    }}
                    .contact-text {{
                        font-size: 14px;
                        color: #1e3a8a;
                        line-height: 1.6;
                    }}
                    .contact-link {{
                        color: #2563eb;
                        text-decoration: none;
                        font-weight: 600;
                    }}
                    .footer {{ 
                        background-color: #f9fafb;
                        padding: 24px;
                        text-align: center;
                        border-top: 1px solid #e5e7eb;
                    }}
                    .footer-text {{
                        font-size: 13px;
                        color: #6b7280;
                        line-height: 1.6;
                    }}
                    .footer-brand {{
                        font-weight: 600;
                        color: #f59e0b;
                    }}
                    .emoji {{ font-size: 20px; margin-right: 8px; }}
                    .logo {{ 
                        width: 240px;
                        height: auto;
                        margin: 0;
                    }}
                    .header h1, .header .subtitle {{ display: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        {'<img src="' + LOGO_BLANCO + '" alt="Fundo Moraga" class="logo">' if LOGO_BLANCO else ''}
                        <h1><span class="emoji">⏰</span> Recordatorio de Reserva</h1>
                        <div class="subtitle">Tu visita es mañana · Fundo Moraga</div>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">
                            Hola <strong>{name_txt}</strong>, 👋<br>
                            Te recordamos que tu reserva en <strong>Batuco Off Road</strong> es mañana.
                        </div>
                        
                        <div class="highlight-box">
                            <div class="highlight-emoji">📅</div>
                            <div class="highlight-title">TU VISITA ES MAÑANA</div>
                            <div class="highlight-date">{day_txt}, {date_txt}</div>
                            <div class="highlight-time">🕘 Llegada: {arrival_txt}</div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">📋 Detalles de tu Reserva</div>
                            <div class="info-grid">
                                <div class="info-row">
                                    <div class="info-label">🚗 Automóviles</div>
                                    <div class="info-value">{cars_count} auto{'s' if cars_count != 1 else ''}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">🏍️ Motos</div>
                                    <div class="info-value">{motos_count} moto{'s' if motos_count != 1 else ''}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">👥 Personas</div>
                                    <div class="info-value">{people_count} persona{'s' if people_count != 1 else ''}</div>
                                </div>
                                <div class="info-row">
                                    <div class="info-label">💵 Tarifa Total</div>
                                    <div class="info-value">{escape(price_txt)}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="contact-box">
                            <div class="contact-title">📞 ¿Necesitas hacer cambios?</div>
                            <div class="contact-text">
                                Contáctanos en <a href="mailto:contacto@fundomoraga.com" class="contact-link">contacto@fundomoraga.com</a><br>
                                o por WhatsApp al <a href="https://wa.me/56941242609" class="contact-link">+56 9 4124 2609</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="footer-text">
                            Mensaje automático de <span class="footer-brand">Hernando</span> · Fundo Moraga
                        </div>
                    </div>
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
