# 🤖 Hernando Orquestador Elite de Herramientas

## Descripción General

Hernando ha sido transformado en un **Orquestador Elite de Herramientas** capaz de acceder y utilizar TODOS los 10 servicios disponibles en la plataforma Railway de Fundo Moraga.

Este sistema permite que Hernando:
- 🎯 Identifique automáticamente qué servicio necesita usar
- 🔄 Delegue tareas a servicios especializados
- 📊 Sintetice resultados en respuestas coherentes
- 🚀 Escale su capacidad sin límites

## Arquitectura de Servicios

### Los 10 Servicios Railway

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HERNANDO ORQUESTADOR ELITE                      │
└─────────────────────────────────────────────────────────────────────┘
     ↓              ↓              ↓              ↓              ↓
┌─────────┐   ┌─────────────┐  ┌────────────┐  ┌──────────┐  ┌──────┐
│Traductor│   │   Lenguaje  │  │Vision-Svc  │  │ WAHA/WA  │  │Redis │
│Azure    │   │Azure Lang   │  │Computer V  │  │WhatsApp  │  │Cache │
└─────────┘   └─────────────┘  └────────────┘  └──────────┘  └──────┘
     ↓              ↓              ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌───────────┐ ┌─────────┐
│Steel Browser │ │  Mensajería  │ │Cosmos DB │ │Web Frontend│ │Storage │
│Web Scraping  │ │Email/Alerts  │ │NoSQL DB  │ │Información│ │Archivos│
└──────────────┘ └──────────────┘ └──────────┘ └───────────┘ └─────────┘
```

### Detalle de Servicios

| # | Servicio | Función Principal | Capacidades | Estado |
|---|----------|------------------|------------|--------|
| 1 | **Hernando** | Main Bot | Orquestación, conversación | ✅ |
| 2 | **Traductor** | Azure Translator | Traducir a 100+ idiomas | ⚠️ Requiere config |
| 3 | **Lenguaje** | Azure Language | Sentimiento, entidades, frases | ⚠️ Requiere config |
| 4 | **Vision Service** | Computer Vision | OCR, objetos, imágenes | ✅ |
| 5 | **WhatsApp (WAHA)** | Mensajería | Enviar/recibir mensajes | ⚠️ Requiere config |
| 6 | **Redis** | Cache | Sesiones, caché rápida | ✅ |
| 7 | **Steel Browser** | Web Navigation | Scraping, investigación | ✅ |
| 8 | **Mensajería** | Email/SMS | Notificaciones, alertas | ✅ |
| 9 | **Cosmos DB** | Database | Persistencia, memoria | ⚠️ Requiere config |
| 10 | **Web Fundo** | Frontend | Info pública, reservas | ✅ |

## Nuevas Herramientas (Tools) Elite

### 1. `listar_servicios_disponibles`

**Descripción:** Lista todos los servicios Railway y sus capacidades.

**Parámetros:**
- `filtro` (enum): `"activos"` | `"todos"` | nombre del servicio específico
- `con_detalles` (bool): Incluir URLs y capacidades completas

**Ejemplo de Uso:**
```
Usuario: "¿Qué herramientas tienes disponibles?"
→ Hernando: "Tengo acceso a 10 servicios especializados..."
```

**Respuesta:**
```json
{
  "total": 10,
  "activos": 6,
  "servicios": [
    {
      "id": "hernando",
      "nombre": "Hernando Bot",
      "disponible": true,
      "url": "http://hernando.railway.internal:8000",
      "capacidades": ["orquestación", "conversación", "coordinación"]
    },
    ...
  ]
}
```

### 2. `verificar_salud_servicios`

**Descripción:** Health checks a todos los servicios. Verifica qué está operativo.

**Parámetros:**
- `timeout` (int): Segundos de espera máxima para cada servicio (default: 5)

**Ejemplo de Uso:**
```
Usuario: "¿Están todos los servicios funcionando?"
→ Hernando ejecuta health checks a los 10 servicios
→ Retorna estado individual + resumen
```

**Respuesta:**
```json
{
  "timestamp": "2024-12-16T10:30:00Z",
  "servicios": {
    "hernando": {
      "nombre": "Hernando Bot",
      "estado": "operativo",
      "tiempo_respuesta_ms": 45.2
    },
    ...
  },
  "resumen": {
    "operativos": 6,
    "fallos": 3,
    "no_verificados": 1
  }
}
```

### 3. `consultar_servicio_railway`

**Descripción:** Acceso genérico a cualquier endpoint de servicio Railway.

**Parámetros:**
- `servicio` (string): Nombre del servicio
- `endpoint` (string): Ruta del endpoint (ej: `/api/translate`)
- `metodo` (enum): `"GET"` | `"POST"` | `"PUT"` | `"DELETE"`
- `datos` (object): Datos para POST/PUT
- `parametros` (object): Parámetros de query

**Ejemplo de Uso:**
```
Usuario: "Consulta el endpoint /api/stats del servicio lenguaje"
→ Hernando: 
  consultar_servicio_railway(
    servicio="lenguaje",
    endpoint="/api/stats",
    metodo="GET"
  )
