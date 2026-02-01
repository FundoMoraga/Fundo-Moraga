# 🚀 Automatización de Blog Multi-Categoría - Implementación Completa

## 📋 Resumen Ejecutivo

Se ha implementado un sistema **completamente automatizado** de publicación diaria de artículos del blog de Fundo Moraga con las siguientes características:

✅ **5+ Artículos diarios** (mínimo 1 por categoría)
✅ **Contenido variado** (tópicos rotados por categoría)  
✅ **Mínimo 1500 caracteres** por artículo
✅ **Categorización automática** (historia, guías, rutas, eventos, noticias)
✅ **Publicación diaria** a las 08:00 AM (Zona horaria Chile)
✅ **Salvaguarda en Cosmos DB** para auditoría y análisis

---

## 🏗️ Arquitectura del Sistema

### 1. **Pipeline de Generación** (news_aggregator.py)

#### Método `create_daily_digest()`
```
┌─────────────────────────────────────────┐
│ 1. Fetch headlines (todas las fuentes)  │
│    → ~50 títulos de múltiples sources   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 2. Loop a través de 5 categorías        │
│    ├── historia                         │
│    ├── guías                            │
│    ├── rutas                            │
│    ├── eventos                          │
│    └── noticias                         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 3. Para cada categoría:                 │
│    - Generar artículo específico        │
│    - Rotar tópicos (5 por categoría)    │
│    - Aplicar prompt prefix personalizado│
│    - Validar 1500+ caracteres          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. Retornar digest con 5+ artículos    │
│    (estructura: articles[])             │
└─────────────────────────────────────────┘
```

#### Método `generate_article_by_category()`
- **Entrada**: headlines, category, topic_index
- **Rotación de tópicos**: `topic = topics[topic_index % len(topics)]`
- **Prompt personalizado**: Cada categoría tiene su `prompt_prefix`
- **Salida**: Artículo JSON con:
  - `title`, `subtitle`, `slug`
  - `content_html` (1500+ caracteres)
  - `category`, `keywords`, `reading_time_minutes`

#### Configuración de Categorías (BLOG_CATEGORIES)
```python
BLOG_CATEGORIES = {
    "historia": {
        "topics": ["Rodeos chilenos", "Tradición 4x4", "Historia off-road", "Vehículos clásicos", "Cultura aventurera"],
        "prompt_prefix": "Enfócate en la historia y tradición del 4x4 en Chile..."
    },
    "guías": {
        "topics": ["Preparación de vehículos", "Equipo esencial", "Técnicas de conducción", "Mantenimiento 4x4", "Seguridad off-road"],
        "prompt_prefix": "Crea una guía práctica y detallada..."
    },
    "rutas": {
        "topics": ["Ruta Atacama", "Ruta Patagonia", "Senderos Chile Central", "Rutas costeras", "Circuitos Andes"],
        "prompt_prefix": "Describe rutas específicas con detalles GPS..."
    },
    "eventos": {
        "topics": ["Competencias 4x4", "Off-road adventure", "Rally técnico", "Experiencias corporativas", "Tours guiados"],
        "prompt_prefix": "Enfócate en beneficios corporativos..."
    },
    "noticias": {
        "topics": ["Lanzamientos de vehículos", "Cambios normativas", "Tendencias 4x4", "Nuevas tecnologías", "Eventos industria"],
        "prompt_prefix": "Escribe un artículo de noticias..."
    }
}
```

### 2. **Pipeline de Publicación** (news_scheduler.py)

#### Método `_generate_and_publish()` - ACTUALIZADO
```
┌──────────────────────────────────────┐
│ 1. Crear digest multi-categoría      │
│    → news_aggregator.create_daily_digest()
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│ 2. Extraer articles[] del digest     │
│    → 5+ artículos generados          │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│ 3. Para cada artículo:               │
│    - publisher.publish_article()      │
│    - Guardar en Cosmos DB             │
│    - Generar archivo HTML             │
│    - Actualizar índice del blog       │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│ 4. Reporte final                     │
│    - Exitosas: X/5                   │
│    - Fallidas: Y/5                   │
│    - URLs de los artículos           │
└──────────────────────────────────────┘
```

