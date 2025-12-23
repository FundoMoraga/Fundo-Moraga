"""
Servidor web para Hernando - Fundo Moraga
Maneja webhooks de Instagram y chat de la página web
"""
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import config
from instagram_bot_enhanced import InstagramBotEnhanced as InstagramBot
from reminder_scheduler import start_reminder_scheduler
from typing import Optional, Tuple
import json

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde fundomoraga.com
start_reminder_scheduler()

# Inicializar bot (lazy) para que el servidor pueda arrancar en Railway
# incluso si faltan variables de entorno; las rutas de chat devolverán 503 con detalle.
_bot: Optional[InstagramBot] = None
_bot_init_error: Optional[str] = None

# Token de verificación del webhook (configúralo en .env)
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "fundomoraga_2025")

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

    return (len(missing_required) == 0, missing_required, warnings)


def get_bot() -> InstagramBot:
    global _bot, _bot_init_error
    if _bot is not None:
        return _bot
    if _bot_init_error is not None:
        raise RuntimeError(_bot_init_error)

    configured_ok, missing_required, warnings = _config_status()
    if not configured_ok:
        _bot_init_error = (
            "Configuración incompleta. Faltan variables requeridas: "
            + ", ".join(missing_required)
            + ". Configúralas en Railway → Variables y redepliega."
        )
        raise RuntimeError(_bot_init_error)

    try:
        _bot = InstagramBot()
        return _bot
    except Exception as e:
        _bot_init_error = f"Error inicializando bot: {e}"
        raise RuntimeError(_bot_init_error)


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


# ============= INSTAGRAM WEBHOOK =============

@app.route('/webhook/instagram', methods=['GET', 'POST'], strict_slashes=False)
def instagram_webhook():
    """
    Webhook para Instagram/Facebook Messenger.
    GET: verificación inicial del webhook (Meta).
    POST: recepción de mensajes.
    """
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("[OK] Webhook de Instagram verificado")
            return challenge, 200

        print("[ERROR] Webhook de Instagram fallo verificacion")
        return 'Forbidden', 403

    # POST
    data = request.get_json(silent=True) or {}
    print(f"[WEBHOOK] Webhook recibido de Instagram: {data}")

    try:
        bot = get_bot()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 503

    try:
        bot.handle_webhook_message(data)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"[ERROR] Error procesando webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Se requiere el campo 'message'"
            }), 400
        
        # Extraer datos
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', f"web_{request.remote_addr}")
        
        if not user_message:
            return jsonify({
                "error": "El mensaje no puede estar vacío"
            }), 400
        
        # Procesar mensaje con el bot
        try:
            bot = get_bot()
        except Exception as e:
            return jsonify({
                "error": "Servicio no configurado",
                "message": str(e)
            }), 503

        response = bot.process_message(user_id, user_message)

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
