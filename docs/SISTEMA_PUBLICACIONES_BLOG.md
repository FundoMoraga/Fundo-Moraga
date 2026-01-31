# Sistema de Publicaciones Automáticas del Blog

## 📰 Descripción General

Sistema completo de generación y publicación automática de artículos para el blog de Fundo Moraga. Hernando IA agrega noticias de múltiples fuentes automotrices, genera contenido **100% original** usando IA, y publica automáticamente cada día.

## ⚖️ Ética y Cumplimiento

### ✅ Fair Use y Originalidad

Este sistema cumple estrictamente con:
- **NO copia contenido con copyright** - Solo extrae titulares públicos como referencias
- **Contenido 100% original** - IA genera artículos completamente nuevos
- **Transformativo** - Añade valor único desde perspectiva off-road chilena
- **Attribution** - Referencias claras a fuentes consultadas
- **Rate limiting** - Scraping ético con delays apropiados

### 📚 Fuentes Consultadas

- **RutaMotor.com** - Noticias automotrices Chile
- **La Tercera Motores** - Sección automotriz
- **Al Torque** - Revista digital automotriz
- Otras fuentes internacionales (expandible)

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    NEWS SCHEDULER                       │
│           (Ejecuta diariamente 08:00 AM Chile)         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  NEWS AGGREGATOR                        │
│  • Fetch headlines de múltiples fuentes                │
│  • Rate limiting ético (2s entre requests)              │
│  • Extrae solo: título, link, excerpt corto             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              OPENAI (GPT-5.2)                          │
│  • Genera artículo 100% original (600-800 palabras)   │
│  • Enfoque: 4x4/off-road para audiencia chilena       │
│  • SEO optimizado con keywords naturales               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 BLOG PUBLISHER                          │
│  • Guarda artículo en Cosmos DB                        │
│  • Genera archivo HTML estático                        │
│  • Publica en /Web/blog/articulos/                     │
└─────────────────────────────────────────────────────────┘
```

## 📁 Archivos del Sistema

### `news_aggregator.py`
**Función:** Agrega titulares de fuentes públicas y genera contenido original

**Clases principales:**
- `NewsSource` - Define una fuente de noticias
- `NewsAggregator` - Controlador principal

**Métodos clave:**
```python
fetch_headlines(source, max_items=5)      # Obtiene titulares de una fuente
fetch_all_headlines(max_per_source=5)     # Agrega de todas las fuentes
generate_original_article(headlines)      # Genera artículo con IA
create_daily_digest()                     # Proceso completo diario
```

**CLI:**
```bash
# Solo obtener titulares
python news_aggregator.py --headlines

# Generar artículo completo
python news_aggregator.py --generate

# Digest diario completo
python news_aggregator.py --digest
```

### `blog_publisher.py`
**Función:** Publica artículos generados al blog HTML estático

**Clase principal:**
- `BlogPublisher` - Gestión de publicaciones

**Métodos clave:**
```python
generate_article_html(article)            # Genera HTML completo
publish_article(article, save_cosmos)     # Publica y guarda
get_recent_articles(limit=10)             # Lista artículos recientes
```

**CLI:**
```bash
# Publicar artículo de prueba
python blog_publisher.py --test

# Listar artículos recientes
python blog_publisher.py --list
```

### `news_scheduler.py`
**Función:** Scheduler automático de publicaciones diarias

**Configuración:**
- Hora de publicación: **08:00 AM Chile** (configurable)
- Intervalo de chequeo: **30 minutos**
- Zona horaria: `America/Santiago`

**Métodos clave:**
```python
start_news_scheduler()                    # Inicia daemon thread
run_now()                                 # Publicación inmediata (manual)
get_next_publish_time()                   # Próxima hora de publicación
```

**CLI:**
```bash
# Ejecutar publicación AHORA (manual)
python news_scheduler.py --now

# Loop daemon (producción)
python news_scheduler.py --loop

# Verificar configuración
python news_scheduler.py --test

# Ver próxima hora de publicación
python news_scheduler.py --next
```

## ⚙️ Configuración

### Variables de Entorno (`config.py`)

```bash
# Habilitar/deshabilitar scheduler
NEWS_SCHEDULER_ENABLED=true           # true|false

# Hora de publicación (formato 24h)
NEWS_PUBLISH_HOUR=8                   # 0-23 (default: 8 = 08:00 AM)