```

## Casos de Uso - Ejemplos de Orquestación

### Caso 1: Traducción Inteligente

```
Usuario: "Traduce esto al inglés"
Mensaje: "Hola amigo, ¿cómo estás?"

→ Hernando identifica: Necesita Traductor
→ Usa herramienta: traducir_texto()
→ Servicio: Traductor (Azure)
→ Respuesta: "Hello friend, how are you?"
```

### Caso 2: Análisis de Sentimiento con Contexto

```
Usuario: "¿Qué tan positivo es este feedback?"
Feedback: "El producto es increíble, pero el envío fue lentísimo"

→ Hernando identifica: Necesita análisis de sentimiento + lenguaje
→ Usa herramientas:
   - analizar_sentimiento_texto() → Traductor
   - extraer_frases_clave() → Lenguaje
→ Servicios: Lenguaje + Traductor
→ Respuesta: "Sentimiento MIXTO: positivo en producto (8/10), 
            negativo en logística (3/10)"
```

### Caso 3: Investigación Web + Análisis de Imágenes

```
Usuario: "Busca fotos de 'Jeep Wrangler 2024' y analízalas"

→ Hernando identifica: Necesita búsqueda web + análisis visual
→ Usa herramientas:
   1. buscar_imagenes() → Steel Browser + Vision Service
   2. analizar_imagen_academico() → Vision Service (por cada imagen)
→ Servicios: Steel Browser + Vision Service
→ Respuesta: [análisis detallado de 10 imágenes con descripciones]
```

### Caso 4: Consulta Directa a Servicio Específico

```
Usuario: "Quiero hacer una consulta POST al servicio de Lenguaje
          con datos específicos"

→ Hernando usa:
   consultar_servicio_railway(
     servicio="lenguaje",
     endpoint="/api/analyze",
     metodo="POST",
     datos={...datos complejos...}
   )
→ Retorna: Respuesta directa del servicio
```

## Configuración de Variables de Entorno

Para que los servicios funcionen correctamente, necesitan estar configurados en Railway:

### Traductor
```
TRANSLATOR_SERVICE_URL=http://traductor.railway.internal:5000
AZURE_TRANSLATOR_KEY=<key>
```

### Lenguaje
```
LANGUAGE_SERVICE_URL=http://lenguaje.railway.internal:5000
AZURE_LANGUAGE_KEY=<key>
```

### Vision Service
```
VISION_SERVICE_URL=http://vision-service.railway.internal:5000
AZURE_VISION_KEY=<key>
```

### WhatsApp (WAHA)
```
WAHA_API_URL=http://waha.railway.internal:3000
WAHA_API_KEY=<key>
```

### Cosmos DB
```
COSMOS_ENDPOINT=https://cosmos.railway.internal
COSMOS_KEY=<key>
```

## Uso desde hernando_bot.py

El sistema de Elite Orchestrator está integrado automáticamente en `hernando_bot.py`.

Cuando OpenAI Function Calling selecciona una de las herramientas Elite:

```python
# En execute_tool() de hernando_tools.py
if tool_name == "listar_servicios_disponibles":
    return self.listar_servicios_disponibles(...)

