"""
Servidor web para Hernando - Fundo Moraga
Maneja webhooks de Instagram y chat de la página web
"""
import traceback
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import config
import requests
from instagram_bot_enhanced import InstagramBotEnhanced as HernandoBot
from reminder_scheduler import start_reminder_scheduler
from typing import Optional, Tuple
from datetime import datetime, timezone
import json
# Cliente de Azure Storage (opcional)
import azure_storage_client as storage_client
from azure_storage_client import get_blob_url, list_blobs

def _config_status() -> Tuple[bool, list[str], list[str]]:
    """
    Retorna (configured_ok, missing_required, warnings).
    required: Cosmos + OpenAI para chat.
    warnings: features opcionales (Resend, Google Calendar, inbox pagos).
    """
    missing_required = []
    warnings = []

    # Cosmos: aceptar connection string o endpoint+key
    cosmos_cs = os.getenv("COSMOS_CONNECTION_STRING")
    cosmos_ep = os.getenv("COSMOS_ENDPOINT")
    cosmos_key = os.getenv("COSMOS_KEY")
    if not (cosmos_cs or (cosmos_ep and cosmos_key)):
        missing_required.append("COSMOS_CONNECTION_STRING o COSMOS_ENDPOINT+COSMOS_KEY")
    if not config.OPENAI_API_KEY:
        missing_required.append("OPENAI_API_KEY")

    has_smtp = bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))
    if not (has_smtp or os.getenv("RESEND_API_KEY")):
        warnings.append("SMTP_USER/SMTP_PASSWORD o RESEND_API_KEY (emails)")
    if not os.getenv("GOOGLE_CALENDAR_ID"):
        warnings.append("GOOGLE_CALENDAR_ID (calendar)")
    if not (os.getenv("PAYMENT_INBOX_USER") and os.getenv("PAYMENT_INBOX_PASSWORD")):
        warnings.append("PAYMENT_INBOX_USER/PAYMENT_INBOX_PASSWORD (payment inbox)")
    if not os.getenv("INSTAGRAM_ACCESS_TOKEN"):
        warnings.append("INSTAGRAM_ACCESS_TOKEN (instagram)")
    if not os.getenv("INSTAGRAM_PAGE_ID"):
        warnings.append("INSTAGRAM_PAGE_ID (instagram)")

    # Storage opcional: avisar si falta (para /media y assets remotos)
    if not storage_client.AZURE_STORAGE_CONNECTION_STRING or not storage_client.AZURE_STORAGE_CONTAINER:
        warnings.append("AZURE_STORAGE_CONNECTION_STRING/AZURE_STORAGE_CONTAINER (storage)")
    if not storage_client.AZURE_STORAGE_URL_BASE:
        warnings.append("AZURE_STORAGE_URL_BASE (storage)")

    return (len(missing_required) == 0, missing_required, warnings)

app = Flask(__name__, static_folder='Web', static_url_path='')
CORS(app)  # Permitir peticiones desde fundomoraga.com

# Evitar doble scheduler cuando existe un servicio dedicado.
RUN_SCHEDULER_THREAD = os.getenv("RUN_SCHEDULER_THREAD", "").lower() in ("1", "true", "yes", "y", "si")
if RUN_SCHEDULER_THREAD:
    start_reminder_scheduler()

# Inicializar bot al arranque para evitar timeouts en primera petición
_bot: Optional[HernandoBot] = None
_bot_init_error: Optional[str] = None

def _init_bot_on_startup():
    """Inicializa el bot al arranque del servidor"""
    global _bot, _bot_init_error
    print("[STARTUP] Comenzando inicialización de bot...")
    try:
        configured_ok, missing_required, warnings = _config_status()
        if not configured_ok:
            msg = f"Faltan variables requeridas: {', '.join(missing_required)}"
            print(f"[STARTUP] ⚠️ Bot no inicializado: {msg}")
            _bot_init_error = f"Configuración incompleta: {msg}"
            return
        
        print("[STARTUP] ✓ Configuración completada")
        print("[STARTUP] 🤖 Pre-inicializando HernandoBot...")
        _bot = HernandoBot()
        print("[STARTUP] ✅ HernandoBot pre-inicializado exitosamente")
    except Exception as e:
        msg = f"Excepción durante inicialización: {type(e).__name__}: {str(e)}"
        print(f"[STARTUP] ❌ Error: {msg}")
        traceback.print_exc()
        _bot_init_error = msg

# Pre-inicializar el bot
_init_bot_on_startup()

# Token de verificación del webhook (configúralo en .env)
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "fundomoraga_2025")