# Intervalo de chequeo en minutos
NEWS_CHECK_INTERVAL_MINUTES=30        # default: 30 minutos
```

### Integración con Server

El scheduler se inicia automáticamente en `server.py` cuando:
```python
RUN_SCHEDULER_THREAD=true  # O "1", "yes", "y", "si"
```

Se ejecuta en thread daemon junto al reminder_scheduler existente.

## 📝 Flujo de Publicación

### 1. Agregación (08:00 AM Chile)
```
NEWS AGGREGATOR
├── Consulta RutaMotor.com
│   └── Extrae 5 titulares más recientes
├── Consulta La Tercera Motores
│   └── Extrae 5 titulares más recientes
├── Consulta Al Torque
│   └── Extrae 5 titulares más recientes
└── Total: ~15 titulares agregados
```

### 2. Generación con IA
```
OPENAI GPT-5.2
├── Input: 15 titulares de tendencias actuales
├── Prompt: "Genera artículo original sobre [tema]"
├── Estilo: Profesional, aventurero, SEO-optimized
├── Output: JSON con estructura completa
│   ├── title: Título atractivo
│   ├── subtitle: Bajada
│   ├── slug: URL-friendly
│   ├── content_html: 600-800 palabras en HTML
│   ├── excerpt: 120-150 chars
│   ├── keywords: ["4x4", "off-road", ...]
│   ├── category: noticias|tips|tecnologia
│   └── reading_time_minutes: 4-5
└── Artículo 100% original y transformativo
```

### 3. Publicación
```
BLOG PUBLISHER
├── Guarda en Cosmos DB
│   ├── type: "blog_article"
│   ├── status: "published"
│   └── id: "article_{slug}_{fecha}"
├── Genera HTML estático
│   └── /Web/blog/articulos/{slug}.html
└── (Futuro) Actualiza índice del blog
```

## 🗄️ Estructura de Datos

### Cosmos DB - Artículos

```json
{
  "id": "article_tendencias-4x4-enero-2026_20260131",
  "type": "blog_article",
  "userId": "system",
  "status": "published",
  "title": "Tendencias 4x4 para 2026",
  "subtitle": "Lo último en todoterreno",
  "slug": "tendencias-4x4-enero-2026",
  "content_html": "<h2>Sección 1</h2><p>...</p>",
  "excerpt": "Las tendencias más importantes...",
  "keywords": ["4x4", "off-road", "chile"],
  "category": "noticias",
  "reading_time_minutes": 5,
  "author": "Hernando IA",
  "published_at": "2026-01-31T11:00:00Z",
  "url": "https://fundomoraga.com/blog/articulos/tendencias-4x4-enero-2026.html",
  "sources_referenced": ["RutaMotor", "La Tercera"],
  "source_headlines_count": 15
}
```

### Archivos HTML Generados

```
Web/blog/
├── index.html                          # Índice principal del blog
├── articulos/                          # Artículos publicados
│   ├── tendencias-4x4-enero-2026.html
│   ├── mejores-neumaticos-off-road.html
│   └── ...
└── blog-styles.css                     # Estilos compartidos
```

## 🚀 Instalación y Deploy

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Nuevas dependencias añadidas:
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=5.0.0` - XML/HTML parser

### 2. Configurar Variables

En Railway o `.env`:
```bash
NEWS_SCHEDULER_ENABLED=true
NEWS_PUBLISH_HOUR=8
NEWS_CHECK_INTERVAL_MINUTES=30
RUN_SCHEDULER_THREAD=true
```

### 3. Testing Local

```bash
# Verificar configuración
python news_scheduler.py --test

# Ejecutar publicación manual
python news_scheduler.py --now
```

### 4. Deploy a Railway

```bash
git add .
git commit -m "feat: Sistema de publicaciones automáticas del blog"
git push origin main
```

Railway detectará automáticamente los cambios y redesplegará.

## 🧪 Testing

### Test Completo del Flujo

```bash
# 1. Verificar agregador
python news_aggregator.py --headlines

# 2. Generar artículo de prueba
python news_aggregator.py --generate > test_article.json

# 3. Publicar artículo de prueba
python blog_publisher.py --test

# 4. Verificar scheduler
python news_scheduler.py --test

# 5. Publicación manual completa
python news_scheduler.py --now
```

### Validar Artículo Generado

