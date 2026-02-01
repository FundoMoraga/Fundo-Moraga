# 🚀 Guía Rápida - Imágenes Destacadas en Blog

## ✅ Implementación Completada

Las publicaciones del blog ahora tienen **imágenes principales automáticas** de Pexels (gratis).

---

## 🧪 Prueba Inmediata (5 minutos)

### Opción 1: Local (si tienes el proyecto corriendo)

```bash
# Terminal en la carpeta del proyecto
cd m:/VSC/Fundo-Moraga

# Ejecutar publicación de prueba
python news_scheduler.py --now
```

**Esperado**:
```
🚀 INICIANDO PUBLICACIÓN AUTOMÁTICA...

✅ HISTORIA: [Título]
   ✅ Imagen obtenida: Photographer

[Repite para 5 categorías]

✅ PUBLICACIÓN AUTOMÁTICA COMPLETADA
   📊 Exitosas: 5/5
```

### Opción 2: Railway (Producción)

```bash
# Conectarse a Railway
railway shell

# Ejecutar dentro del contenedor
python news_scheduler.py --now

# Verificar logs
railway logs | grep -i "imagen\|pexels"
```

---

## 📋 Verificación

### 1. Verificar archivos HTML generados

```bash
# Ver lista de artículos
ls -lah Web/blog/articulos/

# Buscar etiqueta de imagen en un artículo
grep -i "featured-image" Web/blog/articulos/*.html | head -5
```

**Esperado**: Encontrar líneas con `<img src="https://images.pexels.com/..."`

### 2. Revisar en el navegador

1. Ir a: `https://fundomoraga.com/blog/articulos/[nombre-articulo].html`
2. Verificar:
   - ✅ Imagen visible bajo el título
   - ✅ Crédito del fotógrafo ("Photo by [Name] on Pexels")
   - ✅ Imagen responsive (prueba en mobile)

### 3. Inspeccionar HTML (DevTools)

```html
<!-- Buscar estas etiquetas -->
<meta property="og:image" content="https://images.pexels.com/...">
<img src="https://images.pexels.com/..." class="featured-image">
<div class="image-attribution">...</div>
```

### 4. Prueba Social Media Preview

1. Ir a: https://www.opengraph.xyz/
2. Ingresar URL del artículo
3. Verificar que aparezca **imagen + título + descripción**

---

## 📊 ¿Qué hace cada componente?

| Componente | Función | Líneas |
|-----------|---------|--------|
| **pexels_client.py** | Busca imágenes en Pexels | 180 |
| **news_aggregator.py** | Obtiene imagen para cada artículo | +90 |
| **blog_publisher.py** | Inserta imagen en HTML | +80 |
| **config.py** | Almacena config Pexels | +3 |

---

## 💡 Búsqueda por Categoría

```
📚 HISTORIA
   ↓ Busca: "4x4 adventure Chile" → "off-road tradition" → curadas
   ↓ Resultado: Imágenes de 4x4, vehículos, paisajes
   
📖 GUÍAS
   ↓ Busca: "vehicle maintenance" → "4x4 repair" → curadas
   ↓ Resultado: Talleres, herramientas, mantenimiento
   
🗺️ RUTAS
   ↓ Busca: "off-road trail" → "mountain road" → curadas
   ↓ Resultado: Paisajes, montañas, senderos
   
🎪 EVENTOS
   ↓ Busca: "off-road competition" → "4x4 rally" → curadas
   ↓ Resultado: Competencias, rallies, aventuras
   
📰 NOTICIAS
   ↓ Busca: "4x4 truck" → "off-road vehicle" → curadas
   ↓ Resultado: Vehículos modernos, noticias
```

---

## 🔧 Configuración (Opcional)

### Para mejorar límites de Pexels:

1. Ir a: https://www.pexels.com/api/
2. Crear cuenta y registrar aplicación
3. Copiar API key
4. En Railway, agregar variable de entorno:

```
PEXELS_API_KEY=pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Sin clave**: Funciona normal (suficiente para 1 artículo/día)

---

## 🐛 Troubleshooting

### "No se obtiene imagen"

```python
# Verificar que Pexels API responda
curl "https://api.pexels.com/v1/search?query=4x4+truck&per_page=5"

# Revisar logs en Railway
railway logs | grep -i pexels
```

### "Imagen lenta"

- Normal: Búsqueda + fallback puede tomar 1-2 segundos
- Se ejecuta en background, no bloquea artículo
- Caching en futuro mejorará esto

### "URL de imagen rota"

- Pexels ocasionalmente puede mover URLs
- Verificar en web: https://www.pexels.com/
- Si API key es válida, implementar descarga local (futuro)

---

## 📈 Métricas

Después de la próxima publicación (08:00 AM mañana):

```
Esperado:
✅ 5 artículos generados
✅ 5 imágenes obtenidas de Pexels
✅ 5 HTML publicados con imágenes
✅ 5 créditos al fotógrafo agregados
✅ Meta tags con imágenes para redes
```

---

## 🎯 Próximos Pasos (Futuro)

- [ ] Descargar imágenes a Azure Storage (velocidad)
- [ ] Generar múltiples tamaños (srcset)
- [ ] Caching en Cosmos DB
- [ ] Análisis de color para tema
- [ ] Búsqueda usando keywords del artículo

---

## 📞 Contacto

¿Preguntas o problemas?

- Ver: [PEXELS_INTEGRATION.md](PEXELS_INTEGRATION.md) - Documentación técnica
- Ver: [FEATURED_IMAGES_SUMMARY.md](FEATURED_IMAGES_SUMMARY.md) - Resumen implementación

---

**Última actualización**: 1 de febrero, 2026  
**Versión**: v1.0 - Pexels API Integration  
**Estado**: ✅ OPERACIONAL
