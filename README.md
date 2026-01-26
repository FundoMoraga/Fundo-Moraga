# Chatbot de Instagram - Fundo Moraga 🍒
Chatbot inteligente para Instagram que usa **OpenAI GPT-5.2** para respuestas naturales y **Azure Cosmos DB** para memoria persistente de conversaciones.

## 🎯 Características

- ✅ Respuestas inteligentes con GPT-5.2 (gpt-5.2-2025-12-11)
- ✅ Memoria de conversaciones en Azure Cosmos DB
- ✅ **Conversación natural chilena sin interrogatorio** 🇨🇱
- ✅ **Extracción inteligente de leads** (+130% tasa de captura objetivo)
- ✅ Integración con Instagram Messaging API
- ✅ Validador anti-interrogatorio (máx 2 preguntas consecutivas)
- ✅ Lenguaje chileno natural (cachái, bacán, tinca, piola)
- ✅ Historial de chat por usuario
- ✅ Análisis de sentimiento con Azure Language API
- ✅ Fácil de configurar y desplegar

## 📊 Métricas (Diciembre 2025)

| Métrica | Actual | Meta | Mejora |
|---------|--------|------|--------|
| Tasa de captura de leads | 13% | 30% | +130% |
| Abandono de conversación | 40% | <20% | -50% |
| Sentimiento positivo | 17% | 35% | +106% |

*Basado en análisis de 192 conversaciones reales*

## 🆕 Mejoras Conversacionales (29/12/2025)

### ✨ **Eliminación del "Interrogatorio de la CIA"**

El bot ahora extrae información de forma **natural y entretenida**:

- ❌ **Antes**: "¿Cuántos autos? ¿Qué fecha? ¿Tu nombre?" → 40% abandono
- ✅ **Ahora**: Storytelling + contexto + lenguaje chileno → <20% abandono esperado

### 🇨🇱 **Lenguaje Chileno Natural**

```
Usuario: "Cuánto sale el off-road?"
Bot: "Te cuento, acá hemos tenido grupos desde 2 hasta 10 autos. 
     El precio va en $15.000 por auto, o si van varios podemos 
     ver un pack más piola. ¿Cachái más o menos pa cuántos 
     fierros sería?"
```

Ver documentación completa en:
- [`MEJORAS_CONVERSACIONALES_HERNANDO.md`](MEJORAS_CONVERSACIONALES_HERNANDO.md) - Plan completo
- [`MEJORAS_IMPLEMENTADAS_2025-12-29.md`](MEJORAS_IMPLEMENTADAS_2025-12-29.md) - Implementación técnica
- [`ANALISIS_CONVERSACIONES_HERNANDO_DICIEMBRE.md`](ANALISIS_CONVERSACIONES_HERNANDO_DICIEMBRE.md) - Análisis de 192 conversaciones

## 📋 Requisitos

- Python 3.8+
- Cuenta de Azure con Cosmos DB (capa gratuita disponible)
- API key de OpenAI
- Token de acceso de Instagram/Facebook

## 🚀 Instalación

### 1. Clonar/Descargar el proyecto

```bash
cd "d:\repos\Fundo Moraga\FM IA"
```

### 2. Crear entorno virtual (recomendado)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

1. Copia el archivo de ejemplo:
```powershell
cp .env.example .env
```

2. Edita `.env` con tus credenciales:

```env
# Azure Cosmos DB
COSMOS_ENDPOINT=https://tu-cuenta.documents.azure.com:443/
COSMOS_KEY=tu-primary-key-aqui
COSMOS_DATABASE=chatbot
COSMOS_CONTAINER=conversations

# OpenAI
OPENAI_API_KEY=sk-tu-api-key-aqui
OPENAI_MODEL=gpt-5.2-2025-12-11

# Instagram (opcional para pruebas)
INSTAGRAM_ACCESS_TOKEN=tu-token-aqui
INSTAGRAM_PAGE_ID=tu-page-id-aqui
```

#### 📝 Cómo obtener las credenciales:

**Azure Cosmos DB:**
1. Ve a tu cuenta de Cosmos DB en Azure Portal
2. En el menú izquierdo, selecciona "Keys"
3. Copia "URI" → `COSMOS_ENDPOINT`
4. Copia "PRIMARY KEY" → `COSMOS_KEY`

