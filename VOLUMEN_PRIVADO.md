# 📁 Volumen de Conocimiento Privado

Este volumen está montado en `/app/private_knowledge` en Railway y está diseñado para almacenar documentos privados accesibles solo por números autorizados.

## 🔐 Acceso Restringido

Solo usuarios con números de WhatsApp autorizados pueden acceder a estos documentos.  
Números autorizados configurados en: `SPECIAL_PERSONA_WHATSAPP_NUMBERS`

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