def get_bot() -> HernandoBot:
    """Obtiene la instancia del bot (pre-inicializado al arranque)"""
    global _bot, _bot_init_error
    if _bot is not None:
        return _bot
    if _bot_init_error is not None:
        raise RuntimeError(_bot_init_error)
    raise RuntimeError("Bot no inicializado")


def _extract_waha_events(payload: dict) -> list[dict]:
    events: list[dict] = []
    if not isinstance(payload, dict):
        return events

    if "event" in payload and "payload" in payload:
        events.append(payload)

    nested = payload.get("events")
    if isinstance(nested, list):
        events.extend([e for e in nested if isinstance(e, dict)])

    messages = payload.get("messages")
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict):
                events.append({"event": "message", "payload": msg, "session": payload.get("session")})

    return events


def _extract_waha_text(payload: dict) -> str:
    for key in ("body", "text", "message", "caption", "content"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    message_obj = payload.get("message")
    if isinstance(message_obj, dict):
        for key in ("text", "body", "caption"):
            value = message_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _waha_from_me(payload: dict) -> bool:
    for key in ("fromMe", "from_me", "isOutgoing", "self", "is_from_me"):
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    return False


def _extract_waha_message_id(payload: dict) -> str:
    for key in ("id", "messageId", "message_id", "msgId"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    message_obj = payload.get("message")
    if isinstance(message_obj, dict):
        for key in ("id", "messageId", "message_id", "msgId"):
            value = message_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        key_obj = message_obj.get("key")
        if isinstance(key_obj, dict):
            value = key_obj.get("id")
            if isinstance(value, str) and value.strip():
                return value.strip()

    key_obj = payload.get("key")
    if isinstance(key_obj, dict):
        value = key_obj.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def _extract_waha_chat_id(payload: dict) -> str:
    for key in ("from", "chatId", "chat_id", "jid", "to", "remoteJid"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _send_waha_text(chat_id: str, text: str, session: str) -> bool:
    if not config.WAHA_API_URL:
        print("⚠️ WAHA API URL no configurada (WAHA_API_URL).")
        return False

    url = f"{config.WAHA_API_URL.rstrip('/')}/api/sendText"
    headers = {"Content-Type": "application/json"}
    if config.WAHA_API_KEY:
        headers["X-API-KEY"] = config.WAHA_API_KEY

    payload = {
        "session": session or "default",
        "chatId": chat_id,
        "text": text,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
    except Exception as e:
        print(f"❌ Error enviando WhatsApp: {e}")
        return False

    if response.status_code >= 200 and response.status_code < 300:
        return True

    print(f"❌ WAHA respondió {response.status_code}: {response.text}")
    return False


@app.route('/oembed.json')
def oembed():
    """Endpoint oEmbed para Canva."""
    return jsonify({
        "version": "1.0",
        "type": "rich",
        "provider_name": "Fundo Moraga",
        "provider_url": "https://fundomoraga.com",
        "title": "Chat IA Hernando",
        "html": '<iframe src="https://hernando.fundomoraga.com/embed" width="100%" height="600" frameborder="0" allowfullscreen></iframe>',
        "width": 800,
        "height": 600
    })


@app.after_request
def add_security_headers(response):
    # Permitir que el widget sea embebido (iframe) solo desde dominios autorizados (Canva + Fundo Moraga).
    # Esto evita el error de Canva "Este contenido está bloqueado".
    response.headers.pop("X-Frame-Options", None)
    response.headers["Content-Security-Policy"] = (
        "frame-ancestors 'self' "
        "https://fundomoraga.com https://www.fundomoraga.com "
        "https://canva.com https://www.canva.com https://*.canva.com;"
    )
    return response


@app.route('/')
def home():
    """Página de inicio: chat a página completa (para hernando.fundomoraga.com)."""
    return render_template('chat_fullscreen.html')


@app.route('/favicon.ico')
def favicon():
    """Servir favicon desde static/hernando.jpg como fallback."""
    from flask import send_from_directory
    return send_from_directory('static', 'hernando.jpg', mimetype='image/jpeg')


@app.route('/static/<path:filename>')
def static_assets(filename: str):
    """Servir assets del chat (hernando.jpg/mp4) desde /static."""
    return send_from_directory('static', filename)

# Nuevo endpoint para servir archivos multimedia desde Azure Storage
@app.route('/media/<tipo>/<path:filename>')
def media_from_azure(tipo, filename):
    """
    Redirige a la URL pública del blob en Azure Storage.
    tipo: images, videos, data
    filename: nombre del archivo
    """
    storage_ready = (
        storage_client.blob_service_client
        and storage_client.container_client
        and storage_client.AZURE_STORAGE_URL_BASE
    )
    if not storage_ready:
        return jsonify({"error": "storage_not_configured"}), 503

    # Validar tipo permitido
    if tipo not in ("images", "videos", "data"):
        return jsonify({"error": "Tipo no permitido"}), 400
    blob_path = f"{tipo}/{filename}"
    try:
        url = get_blob_url(blob_path)
    except Exception as exc:
        return jsonify({"error": "storage_error", "message": str(exc)}), 502
    return jsonify({"url": url})
@app.route('/status')
def status():
    """Estado JSON (útil para monitoreo)."""
    configured_ok, missing_required, warnings = _config_status()
    return jsonify({
        "bot": "Hernando",
        "status": "online",
        "service": "Fundo Moraga",
        "version": "1.0",
        "configured": configured_ok,
        "missing_required": missing_required,
        "warnings": warnings
    })


@app.route('/health')
def health():
    """Endpoint de salud para Railway"""
    configured_ok, missing_required, warnings = _config_status()
    # Siempre 200 para no bloquear el arranque en Railway; la app reporta si está "degraded".
    return jsonify({
        "status": "healthy" if configured_ok else "degraded",
        "configured": configured_ok,
        "missing_required": missing_required,
        "warnings": warnings
    }), 200


@app.route('/debug')
def debug():
    """Endpoint de debug para diagnosticar problemas (no usar en producción)"""
    configured_ok, missing_required, warnings = _config_status()
    
    # Información sobre el bot
    bot_status = "inicializado"
    bot_error = None
    if _bot is None and _bot_init_error is None:
        bot_status = "no inicializado (esperando configuración)"
    elif _bot is None:
        bot_status = "falló en inicialización"
        bot_error = _bot_init_error
    
    # Variables de entorno (SIN REVELAR SECRETOS)
    env_info = {
        "COSMOS_CONNECTION_STRING": "✓ configurada" if os.getenv("COSMOS_CONNECTION_STRING") else "✗ NO configurada",
        "COSMOS_ENDPOINT": "✓ configurada" if os.getenv("COSMOS_ENDPOINT") else "✗ NO configurada",
        "COSMOS_KEY": "✓ configurada" if os.getenv("COSMOS_KEY") else "✗ NO configurada",
        "OPENAI_API_KEY": "✓ configurada" if os.getenv("OPENAI_API_KEY") else "✗ NO configurada",
        "INSTAGRAM_ACCESS_TOKEN": "✓ configurada" if os.getenv("INSTAGRAM_ACCESS_TOKEN") else "✗ NO configurada",
        "INSTAGRAM_PAGE_ID": "✓ configurada" if os.getenv("INSTAGRAM_PAGE_ID") else "✗ NO configurada",
    }
    
    return jsonify({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "status": "ok" if configured_ok else "incompleta",
            "missing_required": missing_required,
            "warnings": warnings,
        },
        "bot": {
            "status": bot_status,
            "error": bot_error,
        },
        "environment_variables": env_info,
    }), 200


# ============= WEB CHAT API =============

@app.route('/api/chat', methods=['POST'])
def web_chat():
    """
    Endpoint para el chat de la página web fundomoraga.com
    
    Espera JSON:
    {
        "user_id": "web_user_12345",
        "message": "¿Cuál es la historia del fundo?",
        "session_id": "optional_session_id"
    }
    
    Retorna JSON:
    {
        "response": "Texto de respuesta de Hernando",
        "timestamp": "2025-12-15T10:30:00Z"
    }
    """
    try:
        print("📨 Recibiendo petición en /api/chat")
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Se requiere el campo 'message'"
            }), 400
        
        # Extraer datos
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', f"web_{request.remote_addr}")
        
        print(f"👤 User: {user_id}, Message: {user_message[:50]}...")
        
        if not user_message:
            return jsonify({
                "error": "El mensaje no puede estar vacío"
            }), 400
        
        # Procesar mensaje con el bot
        try:
            print("🔄 Obteniendo instancia del bot...")
            bot = get_bot()
            print("✅ Bot obtenido, procesando mensaje...")
        except Exception as e:
            print(f"❌ Error obteniendo bot: {e}")
            return jsonify({
                "error": "Servicio no configurado",
                "message": str(e)
            }), 503

        response = bot.process_message(user_id, user_message)
        print(f"✅ Respuesta generada: {len(response)} caracteres")

        close_token = "[[CLOSE_CHAT]]"
        close_chat = False
        if isinstance(response, str) and close_token in response:
            close_chat = True
            response = response.replace(close_token, "").strip()

        # Si el flujo cerró la conversación, generar resumen final interno (no bloqueante).
        if close_chat:
            try:
                bot.finalize_conversation(user_id=user_id, reason="close_chat", platform="Web")
            except Exception as e:
                print(f"[WARNING] Error enviando resumen final: {e}")
        
        from datetime import datetime, timezone
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bot": "Hernando",
            "close_chat": close_chat
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error en web chat: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "message": str(e)
        }), 500


