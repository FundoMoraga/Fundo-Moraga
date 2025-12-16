"""
Servidor web para Hernando - Fundo Moraga
Maneja webhooks de Instagram y chat de la página web
"""
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import config
from instagram_bot import InstagramBot

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde fundomoraga.com

# Inicializar bot
bot = InstagramBot()

# Token de verificación del webhook (configúralo en .env)
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "fundomoraga_2025")


@app.route('/')
def home():
    """Página de inicio: muestra el widget de chat."""
    return render_template('chat_widget.html')


@app.route('/status')
def status():
    """Estado JSON (útil para monitoreo)."""
    return jsonify({
        "bot": "Hernando",
        "status": "online",
        "service": "Fundo Moraga",
        "version": "1.0"
    })


@app.route('/health')
def health():
    """Endpoint de salud para Railway"""
    return jsonify({"status": "healthy"}), 200


# ============= INSTAGRAM WEBHOOK =============

# @app.route('/webhook/instagram', methods=['GET', 'POST'])
# def instagram_webhook():
#     """
#     Webhook para Instagram/Facebook Messenger
#     GET: Verificación inicial del webhook
#     POST: Recepción de mensajes
#     """
    
#     if request.method == 'GET':
#         # Verificación del webhook por parte de Meta
#         mode = request.args.get('hub.mode')
#         token = request.args.get('hub.verify_token')
#         challenge = request.args.get('hub.challenge')
        
#         if mode == 'subscribe' and token == VERIFY_TOKEN:
#             print(f"✅ Webhook de Instagram verificado")
#             return challenge, 200
#         else:
#             print(f"❌ Webhook de Instagram falló verificación")
#             return 'Forbidden', 403
    
#     elif request.method == 'POST':
#         # Procesar mensajes entrantes de Instagram
#         data = request.get_json()
        
#         print(f"📥 Webhook recibido de Instagram: {data}")
        
#         try:
#             bot.handle_webhook_message(data)
#             return jsonify({"status": "ok"}), 200
#         except Exception as e:
#             print(f"❌ Error procesando webhook: {e}")
#             return jsonify({"status": "error", "message": str(e)}), 500


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
        response = bot.process_message(user_id, user_message)

        close_token = "[[CLOSE_CHAT]]"
        close_chat = False
        if isinstance(response, str) and close_token in response:
            close_chat = True
            response = response.replace(close_token, "").strip()
        
        from datetime import datetime, timezone
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bot": "Hernando",
            "close_chat": close_chat
        }), 200
        
    except Exception as e:
        print(f"❌ Error en web chat: {e}")
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

        greeting = bot.start_web_conversation(user_id=user_id)

        from datetime import datetime, timezone
        return jsonify({
            "greeting": greeting,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bot": "Hernando"
        }), 200
    except Exception as e:
        print(f"❌ Error en web chat init: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "message": str(e)
        }), 500


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
        
        # Obtener historial de Cosmos DB
        history = bot.conversation_store.get_conversation_history(
            user_id=user_id,
            limit=limit
        )
        
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
        print(f"❌ Error obteniendo historial: {e}")
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


if __name__ == '__main__':
    # Validar configuración
    try:
        config.validate_config()
        print(f"\n🤖 Hernando - Asistente Virtual de Fundo Moraga")
        print("=" * 60)
        print(f"✅ Configuración válida")
        print(f"📍 Cosmos DB: {config.COSMOS_DATABASE}/{config.COSMOS_CONTAINER}")
        print(f"🤖 Modelo: {config.OPENAI_MODEL}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        exit(1)
    
    # Puerto para Railway (usa la variable de entorno PORT)
    port = int(os.getenv('PORT', 5000))
    
    print(f"\n🚀 Servidor iniciando en puerto {port}")
    print(f"📱 Instagram webhook: /webhook/instagram")
    print(f"💬 Web chat API: /api/chat")
    print(f"📖 Documentación: /api/docs\n")
    
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=port, debug=False)
