# Guía de Despliegue en Railway - Hernando Bot

## 📋 Requisitos Previos

1. Cuenta en [Railway.app](https://railway.app/)
2. Cuenta de GitHub (opcional, pero recomendado)
3. Credenciales configuradas:
   - Azure Cosmos DB (endpoint y key)
   - OpenAI API key
   - Instagram access token (opcional)

---

## 🚀 Pasos para Desplegar

### Opción 1: Despliegue directo desde GitHub (Recomendado)

1. **Sube tu código a GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Hernando Bot"
   git remote add origin https://github.com/tu-usuario/hernando-bot.git
   git push -u origin main
   ```

2. **En Railway.app**:
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio
   - Railway detectará automáticamente los archivos de configuración

3. **Configurar Variables de Entorno**:
   En el proyecto de Railway, ve a "Variables" y agrega:

   ```
   COSMOS_ENDPOINT=https://fundomoraga.documents.azure.com:443/
   COSMOS_KEY=tu-key-aqui
   COSMOS_DATABASE=Fundo Moraga IA
   COSMOS_CONTAINER=Conversaciones
   
   OPENAI_API_KEY=sk-proj-...
   OPENAI_MODEL=gpt-4o-mini
   
   WEBHOOK_VERIFY_TOKEN=fundomoraga_2025
   BOT_NAME=Hernando
   MAX_CONVERSATION_HISTORY=10
   
   # Instagram (opcional)
   INSTAGRAM_ACCESS_TOKEN=tu-token
   INSTAGRAM_PAGE_ID=tu-page-id
   ```

4. **Desplegar**:
   - Railway desplegará automáticamente
   - Espera a que termine el build
   - URL final (dominio): `https://hernando.fundomoraga.com`

### Opción 2: Despliegue desde CLI

1. **Instalar Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Inicializar proyecto**:
   ```bash
   railway init
   ```

4. **Agregar variables**:
   ```bash
   railway variables set COSMOS_ENDPOINT=https://...
   railway variables set OPENAI_API_KEY=sk-...
   # etc.
   ```

5. **Desplegar**:
   ```bash
   railway up
   ```

---

## 🌐 Configurar Webhook de Instagram

Una vez desplegado, configura el webhook de Instagram:

1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. Selecciona tu app de Instagram
3. En "Webhooks" → "Instagram" → "Edit"
4. **Callback URL**: `https://hernando.fundomoraga.com/webhook/instagram`
5. **Verify Token**: `fundomoraga_2025` (el que configuraste en variables)
6. Suscríbete a: `messages`, `messaging_postbacks`

---

## 💬 Integrar en FundoMoraga.com

### Ejemplo de Widget de Chat Simple

Agrega esto en tu página web:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat con Hernando</title>
    <style>
        #chatbox {
            width: 400px;
            height: 500px;
            border: 1px solid #ccc;
            display: flex;
            flex-direction: column;
            font-family: Arial, sans-serif;
        }
        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            background: #f5f5f5;
        }
        .message {
            margin: 10px 0;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 70%;
        }
        .user-message {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .bot-message {
            background: white;
            color: #333;
        }
        #input-area {
            display: flex;
            padding: 10px;
            border-top: 1px solid #ccc;
        }
        #message-input {
            flex: 1;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        #send-btn {
            margin-left: 8px;
            padding: 8px 16px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div id="chatbox">
        <div id="messages"></div>
        <div id="input-area">
            <input type="text" id="message-input" placeholder="Escribe tu mensaje...">
            <button id="send-btn">Enviar</button>
        </div>
    </div>

    <script>
        const API_URL = 'https://hernando.fundomoraga.com/api/chat';
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        // Generar ID de usuario único
        const userId = 'web_' + Date.now();

        function addMessage(text, isUser) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            msgDiv.textContent = text;
            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Mostrar mensaje del usuario
            addMessage(message, true);
            messageInput.value = '';

            try {
                // Enviar a Hernando
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        message: message
                    })
                });

                const data = await response.json();
                
                // Mostrar respuesta de Hernando
                addMessage(data.response, false);
                
            } catch (error) {
                addMessage('Error: No se pudo conectar con Hernando', false);
                console.error('Error:', error);
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Mensaje de bienvenida
        addMessage('¡Hola! Soy Hernando, asistente del Fundo Moraga. ¿En qué puedo ayudarte?', false);
    </script>
</body>
</html>
```

### Ejemplo con Fetch API (para tu JavaScript existente)

```javascript
// En tu archivo JavaScript de fundomoraga.com
class HernandoChat {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.userId = 'web_' + Date.now();
    }

    async sendMessage(message) {
        try {
            const response = await fetch(`${this.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error al enviar mensaje:', error);
            throw error;
        }
    }

    async getHistory(limit = 10) {
        try {
            const response = await fetch(`${this.apiUrl}/api/chat/history`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    limit: limit
                })
            });

            const data = await response.json();
            return data.history;
        } catch (error) {
            console.error('Error al obtener historial:', error);
            throw error;
        }
    }
}

// Uso
const chat = new HernandoChat('https://hernando.fundomoraga.com');

// Enviar mensaje
const respuesta = await chat.sendMessage('¿Qué eventos puedo realizar en el fundo?');
console.log(respuesta);

// Obtener historial
const historial = await chat.getHistory();
console.log(historial);
```

---

## 🧪 Probar el Despliegue

### 1. Verificar que el servidor esté corriendo:
```bash
curl https://hernando.fundomoraga.com/health
```

Deberías recibir: `{"status": "healthy"}`

### 2. Probar el chat:
```bash
curl -X POST https://hernando.fundomoraga.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola Hernando, ¿cuál es la historia del fundo?"}'
```

### 3. Ver documentación de la API:
Abre en tu navegador:
```
https://hernando.fundomoraga.com/api/docs
```

---

## 📊 Monitoreo en Railway

Railway proporciona automáticamente:
- **Logs**: Ve los logs en tiempo real
- **Métricas**: CPU, memoria, requests
- **Deployments**: Historial de despliegues
- **Variables**: Gestión segura de secrets

---

## 🔧 Solución de Problemas

### Error: "Module not found"
- Verifica que todas las dependencias estén en `requirements.txt`
- Railway ejecuta automáticamente `pip install -r requirements.txt`

### Error: "Connection to Cosmos DB failed"
- Verifica que las variables de entorno estén configuradas correctamente
- Revisa que el endpoint y key sean correctos

### El webhook no funciona
- Verifica que la URL sea accesible públicamente
- Confirma que el verify token coincida con el configurado en Meta

### Bot no responde
- Revisa los logs en Railway
- Verifica que OpenAI API key sea válida y tenga créditos

---

## 🔐 Seguridad

⚠️ **NUNCA** hagas commit de:
- `.env` (está en `.gitignore`)
- API keys
- Connection strings
- Tokens de acceso

✅ Usa siempre las **Variables de Entorno** de Railway

---

## 📚 Recursos

- [Documentación de Railway](https://docs.railway.app/)
- [Instagram Messaging API](https://developers.facebook.com/docs/messenger-platform/instagram)
- [Azure Cosmos DB Docs](https://learn.microsoft.com/azure/cosmos-db/)
- [OpenAI API Docs](https://platform.openai.com/docs/)

---

**¿Necesitas ayuda?**  
Contacto: contacto@fundomoraga.com
