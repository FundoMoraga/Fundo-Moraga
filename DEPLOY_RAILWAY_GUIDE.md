# 🚀 Desplegar Hernando a Railway

## Pasos para el Deploy

### 1. Crear Repositorio en GitHub

1. Ve a [github.com/new](https://github.com/new)
2. Nombre: `Fundo-Moraga` (o el que prefieras)
3. **NO inicialices** con README, .gitignore o licencia
4. Haz clic en "Create repository"

### 2. Conectar tu repositorio local con GitHub

Copia y ejecuta los comandos que GitHub te muestra (algo como):

```powershell
git remote add origin https://github.com/ChimiSystems/Fundo-Moraga.git
git branch -M main
git push -u origin main
```

**O si prefieres SSH:**
```powershell
git remote add origin git@github.com:TU-USUARIO/fundo-moraga-chatbot.git
git branch -M main
git push -u origin main
```

### 3. Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway para acceder a tus repositorios
5. Selecciona `Fundo-Moraga`
6. Railway detectará automáticamente Python y empezará a desplegar

### 4. Configurar Variables de Entorno en Railway

En el dashboard de Railway:

1. Click en tu proyecto
2. Ve a la pestaña **"Variables"**
3. Agrega estas variables (copia desde tu `.env`):

```
COSMOS_ENDPOINT=https://fundomoraga.documents.azure.com:443/
COSMOS_KEY=tu-cosmos-key-aqui
COSMOS_DATABASE=Fundo Moraga IA
COSMOS_CONTAINER=Conversaciones

OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=hernando@fundomoraga.com
RESEND_TO_EMAIL=contacto@fundomoraga.com

WEBHOOK_VERIFY_TOKEN=fundomoraga_2025

BOT_NAME=Hernando
MAX_CONVERSATION_HISTORY=10
```

**IMPORTANTE**: No incluyas `INSTAGRAM_ACCESS_TOKEN` ni `INSTAGRAM_PAGE_ID` todavía (las agregaremos después).

Para el **Worker de traducción** en un servicio separado agrega además:
```
AZURE_TRANSLATOR_KEY=tu-key-aqui
AZURE_TRANSLATOR_REGION=southcentralus
AZURE_TRANSLATOR_ENDPOINT=https://hernando.cognitiveservices.azure.com/
START_COMMAND=python translate_worker.py
```

### 5. Verificar el Deploy

1. Railway mostrará los logs del deploy en tiempo real
2. Espera a ver: `✅ Build successful`
3. URL final (dominio): `https://hernando.fundomoraga.com`

### 6. Probar el Deploy

Una vez desplegado, prueba los endpoints:

**Health Check:**
```
https://hernando.fundomoraga.com/health
```

**Chat a página completa (root):**
```
https://hernando.fundomoraga.com/
```

**Widget (burbuja) para embeber en tu web:**
```
https://hernando.fundomoraga.com/widget
```

**Embed (iframes/Canva):**
```
https://hernando.fundomoraga.com/embed
```

**API Docs:**
```
https://hernando.fundomoraga.com/api/docs
```

**Test de Chat (desde terminal o Postman):**
```powershell
curl -X POST https://hernando.fundomoraga.com/api/chat `
  -H "Content-Type: application/json" `
  -d '{"user_id":"test_user","message":"Hola, soy Juan y quiero información sobre eventos corporativos. Mi email es juan@test.com"}'
```

### 7. Configurar Dominio Personalizado (Opcional)

Si quieres usar `chatbot.fundomoraga.com`:

1. En Railway → Settings → Domains
2. Click "Custom Domain"
3. Ingresa: `chatbot.fundomoraga.com`
4. Railway te dará un CNAME
5. Agrégalo en tu DNS:
   ```
   Type: CNAME
   Name: chatbot
   Value: [el CNAME que Railway te da]
   ```

---

## ✅ Checklist de Deploy

- [ ] Repositorio Git inicializado localmente
- [ ] Commit realizado
- [ ] Repositorio GitHub creado
- [ ] Código subido a GitHub
- [ ] Proyecto creado en Railway
- [ ] Railway conectado al repositorio
- [ ] Variables de entorno configuradas en Railway
- [ ] Deploy exitoso
- [ ] `/health` responde OK
- [ ] `/api/docs` muestra la documentación
- [ ] Test de chat funciona
- [ ] Email de lead llega a contacto@fundomoraga.com

---

## 🔄 Próximos Deploys (Actualizaciones)

Una vez configurado, futuras actualizaciones son automáticas:

```powershell
git add .
git commit -m "descripción de los cambios"
git push origin main
```

Railway detectará el push y redesplegará automáticamente.

---

## 📱 Configurar Instagram (Después del Deploy)

1. Define tu dominio público (elige uno):
   - Dominio Railway: `https://<tu-proyecto>.up.railway.app`
   - Dominio propio (opcional): `https://hernando.fundomoraga.com`
2. Ve a [developers.facebook.com](https://developers.facebook.com)
3. Configura el webhook:
   - URL: `https://TU-DOMINIO/webhook/instagram` (reemplaza `TU-DOMINIO` por el dominio real del deploy)
   - Verify Token: el mismo valor de `WEBHOOK_VERIFY_TOKEN` en Railway (por defecto: `fundomoraga_2025`)
   - Suscripciones: `messages`

Notas:
- El verify token es sensible a mayúsculas/minúsculas y no debe llevar espacios.
- Si cambias `WEBHOOK_VERIFY_TOKEN` en Railway, reinicia/redeploy para que tome el nuevo valor.

---

## 🆘 Troubleshooting

**Si el deploy falla:**
- Revisa los logs en Railway
- Verifica que `runtime.txt` tenga `python-3.11.0`
- Confirma que `Procfile` tenga: `web: gunicorn server:app`

**Si los endpoints no responden:**
- Verifica que las variables de entorno estén configuradas
- Revisa que Railway haya asignado el puerto automáticamente
- Chequea los logs para errores

**Si no llegan emails:**
- Verifica la variable `RESEND_API_KEY` en Railway
- Confirma que el dominio esté verificado en Resend
- Revisa los logs del bot