#### Ejecución Automática
- **Trigger**: 08:00 AM (Zona Horaria Chile)
- **Intervalo de verificación**: Cada 30 minutos
- **Evita duplicados**: Usa flag `_last_publish_date` 
- **Runs as daemon thread**: Background en `server.py`

---

## 🎯 Cambios Realizados

### news_aggregator.py

**1. Added BLOG_CATEGORIES Dictionary**
```python
BLOG_CATEGORIES = {
    "historia": {"topics": [...], "prompt_prefix": "..."},
    "guías": {"topics": [...], "prompt_prefix": "..."},
    "rutas": {"topics": [...], "prompt_prefix": "..."},
    "eventos": {"topics": [...], "prompt_prefix": "..."},
    "noticias": {"topics": [...], "prompt_prefix": "..."}
}
```

**2. New Method: generate_article_by_category()**
- Genera artículos específicos por categoría
- Rota tópicos para variedad
- Aplica prompts personalizados
- Retorna JSON con estructura de artículo

**3. Updated: create_daily_digest()**
- ❌ Antes: Retornaba un solo artículo genérico
- ✅ Ahora: Genera y retorna 5+ artículos (uno por categoría)
- Estructura: `{"articles": [article1, article2, ...], "articles_count": 5}`

### news_scheduler.py

**1. Updated: _generate_and_publish()**
- ❌ Antes: Publicaba un artículo único
- ✅ Ahora: Itera sobre `articles[]` del digest
- Publica cada artículo con contador de éxito/fallo
- Reporte final con estadísticas

---

## 📊 Flujo Completo (Diagrama de Secuencia)

```
HORA: 08:00 AM Chile
┌─────────────────────────────────────────────────┐
│ news_scheduler.py (_run_once_if_needed)         │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ if _is_time_to_publish()
┌─────────────────────────────────────────────────┐
│ _generate_and_publish()                         │
│ ├─ Get headlines (BBC, El País, etc)            │
│ ├─ Create digest with 5+ articles              │
│ └─ For each article: publish_article()         │
└────────────────┬────────────────────────────────┘
                 │
                 ├─► historia-[slug].html
                 ├─► guias-[slug].html
                 ├─► rutas-[slug].html
                 ├─► eventos-[slug].html
                 └─► noticias-[slug].html
                 
                 ├─► Web/blog/articulos/[files]
                 ├─► Web/blog/index.html (updated)
                 └─► Cosmos DB (saved)
```

---

## ✅ Validación del Sistema

### Test Manual: Ejecutar Publicación Inmediata
```bash
# Ejecutar publicación ahora (sin esperar 08:00)
python news_scheduler.py --now

# Verificar configuración
python news_scheduler.py --test

# Ver próxima publicación
python news_scheduler.py --next

# Iniciar en loop (producción)
python news_scheduler.py --loop
```

### Verificación de Archivos Generados
- ✅ `Web/blog/articulos/` contiene 5+ HTML files
- ✅ `Web/blog/index.html` actualizado con 5+ cards
- ✅ Cosmos DB tiene artículos con timestamp
- ✅ `news_scheduler.py` ejecutándose en background

### Validación de Contenido
- ✅ Cada artículo: mínimo 1500 caracteres
- ✅ Estructura HTML: título, subtítulo, contenido, conclusión
- ✅ Categoría correcta en metadata
- ✅ Keywords relevantes por categoría

---

## 🔧 Características Técnicas

### Configuración OpenAI
- **Modelo**: gpt-5.2-2025-12-11
- **Temperature**: 0.8 (variedad en contenido)
- **Max Tokens**: 4000 (articulos largos)
- **Response Format**: JSON (estructura garantizada)

### Validación de Contenido
- **Min caracteres**: 1500 (enforced)
- **Min palabras**: 1200-1500 (en prompts)
- **Reading time**: Auto-calculado
- **HTML Structure**: Validada

