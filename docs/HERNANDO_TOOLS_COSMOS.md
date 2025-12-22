# Hernando - Tools (Herramientas) para Cosmos DB

Este documento contiene el JSON con todas las herramientas de Hernando, listo para subir al contenedor **Hernando** en Cosmos DB (DB: Entrenamiento).

**Estructura en Cosmos:**
```
Entrenamiento/
└── Hernando (Contenedor)
    ├── Item: hernando_personalidad_v1.json (✅ Ya subido)
    ├── Item: hernando_operativo_v1.json (🟡 Próximo a subir)
    └── Item: hernando_tools_v1.json (🆕 NUEVO - Este documento)
```

**Partition Key:** `/Categoria`

---

## Item 3: Tools (Herramientas de Hernando)

```json
{
  "id": "hernando_tools_v1",
  "Categoria": "Hernando",
  "type": "tools",
  "version": 1,
  "status": "active",
  "env": "prod",
  "updatedAt": "2025-12-22T12:10:00Z",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "enviar_formulario_contacto",
        "description": "Envía un formulario de contacto al equipo de Fundo Moraga con los datos del usuario para cotizaciones, reservas o consultas",
        "parameters": {
          "type": "object",
          "properties": {
            "nombre": {
              "type": "string",
              "description": "Nombre completo del usuario"
            },
            "email": {
              "type": "string",
              "description": "Email de contacto del usuario"
            },
            "telefono": {
              "type": "string",
              "description": "Número de teléfono del usuario"
            },
            "tipo_solicitud": {
              "type": "string",
              "enum": ["evento", "actividad_offroad", "visita", "produccion", "otro"],
              "description": "Tipo de solicitud: evento, actividad_offroad, visita, produccion, otro"
            },
            "mensaje": {
              "type": "string",
              "description": "Mensaje o consulta del usuario"
            },
            "fecha_tentativa": {
              "type": "string",
              "description": "Fecha tentativa en formatos: YYYY-MM-DD; DD/MM/YYYY; 12 enero 2026 (ejemplo); viernes (preguntar si este viernes o el próximo)"
            }
          },
          "required": ["nombre", "email", "tipo_solicitud", "mensaje"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "buscar_informacion_historica",
        "description": "Busca información específica sobre la historia de la Familia Moraga, eventos históricos, personajes o propiedades",
        "parameters": {
          "type": "object",
          "properties": {
            "tema": {
              "type": "string",
              "enum": [
                "conquista",
                "guerra_arauco",
                "independencia",
                "batalla_chacabuco",
                "rodeo_chileno",
                "hacienda_nancagua",
                "hacienda_chacabuco",
                "fundo_batuco",
                "hernando_moraga",
                "familia_general"
              ],
              "description": "Tema histórico a consultar"
            },
            "detalle": {
              "type": "string",
              "description": "Detalle específico o pregunta sobre el tema"
            }
          },
          "required": ["tema"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "informar_actividades_disponibles",
        "description": "Proporciona información detallada sobre las actividades y servicios disponibles en el Fundo Moraga",
        "parameters": {
          "type": "object",
          "properties": {
            "tipo_actividad": {
              "type": "string",
              "enum": ["eventos", "offroad", "turismo_rural", "produccion_audiovisual", "todas"],
              "description": "Tipo de actividad sobre la que se solicita información"
            },
            "numero_personas": {
              "type": "integer",
              "description": "Número aproximado de personas (opcional)"
            }
          },
          "required": ["tipo_actividad"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "obtener_contactos_oficiales",
        "description": "Proporciona los contactos oficiales de Fundo Moraga según el tipo de consulta",
        "parameters": {
          "type": "object",
          "properties": {
            "motivo": {
              "type": "string",
              "enum": ["cotizacion", "reserva", "consulta_general", "emergencia", "prensa"],
              "description": "Motivo del contacto"
            }
          },
          "required": ["motivo"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "verificar_acceso_fundo",
        "description": "Verifica las condiciones y requisitos para acceder al Fundo Moraga",
        "parameters": {
          "type": "object",
          "properties": {
            "proposito": {
              "type": "string",
              "description": "Propósito de la visita"
            }
          },
          "required": ["proposito"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "capturar_informacion_usuario",
        "description": "Registra información del usuario compartida NATURALMENTE durante la conversación. SOLO usar cuando el usuario haya mencionado voluntariamente su información (nombre, interés, contacto) en el flujo natural del diálogo. NUNCA usar como resultado de preguntas directas tipo interrogatorio.",
        "parameters": {
          "type": "object",
          "properties": {
            "nombre": {
              "type": "string",
              "description": "Nombre completo del usuario si lo mencionó naturalmente en la conversación"
            },
            "interes": {
              "type": "string",
              "description": "Descripción detallada y completa de qué necesita o le interesa al usuario, basándose en TODA la conversación hasta el momento"
            },
            "contacto": {
              "type": "string",
              "description": "Email, teléfono móvil o ambos si el usuario los compartió voluntariamente"
            }
          },
          "required": []
        }
      }
    }
  ]
}
```