if tool_name == "verificar_salud_servicios":
    return self.verificar_salud_servicios(...)

if tool_name == "consultar_servicio_railway":
    return self.consultar_servicio_railway(...)
```

## Flujo de Selección de Herramientas

```
┌──────────────────────────────────┐
│   Usuario escribe mensaje        │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│ Hernando procesa con GPT         │
│ - Entiende la necesidad          │
│ - Selecciona herramienta(s)      │
└──────────────┬───────────────────┘
               ↓
        ┌──────┴──────┬──────────┬──────────┐
        ↓             ↓          ↓          ↓
    ┌───────┐   ┌──────────┐  ┌────────┐ ┌──────────┐
    │Base   │   │Language  │  │Privadas│ │Elite     │
    │Tools  │   │Tools     │  │Tools   │ │Orchestr. │
    └───────┘   └──────────┘  └────────┘ └──────────┘
        │             │            │          │
        └─────────────┴────────────┴──────────┘
               ↓
┌──────────────────────────────────┐
│ Ejecutar herramienta(s)          │
│ (puede usar múltiples servicios) │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│ Sintetizar resultado             │
│ en respuesta coherente           │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│ Respuesta al usuario             │
└──────────────────────────────────┘
```

## Autorización

El sistema de Elite Orchestrator está configurado para:

- **Usuarios Normales**: Acceso a herramientas públicas
- **Usuarios Admin (Efraín Moraga)**: Acceso COMPLETO a:
  - Herramientas base
  - Herramientas privadas
  - Herramientas de lenguaje
  - Herramientas de visión
  - Herramientas web
  - **Herramientas Elite Orchestrator** ← TODAS

## Testing

Se incluyen dos scripts de prueba:

### `test_services_config.py`
Valida que los 10 servicios estén correctamente configurados.

```bash
python test_services_config.py
```

Salida esperada:
```
Total de servicios configurados: 10
Resumen: 6/10 servicios disponibles (con configs)
[SUCCESS] Configuracion de servicios validada
```

### `test_elite_orchestrator.py`
Test completo (requiere Cosmos DB configurado).

```bash
python test_elite_orchestrator.py
```

## Proximos Pasos

1. ✅ **Implementación Base**: Sistema Elite Orchestrator creado
2. ⚠️ **Configuración de Servicios**: Completar variables de entorno en Railway
3. 🔄 **Testing End-to-End**: Probar con cada servicio real
4. 📊 **Optimización**: Caching de capabilities, inteligencia mejorada
5. 📈 **Escalamiento**: Agregar más servicios según necesidad

## Arquitectura Técnica

### En `hernando_tools.py`:

1. **RAILWAY_SERVICES** (dict): Registro central de servicios
   - 10 servicios definidos
   - URLs, capabilities, estado de disponibilidad
   - Fallbacks automáticos

2. **Clase HernandoTools**:
   - Métodos de Elite Orchestrator
   - Integración con OpenAI Function Calling
   - Manejo de errores robusto

3. **Herramientas registradas**:
   - `listar_servicios_disponibles()`
   - `verificar_salud_servicios()`
   - `consultar_servicio_railway()`

### En `hernando_bot.py`:

- Acceso automático a todas las herramientas
- Selección inteligente según contexto
- Sintetización de resultados

## Seguridad

- ✅ Validación de servicios permitidos
- ✅ Timeouts configurables
- ✅ Manejo de excepciones
- ✅ Logging de operaciones
- ✅ Autorización por usuario

## Conclusión

Hernando ahora es un **Sistema Inteligente de Orquestación** capaz de:

1. 🎯 Entender qué necesita cada usuario
2. 🔄 Seleccionar el servicio más apropiado
3. 🚀 Ejecutar operaciones complejas
4. 📊 Sintetizar resultados
5. ⚡ Escalar sin límites usando los 10 servicios Railway

**¡Hernando está listo para ser el Orquestador Elite de Fundo Moraga!** 🤖🚀