### Manejo de Errores
- ❌ Sin titulares disponibles: Skip generación
- ❌ OpenAI timeout: Retry con exponential backoff
- ❌ Artículo muy corto: Regenerar
- ⚠️ Una categoría falla: Continuar con otras

---

## 📈 Estadísticas Esperadas (Diarias)

| Métrica | Valor |
|---------|-------|
| Artículos generados | 5+ |
| Artículos publicados | 5+ |
| Caracteres mínimo | 1500 cada uno |
| Tiempo de lectura total | 25-35 min |
| Categorías cubiertas | 5/5 (100%) |
| Tokens OpenAI usados | ~4000-5000 |

---

## 🚀 Deployment en Railway

El sistema está configurado para ejecutarse automáticamente:

1. **Service**: `hernando` (el bot principal)
2. **Startup**: `server.py` inicia scheduler
3. **Timezone**: Detecta zona Chile automáticamente
4. **Logging**: Todos los artículos registrados

### Monitoreo en Railway
```
Dashboard → Logs → Filter "PUBLICACIÓN AUTOMÁTICA"
```

---

## 📝 Ejemplo de Salida

```
==============================================================================
🚀 INICIANDO PUBLICACIÓN AUTOMÁTICA DIARIA (MULTI-CATEGORÍA)
   📅 22/01/2025 08:00:15 -03

🚀 INICIANDO GENERACIÓN DE CONTENIDO DIARIO
📰 Titulares agregados: 47
📝 Generando artículos por categoría...

✅ HISTORIA: El Rodeo Chileno: Una Tradición Milenaria de Destreza...
✅ GUÍAS: Preparar tu Vehículo 4x4: Guía Completa de Mantenimiento...
✅ RUTAS: Explorando la Ruta del Atacama: Aventura Extrema en Chile...
✅ EVENTOS: Eventos Corporativos en Naturaleza: Experiencias Únicas...
✅ NOTICIAS: Tendencias 2025 en Vehículos 4x4: Lo Que Viene...

✅ DIGEST DIARIO COMPLETADO
   📰 Titulares agregados: 47
   📝 Artículos generados: 5
   ⏱️  Tiempo total de lectura: 28 min

📝 5 artículos generados. Iniciando publicación...

[1/5] Publicando: El Rodeo Chileno: Una Tradición Milenaria de Destreza...
   ✅ HISTORIA - /blog/articulos/rodeo-chileno-tradicion.html

[2/5] Publicando: Preparar tu Vehículo 4x4: Guía Completa de Mantenimiento...
   ✅ GUÍAS - /blog/articulos/preparar-vehiculo-4x4.html

[3/5] Publicando: Explorando la Ruta del Atacama: Aventura Extrema en Chile...
   ✅ RUTAS - /blog/articulos/ruta-atacama-aventura.html

[4/5] Publicando: Eventos Corporativos en Naturaleza: Experiencias Únicas...
   ✅ EVENTOS - /blog/articulos/eventos-corporativos-naturaleza.html

[5/5] Publicando: Tendencias 2025 en Vehículos 4x4: Lo Que Viene...
   ✅ NOTICIAS - /blog/articulos/tendencias-4x4-2025.html

==============================================================================
✅ PUBLICACIÓN AUTOMÁTICA COMPLETADA
   📊 Exitosas: 5/5
==============================================================================
```

---

## 🔄 Next Steps (Opcional)

Para futuras mejoras:

1. **Analytics**: Agregar tracking de vistas/engagement por categoría
2. **Comments**: Sistema de comentarios en artículos
3. **Social Media**: Auto-publicar en Instagram/WhatsApp
4. **Email**: Newsletter con los 5 artículos del día
5. **A/B Testing**: Variar prompts para optimizar engagement

---

## 📞 Support

Para verificar el estado:
- SSH a Railway: `railw y shell`
- Ver logs: `tail -f hernando/logs`
- Ejecutar test: `python news_scheduler.py --test`

---

**Última actualización**: 2025-01-22
**Estado**: ✅ OPERACIONAL
**Próxima publicación**: 08:00 AM (Zona Horaria Chile)