@app.route('/api/chat/init', methods=['POST'])
def web_chat_init():
    """
    Inicializa una sesión de chat web y registra el mensaje de bienvenida en el historial
    para evitar doble saludo en la primera respuesta del bot.

    Espera JSON:
    {
        "user_id": "web_user_12345"
    }
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', f"web_{request.remote_addr}")

        try:
            bot = get_bot()
        except Exception as e:
            return jsonify({
                "error": "Servicio no configurado",
                "message": str(e)
            }), 503

        greeting = bot.start_web_conversation(user_id=user_id)

        from datetime import datetime, timezone
        return jsonify({
            "greeting": greeting,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bot": "Hernando"
        }), 200
    except Exception as e:
        print(f"[ERROR] Error en web chat init: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "message": str(e)
        }), 500


@app.route('/api/chat/end', methods=['POST'])
def web_chat_end():
    """
    Finaliza una conversación web y envía un resumen interno por correo.
    Espera JSON: { "user_id": "..." , "reason": "optional" }
    """
    try:
        data = request.get_json(silent=True)
        if data is None:
            try:
                raw = (request.data or b"").decode("utf-8", errors="ignore").strip()
                data = json.loads(raw) if raw else {}
            except Exception:
                data = {}
        user_id = data.get("user_id", f"web_{request.remote_addr}")
        reason = data.get("reason") or "client_end"

        try:
            bot = get_bot()
        except Exception as e:
            return jsonify({"error": "Servicio no configurado", "message": str(e)}), 503

        bot.finalize_conversation(user_id=user_id, reason=reason)
        return jsonify({"ok": True}), 200
    except Exception as e:
        print(f"[ERROR] Error en web chat end: {e}")
        return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500


@app.route('/api/chat/history', methods=['POST'])
def chat_history():
    """
    Obtiene el historial de conversación de un usuario web
    
    Espera JSON:
    {
        "user_id": "web_user_12345",
        "limit": 10
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        limit = data.get('limit', 10)
        
        if not user_id:
            return jsonify({"error": "Se requiere user_id"}), 400
        
        try:
            bot = get_bot()
        except Exception as e:
            return jsonify({
                "error": "Servicio no configurado",
                "message": str(e)
            }), 503

        # Obtener historial de Cosmos DB
        history = bot.conversation_store.get_conversation_history(user_id=user_id, limit=limit)
        
        # Formatear para respuesta
        messages = [
            {
                "role": msg.get("role"),
                "message": msg.get("message"),
                "timestamp": msg.get("timestamp")
            }
            for msg in history
        ]
        
        return jsonify({
            "history": messages,
            "count": len(messages)
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo historial: {e}")
        return jsonify({"error": str(e)}), 500


# ============= WHATSAPP (WAHA) WEBHOOK =============

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook para WAHA (WhatsApp HTTP API).
    Espera eventos con payload de mensaje y responde vía WAHA /api/sendText.
    """
    if config.WAHA_WEBHOOK_SECRET:
        provided = (
            request.headers.get("X-WAHA-SECRET")
            or request.headers.get("X-Webhook-Secret")
            or request.args.get("token")
        )
        if provided != config.WAHA_WEBHOOK_SECRET:
            return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True)
    if data is None:
        try:
            raw = (request.data or b"").decode("utf-8", errors="ignore").strip()
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}

    events = _extract_waha_events(data or {})
    if not events:
        return jsonify({"ok": True, "handled": 0}), 200

    try:
        bot = get_bot()
    except Exception as e:
        return jsonify({"error": "Servicio no configurado", "message": str(e)}), 503

    handled = 0
    seen_messages: set[str] = set()
    for event in events:
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue

        if _waha_from_me(payload):
            continue

        chat_id = _extract_waha_chat_id(payload)
        if not chat_id:
            continue

        message_id = _extract_waha_message_id(payload)
        if message_id:
            dedupe_key = f"{chat_id}:{message_id}"
            if dedupe_key in seen_messages:
                continue
            seen_messages.add(dedupe_key)

        if "status@broadcast" in chat_id:
            continue

        if chat_id.endswith("@g.us") and not config.WAHA_ALLOW_GROUPS:
            continue

        text = _extract_waha_text(payload)
        if not text:
            msg_type = str(payload.get("type") or payload.get("messageType") or "").lower()
            if msg_type and msg_type != "chat":
                text = "[adjunto]"
            elif payload.get("media") or payload.get("file") or payload.get("attachment"):
                text = "[adjunto]"

        if not text:
            continue

        session = (
            (event.get("session") or data.get("session") or config.WAHA_SESSION or "default").strip()
        )
        user_id = f"wa_{chat_id}"

        if text == "[adjunto]":
            response = "Recibí un adjunto. ¿Me puedes contar en texto qué necesitas o qué te gustaría coordinar?"
        else:
            response = bot.process_message(
                user_id,
                text,
                platform="whatsapp",
                source="whatsapp_webhook",
                message_id=str(payload.get("id") or payload.get("messageId") or payload.get("message_id") or ""),
            )

        close_token = "[[CLOSE_CHAT]]"
        close_chat = False
        if isinstance(response, str) and close_token in response:
            close_chat = True
            response = response.replace(close_token, "").strip()

        if response:
            _send_waha_text(chat_id, response, session)
            handled += 1

        if close_chat:
            try:
                bot.finalize_conversation(user_id=user_id, reason="close_chat", platform="WhatsApp")
            except Exception as e:
                print(f"[WARNING] Error enviando resumen final: {e}")

    return jsonify({"ok": True, "handled": handled}), 200


# ============= EJEMPLOS DE INTEGRACIÓN WEB =============

@app.route('/api/docs')
def api_docs():
    """Documentación simple de la API"""
    docs = {
        "title": "Hernando API - Fundo Moraga",
        "version": "1.0",
        "endpoints": {
            "/api/chat": {
                "method": "POST",
                "description": "Enviar mensaje al chatbot",
                "body": {
                    "user_id": "string (opcional)",
                    "message": "string (requerido)"
                },
                "response": {
                    "response": "string",
                    "timestamp": "string",
                    "bot": "Hernando"
                }
            },
            "/api/chat/history": {
                "method": "POST",
                "description": "Obtener historial de conversación",
                "body": {
                    "user_id": "string (requerido)",
                    "limit": "number (opcional, default: 10)"
                }
            },
            "/webhook/instagram": {
                "method": "GET/POST",
                "description": "Webhook para Instagram Messaging API"
            },
            "/webhook/whatsapp": {
                "method": "POST",
                "description": "Webhook para WAHA (WhatsApp HTTP API)"
            }
        },
        "example_web_integration": """
<!-- Ejemplo de integración en fundomoraga.com -->
<script>
async function enviarMensaje(mensaje) {
    const response = await fetch('https://hernando.fundomoraga.com/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: 'web_' + Date.now(),
            message: mensaje
        })
    });
    
    const data = await response.json();
    console.log('Respuesta de Hernando:', data.response);
    return data.response;
}

