# Vision Service para Hernando

Servicio HTTP que expone Azure Computer Vision vía REST API.

## Endpoints

### GET /health
Health check del servicio.

### POST /analyze
Analiza una imagen completa (objetos, personas, descripción, tags, marcas).

**Request:**
```json
{
  "image_url": "https://example.com/image.jpg"
}
```

**Response:**
```json
{
  "objects": [...],
  "people": [...],
  "description": "...",
  "tags": [...],
  "brands": [...],
  "success": true
}
```

### POST /ocr
Extrae texto de una imagen (OCR).

**Request:**
```json
{
  "image_url": "https://example.com/document.jpg"
}
```

**Response:**
```json
{
  "text": "Texto extraído...",
  "success": true
}
```

## Variables de Entorno

- `AZURE_VISION_ENDPOINT`: Endpoint de Computer Vision
- `AZURE_VISION_KEY`: Clave de API
- `PORT`: Puerto (default 8080)

## Deploy en Railway

1. Crear nuevo servicio en Railway
2. Conectar a este directorio
3. Configurar variables de entorno
4. Deploy automático
