# Integración de Azure Computer Vision

## Descripción

A partir del commit `760e613`, Hernando incluye 5 herramientas de visión computacional **exclusivas para Efraín** para análisis avanzado de imágenes.

## Herramientas Disponibles

### 1. **analizar_imagen_completa**
Análisis completo de una imagen con todos los componentes:
- Objetos detectados
- Personas detectadas
- Descripción textual
- Etiquetas/categorías
- Marcas/logos

```
Entrada: URL de imagen
Salida: {
  "objects": [...],
  "people": [...],
  "description": "...",
  "tags": [...],
  "brands": [...]
}
```

### 2. **detectar_objetos_imagen**
Especializado en detección de elementos y objetos:
- Identifica qué hay en la imagen
- Proporciona confianza de detección
- Posición en la imagen

```
Entrada: URL de imagen
Salida: {
  "objects_detected": [
    {"object": "car", "confidence": 98.5, "rectangle": {...}},
    {"object": "person", "confidence": 95.2, "rectangle": {...}}
  ],
  "total_objects": 2
}
```

### 3. **detectar_personas_imagen**
Detección de personas con precisión:
- Cantidad de personas
- Ubicación en la imagen (coordenadas)
- Nivel de confianza

```
Entrada: URL de imagen
Salida: {
  "people_detected": [
    {"confidence": 99.1, "rectangle": {"x": 100, "y": 200, "w": 50, "h": 100}},
    {"confidence": 95.3, "rectangle": {"x": 300, "y": 150, "w": 60, "h": 120}}
  ],
  "total_people": 2
}
```

### 4. **describir_imagen**
Descripción textual inteligente:
- Resumen de lo que hay en la imagen
- Etiquetas/categorías
- Confianza de la descripción

```
Entrada: URL de imagen
Salida: {
  "description": "Two people standing in a sunny park",
  "confidence": 96.5,
  "tags": [
    {"name": "outdoor", "confidence": 99.2},
    {"name": "people", "confidence": 98.5},
    {"name": "park", "confidence": 95.1}
  ]
}
```

### 5. **extraer_texto_imagen**
OCR (Optical Character Recognition):
- Extrae texto visible en la imagen
- Ideal para documentos, señales, etc.

```
Entrada: URL de imagen
Salida: {
  "text": "Texto extraído de la imagen...",
  "success": true
}
```

## Configuración

Para que las herramientas funcionen, necesitas configurar en tu `.env`:

```env
# Azure Computer Vision
AZURE_VISION_ENDPOINT=https://xxxxx.cognitiveservices.azure.com/
AZURE_VISION_KEY=tu_clave_api

# O servicio HTTP de Railway (opcional)
VISION_SERVICE_URL=vision-service-url
```

## Arquitectura

### vision_client.py
- **HTTP Fallback**: Intenta servicio HTTP en Railway primero
- **Azure SDK Fallback**: Si no, usa SDK directo de Azure
- **Funciones Públicas**:
  - `analyze_image(url)`: Análisis completo
  - `detect_objects(url)`: Objetos
  - `detect_people(url)`: Personas
  - `get_image_description(url)`: Descripción
  - `extract_text_from_image(url)`: OCR

### hernando_tools.py
- **5 herramientas** registradas como tools de OpenAI Function Calling
- **Autorización gated**: Solo usuarios con `is_authorized_user(user_id) == True`
- **Routing**: Cada herramienta mapea a función en `vision_client.py`

## Ejemplos de Uso

### Ejemplo 1: Analizar una foto de actividad
```
Tú: "Analiza esta foto de la actividad off-road: https://example.com/batuco-activity.jpg"

Hernando ejecuta: analizar_imagen_completa(url)

Respuesta: "Detecto 8 objetos principales: 3 vehículos 4x4, 5 personas, vegetación, camino de tierra. 
Las personas están distribuidas en la zona de actividad. Confianza: 96%"
```

### Ejemplo 2: Verificar cantidad de personas
```
Tú: "¿Cuántas personas hay en esta foto?"

Hernando ejecuta: detectar_personas_imagen(url)

Respuesta: "Detecto 5 personas en la imagen, distribuidas en diferentes posiciones."
```

### Ejemplo 3: Extraer información de un documento
```
Tú: "Extrae el texto de esta factura"

Hernando ejecuta: extraer_texto_imagen(url)

Respuesta: [texto completo extraído del documento]
```

## Restricciones de Seguridad

- ✅ **Solo Efraín** puede usar estas herramientas (gated por `is_authorized_user`)
- ✅ Las imágenes deben ser **URLs públicas** (no local files)
- ✅ Máximo **10 segundos** por análisis (timeout)
- ✅ Compatible con **HTTP y Azure SDK**

## Casos de Uso

### En Fundo Moraga
1. **Análisis de actividades**: Verificar participantes, vehículos, seguridad
2. **Reportes fotográficos**: Generar descripciones automáticas
3. **Documentación**: Extraer datos de documentos, facturas, permisos
4. **Verificación de propiedad**: Analizar fotos de terreno, mejoras, etc.

## Próximas Mejoras

- [ ] Reconocimiento facial especializado
- [ ] Análisis de placas vehiculares
- [ ] Detección de actividades específicas
- [ ] Caché de análisis por imagen

---

**Commit**: `760e613`  
**Fecha**: 29 de Enero, 2026  
**Autor**: Sistema Automático

## Testing

Para verificar:

1. Asegúrate de tener configuradas las claves en `config.py`
2. Llama a Hernando como Efraín con una URL de imagen
3. Pide análisis: "¿Qué hay en esta foto?"

Las herramientas responden con análisis completos incluyendo confianza y posiciones.