// Uso
enviarMensaje('¿Cuál es la historia del fundo?');
</script>
        """
    }
    
    return jsonify(docs), 200



# ============= CHAT WIDGET =============
@app.route('/widget')
def chat_widget_page():
    """Sirve la página del widget de chat para ser embebida."""
    try:
        return render_template('chat_widget.html')
    except Exception as e:
        return f"<pre>Error rendering template:\n{traceback.format_exc()}</pre>"

@app.route('/embed')
def chat_embed_page():
    """Versión para embeds (Canva/iframes): sin burbuja, solo chat."""
    try:
        return render_template('chat_embed.html')
    except Exception as e:
        return f"<pre>Error rendering template:\n{traceback.format_exc()}</pre>"


if __name__ == '__main__':
    # Validar configuración
    try:
        config.validate_config()
        print(f"\n[BOT] Hernando - Asistente Virtual de Fundo Moraga")
        print("=" * 60)
        print(f"[OK] Configuracion valida")
        print(f"[DB] Cosmos DB: {config.COSMOS_DATABASE}/{config.COSMOS_CONTAINER}")
        print(f"[AI] Modelo: {config.OPENAI_MODEL}")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Error en configuracion: {e}")
        exit(1)
    
    # Puerto para Railway (usa la variable de entorno PORT)
    port = int(os.getenv('PORT', 5000))
    
    print(f"\n[STARTUP] Servidor iniciando en puerto {port}")
    print(f"[API] Instagram webhook: /webhook/instagram")
    print(f"[API] Web chat API: /api/chat")
    print(f"[DOCS] Documentacion: /api/docs\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