```bash
# Ver artículos en Cosmos DB
python -c "
from blog_publisher import get_blog_publisher
articles = get_blog_publisher().get_recent_articles(5)
print(len(articles), 'artículos encontrados')
"

# Verificar archivo HTML
ls Web/blog/articulos/
```

## 📊 Monitoreo

### Logs del Scheduler

El scheduler imprime logs detallados:

```
==================================================================
🤖 NEWS SCHEDULER INICIADO
   ⏰ Publicación diaria: 08:00 (Chile)
   🔄 Intervalo de chequeo: 30 minutos
==================================================================

⏸️  No es hora de publicar (ahora: 07:45 - objetivo: 08:00)
⏰ Es hora de publicar contenido diario!

==================================================================
🚀 INICIANDO PUBLICACIÓN AUTOMÁTICA DIARIA
   📅 31/01/2026 08:00:15 -03
==================================================================

📰 Consultando RutaMotor...
✓ 5 titulares obtenidos de RutaMotor
📰 Consultando La Tercera Motores...
✓ 5 titulares obtenidos de La Tercera Motores

📊 Total: 15 titulares agregados

🤖 Generando artículo original con IA...
✅ Artículo generado: 'Tendencias 4x4 para 2026'

💾 Guardando artículo en Cosmos DB...
✅ Guardado en Cosmos: article_tendencias-4x4_20260131
📄 Generando HTML: Web/blog/articulos/tendencias-4x4.html
✅ Artículo publicado

==================================================================
✅ PUBLICACIÓN COMPLETADA EXITOSAMENTE
   📝 Título: Tendencias 4x4 para 2026
   🔗 URL: https://fundomoraga.com/blog/articulos/tendencias-4x4.html
==================================================================
```

## 🔧 Mantenimiento

### Añadir Nueva Fuente de Noticias

Editar `news_aggregator.py`:

```python
NEWS_SOURCES.append(
    NewsSource(
        name="NuevoMedio",
        url="https://nuevomedio.com/autos",
        selectors={
            "articles": "article.post",
            "title": "h2.title",
            "link": "a.permalink",
            "excerpt": "p.summary"
        },
        category="internacional"
    )
)
```

### Modificar Hora de Publicación

```bash
# Cambiar a 10:00 AM
NEWS_PUBLISH_HOUR=10
```

O en Railway: Variables de Entorno → `NEWS_PUBLISH_HOUR` → `10`

### Deshabilitar Publicaciones Automáticas

```bash
NEWS_SCHEDULER_ENABLED=false
```

Las publicaciones manuales con `--now` siguen disponibles.

## 📈 Próximas Mejoras

### En Desarrollo
- [ ] Actualización automática del índice del blog
- [ ] Sistema de categorías y tags dinámicos
- [ ] Integración con imágenes (Azure Storage)
- [ ] SEO avanzado con structured data (JSON-LD)

### Roadmap
- [ ] Sistema de revisión editorial (draft → review → published)
- [ ] Notificaciones push cuando se publica artículo
- [ ] Analytics de engagement por artículo
- [ ] A/B testing de títulos
- [ ] Generación de imágenes destacadas con DALL-E

## 🆘 Troubleshooting

### El scheduler no publica

1. Verificar logs:
   ```bash
   python news_scheduler.py --test
   ```

2. Verificar hora actual Chile:
   ```python
   from datetime import datetime
   from zoneinfo import ZoneInfo
   print(datetime.now(ZoneInfo("America/Santiago")))
   ```

3. Ejecutar publicación manual:
   ```bash
   python news_scheduler.py --now
   ```

### Error al obtener titulares

- **Causa:** Cambios en estructura HTML de las fuentes
- **Solución:** Actualizar selectores CSS en `NEWS_SOURCES`

### Artículo no aparece en el blog

1. Verificar archivo generado:
   ```bash
   ls Web/blog/articulos/
   ```

2. Verificar Cosmos DB:
   ```bash
   python blog_publisher.py --list
   ```

3. Verificar permisos de escritura en directorio Web/blog/

## 📞 Soporte

Para problemas o consultas sobre el sistema:
- **Logs:** Revisar output del scheduler en Railway
- **Testing:** Usar comandos CLI con `--test`
- **Manual:** Usar `--now` para publicación inmediata

---

**Sistema implementado por:** Hernando IA  
**Fecha:** Enero 2026  
**Versión:** 1.0.0