**OpenAI:**
1. Ve a [platform.openai.com](https://platform.openai.com/)
2. Crea una API key en "API keys"
3. Copia la key → `OPENAI_API_KEY`

**Instagram:**
- Sigue la [guía de Instagram Messaging API](https://developers.facebook.com/docs/messenger-platform/instagram/get-started)

## 🧪 Probar localmente

Una vez configuradas las variables de entorno:

```powershell
python instagram_bot.py
```

Esto iniciará un modo de prueba interactivo donde puedes chatear directamente en la consola. El bot guardará todas las conversaciones en Cosmos DB.

**Ejemplo:**
```
🤖 Fundo Moraga Bot iniciado
==================================================
Modo de prueba - Simula conversaciones
Escribe 'salir' para terminar

Bot: ¡Hola! Soy el asistente virtual de Fundo Moraga Bot...

Tú: ¿Qué frutas tienen disponibles?
Bot: [Respuesta generada por OpenAI]
```

## 📂 Estructura del Proyecto

```
FM IA/
├── config.py              # Configuración y variables de entorno
├── cosmos_client.py       # Cliente de Azure Cosmos DB
├── openai_client.py       # Cliente de OpenAI
├── instagram_bot.py       # Bot principal (lógica de negocio)
├── requirements.txt       # Dependencias de Python
├── .env                   # Variables de entorno (NO subir a Git)
├── .env.example          # Ejemplo de variables de entorno
├── .gitignore            # Archivos a ignorar en Git
└── README.md             # Este archivo
```

## 🔧 Componentes Principales

### `cosmos_client.py`
Gestiona el almacenamiento de conversaciones en Cosmos DB:
- ✅ Guarda mensajes con timestamp
- ✅ Recupera historial por usuario
- ✅ Usa partition key para queries eficientes
- ✅ Sigue best practices de Azure Cosmos DB

### `openai_client.py`
Genera respuestas inteligentes con OpenAI:
- ✅ Usa GPT-5.2 (modelo de última generación)
- ✅ Personalidad configurada para Fundo Moraga
- ✅ Mantiene contexto de conversación

### `instagram_bot.py`
Integra todo:
- ✅ Procesa mensajes de Instagram
- ✅ Mantiene memoria de conversaciones
- ✅ Genera respuestas contextuales
- ✅ Envía respuestas a usuarios

## 🧪 Testing

### Validar mejoras conversacionales:

```bash
python test_mejoras_conversacionales.py
```

Este test valida:
- ✅ Validador de flujo conversacional (detección de interrogatorio)
- ✅ Comparación ANTES vs DESPUÉS de mejoras
- ✅ Patrones de lenguaje chileno
- ✅ Estrategias de extracción natural
- ✅ Métricas objetivo

### Tests adicionales:

```bash
# Test de features avanzadas
python test_advanced_features.py

# Test de conexión a OpenAI
python test_openai_model.py

# Test del validador de flujo solo
python conversation_flow_validator.py
```

## 🌐 Despliegue en Producción

Para conectar con Instagram real:

1. **Configura webhook de Instagram:**
   - Necesitas un servidor público (Azure App Service, Railway, etc.)
   - Configura el webhook en Facebook Developers
   - Verifica el token de verificación

2. **Crea un servidor web** (Flask/FastAPI):
   ```python
   from flask import Flask, request
   from instagram_bot import InstagramBot
   
   app = Flask(__name__)
   bot = InstagramBot()
   
   @app.route('/webhook', methods=['POST'])
   def webhook():
       data = request.get_json()
       bot.handle_webhook_message(data)
       return "OK", 200
   ```

3. **Despliega en la nube**
   - Azure App Service
   - AWS Lambda
   - Google Cloud Run
   - Railway, Heroku, etc.

## 💰 Costos Estimados

Con **5 conversaciones/día**:

| Servicio | Costo Mensual |
|----------|---------------|
| Azure Cosmos DB (Free Tier) | $0.00 |
| OpenAI GPT-5.2 (~50 mensajes/día) | ~$0.50 |
| **Total** | **~$0.50/mes** |

## 🔒 Seguridad

- ⚠️ **NUNCA** subas el archivo `.env` a GitHub
- ✅ Usa `.gitignore` para excluir archivos sensibles
- ✅ Rota las API keys regularmente
- ✅ Usa variables de entorno en producción

## 🐛 Solución de Problemas

### Error: "Failed to connect to Cosmos DB"
- Verifica que `COSMOS_ENDPOINT` y `COSMOS_KEY` sean correctos
- Asegúrate de que la cuenta de Cosmos DB esté activa
- Verifica que el firewall permita conexiones desde tu IP

### Error: "OpenAI API key invalid"
- Verifica que tu API key esté activa en [platform.openai.com](https://platform.openai.com/)
- Asegúrate de tener créditos disponibles en OpenAI

### El bot no responde en Instagram
- Verifica que el webhook esté configurado correctamente
- Revisa los logs del servidor
- Asegúrate de que el token de Instagram sea válido

## 📚 Recursos

- [Azure Cosmos DB Documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Instagram Messaging API](https://developers.facebook.com/docs/messenger-platform/instagram)

## 🤝 Soporte

Para preguntas o problemas, contacta al equipo de desarrollo de Fundo Moraga.

---

**Desarrollado con ❤️ para Fundo Moraga** 🍒
