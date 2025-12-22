# 🤖 FM IA - Hernando Chatbot with Dynamic Prompt Loading

## ✨ Cambios Principales (Configuración Dinámica de Prompts)

A partir de esta versión, los prompts de Hernando (personalidad y reglas operativas) se **cargan dinámicamente desde Azure Cosmos DB** en lugar de estar embebidos en el código.

### Beneficios
- ✅ **Actualizar prompts sin redeploy**: Cambia los prompts en Cosmos DB, se cargan automáticamente
- ✅ **Caché en memoria**: 60 minutos de TTL para reducir costos de RUs en Cosmos
- ✅ **Fallback automático**: Si Cosmos no responde, usa prompts embebidos como respaldo
- ✅ **A/B Testing**: Versiona múltiples prompts, activando uno a la vez
- ✅ **Exponential Backoff**: Si Cosmos falla, espera 5 minutos antes de reintentar (evita saturación)

---

## 🗂️ Estructura de Cosmos DB

```
Fundo Moraga IA (account)
├── Conversaciones (DB)
│   └── [container]  ← Chat history (PK: /userId)
├── Entrenamiento (DB)
│   ├── Biblioteca (container)  ← Otros prompts de IA (PK: /Categoria)
│   └── Hernando (container)    ← Prompts de Hernando [NUEVO] (PK: /Categoria)
```

### Documentos en `Entrenamiento/Hernando`

Cada documento debe tener esta estructura:

```json
{
  "id": "hernando_personalidad_v1",
  "Categoria": "Hernando",
  "type": "personalidad",  // o "operativo"
  "version": 1,
  "status": "active",      // o "inactive"
  "content": "Eres Hernando, anfitrión virtual de Fundo Moraga...",
  "created": "2025-01-15T10:00:00Z",
  "updated": "2025-01-15T10:00:00Z",
  "notes": "Versión inicial con nueva estructura"
}
```

**Campos críticos:**
- `Categoria`: Siempre `"Hernando"` (debe coincidir con PK)
- `type`: `"personalidad"` o `"operativo"`
- `status`: `"active"` (solo se cargan documentos activos)
- `version`: Número de versión (se cargan en orden DESC, últimas primero)

---

## 📋 Pasos de Configuración

### 1. Crear el Contenedor en Cosmos DB

**Opción A: Using VS Code Cosmos DB Extension**
1. Abre VS Code y ve a la extensión Azure Cosmos DB
2. Conecta tu cuenta fundomoraga.documents.azure.com
3. Crear nuevo contenedor:
   - Database: `Entrenamiento` (ya existe)
   - Container name: `Hernando`
   - Partition key: `/Categoria`
   - Throughput: Shared (default)

**Opción B: Using Azure Portal**
1. Ve a https://portal.azure.com
2. Data Explorer → Entrenamiento → New Container
3. Container ID: `Hernando`
4. Partition Key: `/Categoria`
5. Create

### 2. Subir los Prompts a Cosmos DB

Usa el archivo `docs/HERNANDO_PROMPTS_COSMOS.md` que contiene JSONs listos para copiar:

1. Abre VS Code Cosmos DB Extension
2. Conéctate a `Entrenamiento` → `Hernando`
3. Copia el contenido del Item 1 (personalidad) y crea nuevo item
4. Copia el contenido del Item 2 (operativo) y crea nuevo item
5. Copia el contenido del Item 3 (pointer/optional) si quieres control de versión

O usa el CLI:
```bash
python scripts/cosmos_prompts_inspect.py --db "Entrenamiento" --container "Hernando" --persona "Hernando"
```

### 3. Configurar Variables de Entorno

Copia `.env.example` a `.env` y rellena:

```env
# Cosmos DB - Main (conversations)
COSMOS_ENDPOINT=https://fundomoraga.documents.azure.com:443/
COSMOS_KEY=your_key_here

# Cosmos DB - Prompts [NUEVO]
COSMOS_PROMPTS_DB=Entrenamiento
COSMOS_PROMPTS_CONTAINER=Hernando
COSMOS_PROMPTS_PERSONA=Hernando

# OpenAI [IMPORTANTE: cambió a gpt-4o-mini]
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-xxx
```

### 4. Probar la Integración

```bash
python test_prompts_loader.py
```

Debe mostrar:
```
✅ COSMOS_ENDPOINT: https://fundomoraga.documents.azure.com...
✅ COSMOS_PROMPTS_DB: Entrenamiento
✅ COSMOS_PROMPTS_CONTAINER: Hernando
✅ OPENAI_MODEL: gpt-4o-mini
✅ Loader instanciado (singleton)
✅ System prompt cargado: XXXX caracteres
✅ Operational prompt cargado: XXXX caracteres
✅ ChatbotAI instanciado
```

