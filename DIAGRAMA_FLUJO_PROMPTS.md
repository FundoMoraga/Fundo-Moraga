# 🔄 Diagrama del Flujo de Carga de Prompts

## Vista General del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                      HERNANDO CHATBOT                           │
│                  (openai_client.ChatbotAI)                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 └──> __init__()
                      │
                      ├─> from prompts_loader import get_prompts_loader
                      │
                      └─> loader.get_prompts(persona="Hernando", fallback_*)
                           │
                           └─┬──────────────────────────────────────┐
                             │                                      │
                             ▼                                      ▼
                 ┌─────────────────────┐          ┌────────────────────────┐
                 │ CACHÉ EN MEMORIA    │          │  COSMOS DB             │
                 │ (60 min TTL)        │          │  Entrenamiento/Hernando│
                 │                     │          │  (PK: /Categoria)      │
                 │ ✓ Rápido            │          │                        │
                 │ ✓ Sin costo RU      │          │ Docs:                  │
                 │ ✓ Siempre disponible│          │ - personalidad (v1)    │
                 └─────────────────────┘          │ - operativo (v1)       │
                             ▲                     │ - etc.                 │
                             │                     └────────────────────────┘
                             │                              ▲
                    ┌────────┘                              │
                    │                                        │
              Pasados 60 min ─────────────────────────────────
              o primer acceso
```

## Flujo de Carga (En Detalle)

```
┌──────────────────────────────────────────────────────────────┐
│  ChatbotAI.__init__()                                        │
└──┬────────────────────────────────────────────────────────────┘
   │
   ├─ get_prompts_loader() ─┐
   │  (Singleton)           │ Retorna única instancia de PromptsLoader
   │                        │
   └─────────────────────────────────────────┐
                                              │
                        ┌─────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │ loader.get_prompts()             │
         │ ("Hernando", fallback_*, ...)    │
         └──┬───────────────────────────────┘
            │
            ├─ ¿Caché válido? (< 60 min) ──────┐
            │ SI: Retorna caché                  │
            │ NO: Continúa                       │
            │                                    │
            └─ ¿Cosmos marcado unavailable?─────┐
              (dentro de 5 min backoff)         │
              SI: Usa fallback                   │
              NO: Intenta conexión               │
                                                 │
            ┌─────────────────────────────────────
            │
            ├─ Conectar a Cosmos DB ──────────┐
            │                                   │
            │ if COSMOS_ENDPOINT && COSMOS_KEY │
            │    CosmosClient(endpoint, key)   │
            │                                   │
            └────────────────────┬─────────────┘
                                 │
                                 ▼
            ┌────────────────────────────────┐
            │ db.get_database_client()       │
            │ cont.get_container_client()    │
            └──┬─────────────────────────────┘
               │
               ▼
   Query:
   SELECT c.type, c.content
   FROM c
   WHERE c.Categoria = "Hernando"
     AND c.status = "active"
   ORDER BY c.version DESC
               │
               ├─ Documento type="personalidad" ──> system_prompt
               └─ Documento type="operativo"   ──> operational_prompt
                                                │
                                    ┌───────────┘
                                    │
                                    ├─ Éxito: Guarda en caché (TTL 60 min)
                                    │          Retorna {"system": "...", "operational": "..."}
                                    │
                                    └─ Error: Marca Cosmos unavailable (5 min backoff)
                                               Retorna fallback embebido


FALLBACK (Si Cosmos falla):
{
  "system": "Eres Hernando, anfitrión virtual de Fundo Moraga...",
  "operational": "Sé proactivo. Pide datos para reservar..."
}
```

## Caché y TTL

```
Inicio            Minuto 1         Minuto 30        Minuto 60        Minuto 61
  │                 │                  │                │                 │
  ├─ DB request     ├─ Usa caché      ├─ Usa caché    ├─ Usa caché      ├─ CACHÉ EXPIRÓ
  ├─ Guarda caché   │                  │                │                 │
  │ _cache = {...}  │                  │                │                 ├─ DB request
  │ _last_cache =   │                  │                │                 ├─ Caché refrescado
  │   datetime.now()│                  │                │                 │
  │ TTL = 60 min    │                  │                │                 │
  │                 │                  │                │                 │
  └─────────────────┴──────────────────┴────────────────┴─────────────────┘
        Caché válido (< 60 min) ──────────────────────────► Caché inválido
                                                            (> 60 min)
```

## Exponential Backoff (Error Handling)

```
Solicitud 1 (OK)
  └─> Conecta a Cosmos DB ✓
      Obtiene prompts ✓
      Guarda caché ✓

Solicitud 2 (Cosmos DOWN)
  └─> Intenta conectar a Cosmos DB ✗
      ERROR: Connection refused
      └─> _mark_cosmos_unavailable(backoff_minutes=5)
          _cosmos_unavailable_until = NOW + 5 min
      └─> Retorna fallback

