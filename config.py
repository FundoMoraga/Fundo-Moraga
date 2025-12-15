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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Instagram
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID")

# Bot Configuration
BOT_NAME = os.getenv("BOT_NAME", "Fundo Moraga Bot")
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))

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
