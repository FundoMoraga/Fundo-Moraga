To embed the chat widget on your Canva website using CodePen, follow these steps:

1.  **Open CodePen:** Go to [https://codepen.io/pen](https://codepen.io/pen)
2.  **Copy and paste the code:** In the CodePen editor, you will see three sections: HTML, CSS, and JS.
    *   Copy the HTML code below and paste it into the HTML section of CodePen.
    *   Copy the CSS code below and paste it into the CSS section of CodePen.
    *   Copy the JavaScript code below and paste it into the JS section of CodePen.
3.  **Save the Pen:** Click on the "Save" button in CodePen.
4.  **Embed the Pen on your website:**
    *   Click on the "Embed" button in the bottom right corner of the CodePen editor.
    *   Copy the HTML code provided and paste it into your Canva website.

**HTML Code:**
```html
<div id="chatbox">
    <div id="chat-header">Chat con Hernando</div>
    <div id="messages"></div>
    <div id="input-area">
        <input type="text" id="message-input" placeholder="Escribe tu mensaje...">
        <button id="send-btn" aria-label="Enviar">➔</button>
    </div>
</div>
```

**CSS Code:**
```css
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');

body {
    margin: 0;
    font-family: 'Nunito', sans-serif;
    background-color: #f7f9fc;
}
#chatbox {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    background-color: #ffffff;
}
#chat-header {
    background: #007bff;
    color: white;
    padding: 1rem;
    text-align: center;
    font-weight: 700;
    font-size: 1.1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    z-index: 10;
}
#messages {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
.message {
    padding: 0.75rem 1.25rem;
    border-radius: 22px;
    max-width: 80%;
    line-height: 1.5;
    word-wrap: break-word;
}
.user-message {
    background-image: linear-gradient(to right, #007bff, #0056b3);
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 6px;
}
.bot-message {
    background: #e9e9eb;
    color: #2c2c2c;
    align-self: flex-start;
    border-bottom-left-radius: 6px;
}
#input-area {
    display: flex;
    align-items: center;
    padding: 1rem;
    border-top: 1px solid #e0e0e0;
    background: #ffffff;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}
#message-input {
    flex: 1;
    padding: 0.75rem 1.25rem;
    border: 1px solid #ccc;
    border-radius: 25px;
    font-family: 'Nunito', sans-serif;
    font-size: 1rem;
    transition: border-color 0.2s;
}
#message-input:focus {
    outline: none;
    border-color: #007bff;
}
#send-btn {
    margin-left: 0.75rem;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    cursor: pointer;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s;
}
#send-btn:hover {
    background: #0056b3;
}
#send-btn:disabled {
    background: #a0a0a0;
    cursor: not-allowed;
}
```

**JavaScript Code:**
```javascript
const API_URL = 'https://fm-ia.up.railway.app/api/chat';
const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

const userId = 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

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

    addMessage(message, true);
    messageInput.value = '';
    sendBtn.disabled = true;

    try {
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

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        addMessage(data.response, false);
        
    } catch (error) {
        addMessage('Error: No se pudo conectar con Hernando. Inténtalo de nuevo más tarde.', false);
        console.error('Error:', error);
    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

// Simular un mensaje de bienvenida del bot
setTimeout(() => {
    addMessage('¡Hola! Soy Hernando, tu asistente virtual del Fundo Moraga. ¿En qué puedo ayudarte hoy?', false);
}, 500);

messageInput.focus();
```
In the Javascript code, I have replaced the `API_URL` with the Railway production URL. You can find this URL in your Railway project dashboard. Make sure to replace `'https://fm-ia.up.railway.app/api/chat'` with your actual production URL.