Solicitudes 3-5 (mientras unavailable < 5 min)
  └─> Verifica: ¿_cosmos_unavailable_until < NOW?
      NO → Retorna fallback (sin intentar DB)
      └─> Evita golpeteo a DB caída

Solicitud 6 (después de 5 min)
  └─> Verifica: ¿_cosmos_unavailable_until < NOW?
      SÍ → _cosmos_unavailable_until = None
      └─> Reintenta conexión a Cosmos DB
          Si Cosmos está OK: Carga prompts
          Si sigue caído: Vuelve a esperar 5 min
```

## Flujo Completo: Primer Mensaje de Usuario

```
USER envia mensaje:
  "Hola, quiero agendar una visita"
       │
       ▼
instagram_bot.process_message()
       │
       ├─ Obtiene ChatbotAI singleton ────────┐
       │ get_chatbot_ai()                      │
       │                                       │
       └────────┬──────────────────────────────┘
                │
                ├─ Si es primera vez:
                │  __init__() se ejecuta UNA SOLA VEZ
                │  └─> loader.get_prompts() (acceso a Cosmos)
                │      ✓ Caché guardado
                │      ✓ self.system_prompt = {...}
                │      ✓ self.operational_prompt = {...}
                │
                └─ generate_response(user_message)
                   │
                   ├─ _build_messages():
                   │  ├─ messages.append({"role": "system", "content": self.system_prompt})
                   │  ├─ messages.append({"role": "system", "content": "CONTEXTO..."})
                   │  └─ messages.append({"role": "system", "content": self.operational_prompt})
                   │
                   └─ OpenAI API call:
                      POST https://api.openai.com/v1/chat/completions
                      model: gpt-4o-mini
                      messages: [system, system, system, user]
                      tools: [6 herramientas]
                      │
                      └─> Response: "Hola, me encantaría ayudarte..."
                          (Contiene respuesta generada con prompts dinámicos)
```

## Archivo de Configuración (.env)

```
┌────────────────────────────────┐
│        ARCHIVO .env            │
├────────────────────────────────┤
│                                │
│ COSMOS_ENDPOINT                │
│ COSMOS_KEY                     │  ────┐
│ COSMOS_DATABASE (conversaciones)│      │
│ COSMOS_CONTAINER (chats)       │      │
│                                │      │ Usado por:
│ COSMOS_PROMPTS_DB             │      │ - conversación (Conversaciones)
│ COSMOS_PROMPTS_CONTAINER      │      │ - prompts (Entrenamiento/Hernando)
│ COSMOS_PROMPTS_PERSONA        │      │
│                                │      │
│ OPENAI_API_KEY                │      │ Usado por:
│ OPENAI_MODEL=gpt-4o-mini      │      │ - openai_client.py
│                                │      │
│ INSTAGRAM_ACCESS_TOKEN        │ ────┘
│ GOOGLE_CALENDAR_ID            │
│ ... más variables ...          │
└────────────────────────────────┘
```

## Estructura de Cosmos DB

```
fundomoraga.documents.azure.com (Cuenta)
│
├─ DATABASE: Fundo Moraga IA
│  ├─ CONTAINER: Conversaciones (PK: /userId)
│  │  └─ Documentos: {...} (chat history)
│  │
│  └─ DATABASE: Entrenamiento
│     ├─ CONTAINER: Biblioteca (PK: /Categoria)
│     │  └─ Documentos: Corporativo, Marketing, Médico, etc.
│     │
│     └─ CONTAINER: Hernando (PK: /Categoria) [NUEVO]
│        └─ Documentos:
│           ├─ {
│           │    "id": "hernando_personalidad_v1",
│           │    "Categoria": "Hernando",
│           │    "type": "personalidad",
│           │    "version": 1,
│           │    "status": "active",
│           │    "content": "Eres Hernando..."
│           │  }
│           │
│           └─ {
│                "id": "hernando_operativo_v1",
│                "Categoria": "Hernando",
│                "type": "operativo",
│                "version": 1,
│                "status": "active",
│                "content": "REGLAS OPERATIVAS..."
│              }
```

## Logs Esperados

```
Primer inicio (caché vacío):
  ✅ Prompts para 'Hernando' cargados desde Cosmos DB
  📦 Sistema listo

Llamadas siguientes (dentro de 60 min):
  📦 Prompts para 'Hernando' obtenidos del caché
  (sin acceso a DB)

Si Cosmos falla:
  ❌ Error fetching prompts from Cosmos: [error]
  ⚠️ Cosmos DB marcado como no disponible por 5 min; usando caché/fallback.
  ⏭️ Cosmos marcado como no disponible; usando fallback para 'Hernando'
  (continúa con prompts embebidos)

Después de 5 min, reintento automático:
  ✅ Prompts para 'Hernando' cargados desde Cosmos DB
  (Cosmos vuelve a estar disponible)
```

---

**Resumen: El sistema es resiliente, eficiente y escalable. ✨**
