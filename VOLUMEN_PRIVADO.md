# 📁 Volumen de Conocimiento Privado

Este volumen está montado en `/app/private_knowledge` en Railway y está diseñado para almacenar documentos privados accesibles solo por números autorizados.

## 🔐 Acceso Restringido

Solo usuarios con números de WhatsApp autorizados pueden acceder a estos documentos.  
Números autorizados configurados en: `SPECIAL_PERSONA_WHATSAPP_NUMBERS`

## 📤 Subir Archivos por WhatsApp

**La forma más fácil:** ¡Simplemente envía archivos adjuntos por WhatsApp!

Cuando envías un archivo desde tu número autorizado (+56941242609) al WhatsApp de Hernando (+56951016809), el sistema:

1. ✅ **Descarga automáticamente** el archivo de WAHA
2. 📂 **Organiza** por fecha y tipo en carpetas
3. 💾 **Guarda** en el volumen persistente
4. ✉️ **Confirma** con detalles del archivo guardado
5. 📝 **Almacena metadata** si el archivo tenía caption/texto

### Tipos de Archivos Soportados

- 🖼️ **Imágenes**: JPG, PNG, GIF, WebP
- 🎥 **Videos**: MP4, MOV, AVI
- 🎵 **Audios**: MP3, OGG, WAV, notas de voz
- 📄 **PDFs**: Documentos PDF
- 📝 **Documentos**: DOCX, DOC
- 📊 **Hojas de cálculo**: XLSX, XLS
- 📊 **Presentaciones**: PPTX, PPT
- 📃 **Textos**: TXT, MD, CSV, JSON
- 📁 **Otros**: Cualquier otro formato

### Estructura Automática

Los archivos se organizan automáticamente:

```
/app/private_knowledge/
└── uploads/
    └── 2026-01-29/              # Fecha de subida
        ├── imagenes/
        │   ├── foto_140532.jpg
        │   └── foto_140532.jpg.meta.txt  # Metadata
        ├── videos/
        │   └── video_151203.mp4
        ├── audios/
        │   └── nota_voz_160145.ogg
        ├── pdfs/
        │   ├── contrato.pdf
        │   └── contrato.pdf.meta.txt
        └── documentos/
            └── reporte.docx
```

### Ejemplo de Uso

**Tú (por WhatsApp):** *[Envías una foto con el texto "Logo nuevo del Fundo"]*

**Hernando:** 
```
🖼️ ¡Archivo guardado exitosamente!

📁 Nombre: IMG_20260129_143052.jpg
📏 Tamaño: 2.3 MB
📂 Categoría: imagenes
🗂️ Ruta: uploads/2026-01-29/imagenes/IMG_20260129_143052.jpg

Ya está disponible en tu volumen privado. Puedes pedirme que te muestre los archivos en cualquier momento.

💬 También guardé el texto que acompañó al archivo.
```

## 📂 Estructura Recomendada

```
/app/private_knowledge/
├── documentos/          # Documentos generales
│   ├── contratos/
│   ├── facturas/
│   └── reportes/
├── proyectos/           # Información de proyectos
├── notas/               # Notas personales
└── referencias/         # Material de referencia
```

## 🎯 Herramientas Disponibles

Cuando Efraín contacta a Hernando, tiene acceso a 3 herramientas adicionales:

### 1. **list_private_documents**
Lista todos los documentos disponibles
- **Uso**: "¿Qué documentos tengo?"
- **Respuesta**: Lista organizada por carpetas

### 2. **read_private_document**
Lee el contenido de un documento específico
- **Uso**: "Muéstrame el contenido de documento.txt"
- **Parámetro**: `file_path` (ej: "contratos/contrato2024.txt")
- **Límite**: 10,000 caracteres por archivo

### 3. **search_private_documents**
Busca documentos por nombre o contenido
- **Uso**: "Busca documentos que contengan 'presupuesto 2025'"
- **Parámetro**: `query` (término de búsqueda)
- **Busca en**: Nombres de archivo y contenido de archivos de texto

## 📝 Formatos Soportados

### Lectura de Contenido
- `.txt` - Archivos de texto plano
- `.md` - Markdown
- `.json` - JSON
- `.csv` - CSV

### Solo Listado
- `.pdf`, `.docx`, `.xlsx` - Se listan pero no se lee contenido automáticamente
- Imágenes (`.jpg`, `.png`, etc.) - Se listan con tamaño

## 🚀 Cómo Subir Archivos

### Opción 1: Railway CLI (Recomendado para archivos grandes)
```bash
# Desde tu computadora local
railway link
railway service link "Hernando"
railway volume attach <volume-id>

# Copiar archivos
railway run cp miarchivo.pdf /app/private_knowledge/
```

### Opción 2: Durante el Deploy
1. Agregar archivos en el repositorio bajo una carpeta `knowledge_base/`
2. Modificar Dockerfile para copiar al volumen:
```dockerfile
COPY knowledge_base/ /app/private_knowledge/
```

### Opción 3: API/Script
Crear script Python que suba archivos usando `requests` o similar al endpoint del servicio.

## 💡 Ejemplos de Uso

### Conversación con Hernando (como Efraín):

**Tú:** "¿Qué documentos tengo disponibles?"  
**Hernando:** *Lista todos los documentos organizados por carpeta*

**Tú:** "Muéstrame el archivo contratos/contrato-batuco.txt"  
**Hernando:** *Lee y muestra el contenido del archivo*

**Tú:** "Busca documentos que hablen sobre el presupuesto 2025"  
**Hernando:** *Busca en nombres y contenidos, devuelve coincidencias*

## 🔒 Seguridad

- **Acceso**: Solo números autorizados en `SPECIAL_PERSONA_WHATSAPP_NUMBERS`
- **Validación**: Path traversal protegido (no se puede acceder fuera de `/app/private_knowledge`)
- **Límites**: Archivos truncados a 10KB para evitar sobrecarga
- **Privacidad**: Documentos nunca visibles para clientes normales

## ⚙️ Configuración en Railway

```bash
# Ver volumen actual
railway volume list

# ID del volumen: hernando-volume
# Mount path: /app/private_knowledge
```

## 📊 Límites y Consideraciones

- **Tamaño del volumen**: Según plan de Railway (5-100 GB típicamente)
- **Límite de lectura**: 10,000 caracteres por archivo
- **Archivos binarios**: Solo se lista metadata, no se lee contenido
- **Performance**: Acceso de disco, no hay caching (considerar Redis para docs frecuentes)

## 🛠️ Mantenimiento

### Listar archivos del volumen
```bash
railway run ls -lah /app/private_knowledge
```

### Eliminar archivo
```bash
railway run rm /app/private_knowledge/archivo.txt
```

### Ver espacio usado
```bash
railway run du -sh /app/private_knowledge
```

---

**Última actualización**: 29 de enero, 2026  
**Commit**: 56dcc76