---

## Pasos para Subir a Cosmos DB

### Opción 1: Después de Item 2 (Operativo)

1. **En Data Explorer** de Cosmos DB (VS Code o Portal Azure)
2. Click derecho en **Items** del contenedor **Hernando**
3. Selecciona "New Item"
4. Pega el JSON completo de `hernando_tools_v1` arriba
5. Click en "Save" (o presiona Ctrl+Enter)

### Opción 2: Verificar que existan los 3 Items

Después de subir tools, ejecuta esta consulta en el Query Editor de Cosmos DB:

```sql
SELECT c.id, c.type, c.status FROM c WHERE c.Categoria = "Hernando" ORDER BY c.type ASC
```

Resultado esperado:
```
[
  { "id": "hernando_operativo_v1", "type": "operativo", "status": "active" },
  { "id": "hernando_personalidad_v1", "type": "personalidad", "status": "active" },
  { "id": "hernando_tools_v1", "type": "tools", "status": "active" }
]
```

---

## Beneficios de Mover Tools a Cosmos DB

✅ **Centralización**: Toda la configuración de Hernando en un mismo lugar
✅ **Dinamismo**: Actualizar herramientas sin desplegar código
✅ **Versionado**: Fácil mantener múltiples versiones (v1, v2, v3...)
✅ **Escalabilidad**: Si agregamos más bots (Beatriz, Felipe, etc.) cada uno con sus tools propias
✅ **Auditoría**: Historial de cambios en Cosmos DB
✅ **Disponibilidad**: Fallback a tools embebidas en código si DB falla

---

## Próximos Pasos

Después de subir los 3 Items (personalidad, operativo, tools):

1. **Crear un Item "pointer" (opcional)** para simplificar las queries:
   ```json
   {
     "id": "hernando_current",
     "Categoria": "Hernando",
     "type": "pointer",
     "active": {
       "personalidadId": "hernando_personalidad_v1",
       "operativoId": "hernando_operativo_v1",
       "toolsId": "hernando_tools_v1"
     },
     "updatedAt": "2025-12-22T12:10:00Z"
   }
   ```

2. **Actualizar prompts_loader.py** para cargar tools además de prompts:
   - Nueva query: `SELECT * FROM c WHERE c.Categoria = @persona AND c.type IN ("personalidad", "operativo", "tools")`
   - Retornar dict con {personalidad, operativo, tools}

3. **Modificar openai_client.py** para usar tools dinámicas:
   - En `__init__()`: `self.tools = loader.get_prompts()[tools]`
   - En `_generate_with_model()`: pasar `self.tools` a OpenAI

4. **Test y Deploy**:
   ```bash
   python test_prompts_loader.py
   git push origin main
   ```

---

## Estructura de Datos en Cosmos DB (Resumen Final)

```
Entrenamiento (Database)
└── Hernando (Container, PK: /Categoria)
    ├── hernando_personalidad_v1
    │   └── "Eres Hernando, tu anfitrión virtual..."
    ├── hernando_operativo_v1
    │   └── "REGLAS OPERATIVAS (CUMPLIMIENTO ESTRICTO)..."
    ├── hernando_tools_v1 🆕
    │   └── [6 function definitions for OpenAI]
    └── hernando_current (opcional)
        └── { personalidadId, operativoId, toolsId }
```

**Tamaño estimado del contenedor Hernando**: ~500 KB (muy manejable)

---

## Referencia Rápida

| Archivo | Propósito |
|---------|-----------|
| [HERNANDO_PROMPTS_COSMOS.md](HERNANDO_PROMPTS_COSMOS.md) | Personalidad + Operativo |
| [HERNANDO_TOOLS_COSMOS.md](HERNANDO_TOOLS_COSMOS.md) | Tools (este archivo) |
| [hernando_tools.py](../hernando_tools.py) | Implementación de herramientas en código |
| [prompts_loader.py](../prompts_loader.py) | Cargador dinámico desde Cosmos DB |

---

¡La arquitectura dinámica de Hernando está casi lista! 🚀
