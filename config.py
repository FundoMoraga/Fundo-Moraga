"""
Configuración del chatbot de Fundo Moraga
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
# Utilidad para limpiar variables de entorno con comillas
def _clean_env(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().strip('"').strip("'")
    return cleaned or None

# Azure Cosmos DB
# Limpia posibles comillas en variables de entorno provenientes de Railway/ENV
COSMOS_ENDPOINT = _clean_env(os.getenv("COSMOS_ENDPOINT"))
COSMOS_KEY = _clean_env(os.getenv("COSMOS_KEY"))
COSMOS_CONNECTION_STRING = _clean_env(os.getenv("COSMOS_CONNECTION_STRING"))
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "chatbot")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "conversations")
COSMOS_PROMPTS_DB = os.getenv("COSMOS_PROMPTS_DB", "Entrenamiento")
COSMOS_PROMPTS_CONTAINER = os.getenv("COSMOS_PROMPTS_CONTAINER", "Hernando")
COSMOS_PROMPTS_PERSONA = os.getenv("COSMOS_PROMPTS_PERSONA", "Hernando")

# Cosmos DB - Memoria
COSMOS_MEMORY_CONTAINER = os.getenv("COSMOS_MEMORY_CONTAINER", "Memoria")
# Ruta del PK del contenedor Memoria (ej: /Categoria, /type, /tenantId)
COSMOS_MEMORY_PK_PATH = os.getenv("COSMOS_MEMORY_PK_PATH", "/Categoria")

# OpenAI
OPENAI_API_KEY = _clean_env(os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

# Azure Translator (Text Translation)
AZURE_TRANSLATOR_ENDPOINT = os.getenv(
    "AZURE_TRANSLATOR_ENDPOINT", "https://hernando.cognitiveservices.azure.com/"
)
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION", "southcentralus")

# Azure AI Language (Text Analytics)
AZURE_LANGUAGE_ENDPOINT = _clean_env(
    os.getenv("AZURE_LANGUAGE_ENDPOINT", "https://hernando.cognitiveservices.azure.com/")
)
AZURE_LANGUAGE_KEY = _clean_env(os.getenv("AZURE_LANGUAGE_KEY"))

# Language Service URL (Railway internal)
LANGUAGE_SERVICE_URL = _clean_env(os.getenv("LANGUAGE_SERVICE_URL"))
TRANSLATOR_SERVICE_URL = _clean_env(os.getenv("TRANSLATOR_SERVICE_URL"))

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
PAYMENT_INBOX_MAX_SCAN = int(os.getenv("PAYMENT_INBOX_MAX_SCAN", "50"))
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

# Reintentos de correos pendientes (Resend)
PENDING_EMAIL_RETRY_MINUTES = int(os.getenv("PENDING_EMAIL_RETRY_MINUTES", "10"))
PENDING_EMAIL_RETRY_MAX_MINUTES = int(os.getenv("PENDING_EMAIL_RETRY_MAX_MINUTES", "60"))

# Validar configuración requerida
def validate_config():
    """Valida que todas las variables de entorno requeridas estén configuradas"""
    # Cosmos puede venir por connection string o endpoint+key
    cosmos_ok = bool(COSMOS_CONNECTION_STRING) or bool(COSMOS_ENDPOINT and COSMOS_KEY)
    missing = []
    if not cosmos_ok:
        missing.append("COSMOS_CONNECTION_STRING o COSMOS_ENDPOINT+COSMOS_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        raise ValueError(
            f"Faltan las siguientes variables de entorno: {', '.join(missing)}\n"
            "Por favor, copia .env.example a .env y configura los valores."
        )