---

## 🔧 Archivos Clave

### Nuevos/Modificados

| Archivo | Cambio | Descripción |
|---------|--------|-------------|
| `prompts_loader.py` | **NUEVO** | Cargador dinámico de prompts con caché y fallback |
| `config.py` | **MODIFICADO** | Agregadas variables COSMOS_PROMPTS_* y cambió OPENAI_MODEL |
| `openai_client.py` | **MODIFICADO** | Ahora carga prompts dinámicamente usando prompts_loader |
| `.env.example` | **NUEVO** | Plantilla con todas las variables necesarias |
| `test_prompts_loader.py` | **NUEVO** | Script para verificar que todo funciona |

### Referencia

| Archivo | Propósito |
|---------|-----------|
| `docs/HERNANDO_PROMPTS_COSMOS.md` | JSONs listos para pegar en Cosmos DB |
| `scripts/cosmos_prompts_inspect.py` | CLI para inspeccionar prompts en DB |

---

## ⚙️ Comportamiento del Loader

### Caché (60 minutos)
1. Primera llamada → Lee desde Cosmos DB
2. Guardá en caché junto con timestamp
3. Llamadas siguientes en 60 minutos → Usa caché (sin acceso a DB)
4. Pasados 60 minutos → Lee nuevamente de Cosmos DB

### Fallback Automático
- Si Cosmos DB no responde → Usa prompts embebidos en `openai_client.py`
- Si la conexión falla → Marca "unavailable" por 5 minutos (exponential backoff)
- Después de 5 minutos → Reintenta conexión automáticamente

### Logs

```python
📦 Prompts para 'Hernando' obtenidos del caché
✅ Prompts para 'Hernando' cargados desde Cosmos DB
⚠️ Cosmos DB marcado como no disponible por 5 min; usando caché/fallback.
⏭️ Cosmos marcado como no disponible; usando fallback para 'Hernando'
```

---

## 🚀 Despliegue (Railway, Render, etc.)

### Configurar Variables de Entorno

En el panel de tu plataforma (Railway, Render, Heroku, etc.):

```
COSMOS_ENDPOINT=https://fundomoraga.documents.azure.com:443/
COSMOS_KEY=... (tu key)
COSMOS_PROMPTS_DB=Entrenamiento
COSMOS_PROMPTS_CONTAINER=Hernando
COSMOS_PROMPTS_PERSONA=Hernando
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

No necesitas subir los prompts en cada deploy; se cargan dinámicamente de Cosmos DB.

---

## ✅ Checklist de Implementación

- [ ] Crear contenedor `Entrenamiento/Hernando` en Cosmos DB
- [ ] Subir prompts (personalidad + operativo) al contenedor
- [ ] Actualizar `.env` con `COSMOS_PROMPTS_*` variables
- [ ] Ejecutar `python test_prompts_loader.py` y verificar salida
- [ ] Iniciar servidor: `python server.py`
- [ ] Probar chat: enviar mensaje a Instagram/API y verificar respuesta
- [ ] Revisar logs para `✅ Prompts cargados desde Cosmos DB` o `📦 Prompts del caché`

---

## 🔍 Solución de Problemas

### "COSMOS_ENDPOINT/COSMOS_KEY no configurados"
→ Verifica que `COSMOS_ENDPOINT` y `COSMOS_KEY` estén en `.env`

### "Error fetching prompts from Cosmos: [error]"
→ Verifica que el contenedor `Entrenamiento/Hernando` existe y tiene permisos

### "Prompts vacíos o sin contenido"
→ Verifica que los documentos en Cosmos tengan `status="active"`

### Prompts no se actualizan después de cambiar en Cosmos
→ Normal si usa caché. Espera 60 minutos o reinicia el servidor para limpiar caché

---

## 📚 Referencia de Prompts

Los prompts se cargan en este orden:
1. **System Prompt** (Personalidad de Hernando)
   - Quién es Hernando
   - Tono, idioma, identidad
   - Información sobre Fundo Moraga
   
2. **Operational Prompt** (Reglas de comportamiento)
   - Cuándo saludar
   - Cómo capturar leads
   - Cómo manejar agendamientos
   - Límites del bot (qué NO hacer)

Ambos se pasan como `system` role al modelo OpenAI.

---

## 📞 Contacto

Para preguntas sobre la configuración de prompts dinámicos, contacta:
- Email: contacto@fundomoraga.com
- WhatsApp: +5699 9392122
