"""
Configuración del chatbot de Fundo Moraga
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Azure Cosmos DB
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "chatbot")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "conversations")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

# Instagram
def _clean_token(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().strip('"').strip("'")
    if cleaned.lower().startswith("bearer "):
        cleaned = cleaned.split(" ", 1)[1].strip()
    return cleaned or None

INSTAGRAM_ACCESS_TOKEN = _clean_token(os.getenv("INSTAGRAM_ACCESS_TOKEN"))
INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID")

# Bot Configuration
BOT_NAME = os.getenv("BOT_NAME", "Fundo Moraga Bot")
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))

# Google Calendar (opcional, para agendamientos)
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_CALENDAR_TIMEZONE = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "America/Santiago")
GOOGLE_CALENDAR_SEND_UPDATES = os.getenv("GOOGLE_CALENDAR_SEND_UPDATES", "all")

# Verificación de transferencia (opcional)
PAYMENT_INBOX_HOST = os.getenv("PAYMENT_INBOX_HOST", "imap.gmail.com")
PAYMENT_INBOX_USER = os.getenv("PAYMENT_INBOX_USER")  # ej: contacto@gmail.com
PAYMENT_INBOX_PASSWORD = os.getenv("PAYMENT_INBOX_PASSWORD")  # ideal: App Password
PAYMENT_INBOX_FOLDER = os.getenv("PAYMENT_INBOX_FOLDER", "INBOX")
PAYMENT_EMAIL_FROM_CONTAINS = os.getenv("PAYMENT_EMAIL_FROM_CONTAINS", "Banco")
PAYMENT_EMAIL_SUBJECT_CONTAINS = os.getenv("PAYMENT_EMAIL_SUBJECT_CONTAINS", "transferencia")
# Auto-confirmación temporal de transferencias (ISO8601, ej: 2025-12-20T12:00:00-03:00)
TEMP_TRANSFER_AUTO_CONFIRM_UNTIL = os.getenv("TEMP_TRANSFER_AUTO_CONFIRM_UNTIL")

# Recordatorios de reserva (email)
REMINDER_SCHEDULER_ENABLED = os.getenv("REMINDER_SCHEDULER_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
    "y",
    "si",
)
REMINDER_POLL_SECONDS = int(os.getenv("REMINDER_POLL_SECONDS", "300"))
REMINDER_SEND_HOUR = int(os.getenv("REMINDER_SEND_HOUR", "9"))

# Validar configuración requerida
def validate_config():
    """Valida que todas las variables de entorno requeridas estén configuradas"""
    required_vars = {
        "COSMOS_ENDPOINT": COSMOS_ENDPOINT,
        "COSMOS_KEY": COSMOS_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(
            f"Faltan las siguientes variables de entorno: {', '.join(missing)}\n"
            "Por favor, copia .env.example a .env y configura los valores."
        )
