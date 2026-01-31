# 🚀 RAILWAY - VARIABLES DE ENTORNO RECOMENDADAS

## Variables Críticas (Requeridas)

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Cosmos DB (opción 1: connection string)
COSMOS_CONNECTION_STRING=AccountEndpoint=https://...

# O (opción 2: endpoint + key)
COSMOS_ENDPOINT=https://....documents.azure.com:443/
COSMOS_KEY=...

# Cosmos DB - Configuración
COSMOS_DATABASE=chatbot
COSMOS_CONTAINER=conversations
COSMOS_MEMORY_CONTAINER=Memoria
COSMOS_PROMPTS_DB=Entrenamiento
COSMOS_PROMPTS_CONTAINER=Hernando
```

## Variables Importantes (Alta Prioridad)

```bash
# 🔴 CRÍTICO: Google Analytics
GOOGLE_ANALYTICS_ID=G-TU-ID-REAL    # ← CONFIGURAR AHORA

# 🔴 CRÍTICO: Activar Schedulers
RUN_SCHEDULER_THREAD=true           # ← CONFIGURAR AHORA

# Blog Automation
NEWS_SCHEDULER_ENABLED=true
NEWS_PUBLISH_HOUR=8                 # 08:00 AM Chile
NEWS_CHECK_INTERVAL_MINUTES=30

# Server
PORT=8080
WORKERS=4
GUNICORN_TIMEOUT=60
```

## Variables Opcionales (Features)

```bash
# Email (Resend)
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=contacto@fundomoraga.com

# Instagram
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_PAGE_ID=...

# Google Calendar
GOOGLE_CALENDAR_ID=...
GOOGLE_CALENDAR_CREDENTIALS_JSON=...

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_STORAGE_CONTAINER=assets
AZURE_STORAGE_URL_BASE=https://fundomoragastorage.blob.core.windows.net

# Payment Inbox
PAYMENT_INBOX_USER=...
PAYMENT_INBOX_PASSWORD=...
PAYMENT_INBOX_HOST=...
```

## Variables de Optimización

```bash
# OpenAI Caching
OPENAI_CACHE_TTL_SECONDS=86400      # 24 horas
OPENAI_CACHE_MAX_TOKENS=4000

# Redis (opcional)
REDIS_URL=redis://...

# Logging
LOG_LEVEL=info
DEBUG=false
```

---

## 📋 Checklist de Configuración

### Mínimo para Funcionar
- [x] OPENAI_API_KEY
- [x] COSMOS_ENDPOINT + COSMOS_KEY
- [ ] GOOGLE_ANALYTICS_ID ← **PENDIENTE**
- [ ] RUN_SCHEDULER_THREAD=true ← **PENDIENTE**

### Recomendado
- [ ] NEWS_SCHEDULER_ENABLED=true
- [ ] RESEND_API_KEY (emails)
- [ ] AZURE_STORAGE_CONNECTION_STRING

### Opcional
- [ ] INSTAGRAM_ACCESS_TOKEN
- [ ] GOOGLE_CALENDAR_ID
- [ ] REDIS_URL

---

## 🔧 Cómo Configurar en Railway

1. Ve a tu proyecto en Railway
2. Click en "Variables" (tab lateral)
3. Añade las variables una por una
4. Click "Deploy" para aplicar cambios

**O usa Railway CLI:**
```bash
railway variables set GOOGLE_ANALYTICS_ID=G-TU-ID-REAL
railway variables set RUN_SCHEDULER_THREAD=true
railway up
```

---

## 🎯 Variables Críticas que Debes Configurar AHORA

```bash
# 1. Google Analytics (sin esto no hay métricas)
GOOGLE_ANALYTICS_ID=G-TU-ID-REAL

# 2. Activar schedulers (sin esto el blog no publica)
RUN_SCHEDULER_THREAD=true

# 3. Habilitar publicaciones automáticas
NEWS_SCHEDULER_ENABLED=true
```

**⏱️ Tiempo estimado: 2 minutos**
