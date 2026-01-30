# 🛠️ GUÍA RÁPIDA - 7 NUEVAS HERRAMIENTAS

## Resumen
Se han implementado 7 nuevas herramientas para Hernando. Estas herramientas permiten:
- 💾 Guardar documentos en Azure Storage
- 📧 Enviar emails y crear alertas
- 🔍 Buscar en conversaciones pasadas
- 📊 Exportar datos y generar reportes

---

## 1️⃣ GUARDAR DOCUMENTO

**Función:** `guardar_documento(nombre, contenido, tipo, categoria)`

**Parámetros:**
- `nombre` (string): Nombre del archivo (ej: "presupuesto_2026")
- `contenido` (string): Contenido a guardar
- `tipo` (string): Tipo de contenido (text, json, csv, html)
- `categoria` (string): Carpeta de organización (ej: "reportes", "documentos", "contratos")

**Ejemplo de uso en conversación:**
```
Usuario: "Guarda este documento de presupuesto en la carpeta reportes"
Hernando: 
  - Guarda documento
  - Retorna: "Documento guardado: presupuesto_2026 en /reportes"
  - URL: https://fundomoragastorage.blob.core.windows.net/...
```

**Caso de uso:** Crear documentos permanentes que quedan guardados en la nube

---

## 2️⃣ LISTAR DOCUMENTOS GUARDADOS

**Función:** `listar_documentos_guardados(categoria, incluir_urls)`

**Parámetros:**
- `categoria` (string): Carpeta a listar (ej: "reportes")
- `incluir_urls` (boolean): Si incluir URLs descargables (default: False)

**Ejemplo de uso:**
```
Usuario: "Muestra mis documentos guardados de reportes"
Hernando:
  - Busca en /reportes
  - Retorna lista con:
    * Nombre archivo
    * Tamaño
    * Fecha de modificación
    * URL de descarga (si incluir_urls=True)
```

**Caso de uso:** Gestionar y acceder a documentos guardados previamente

---

## 3️⃣ ENVIAR EMAIL

**Función:** `enviar_email(destinatario, asunto, cuerpo, adjunto_url)`

**Parámetros:**
- `destinatario` (string): Email del receptor (ej: "admin@fundomoraga.com")
- `asunto` (string): Asunto del email
- `cuerpo` (string): Contenido del email (puede ser HTML)
- `adjunto_url` (string, opcional): URL del archivo a adjuntar

**Ejemplo de uso:**
```
Usuario: "Envía un email a admin@fundomoraga.com con el reporte mensual"
Hernando:
  - Prepara email
  - Adjunta documento
  - Envía vía Resend
  - Retorna: "Email enviado a admin@fundomoraga.com"
```

**Caso de uso:** Comunicar resultados, enviar reportes, notificaciones automáticas

---

## 4️⃣ CREAR ALERTA

**Función:** `crear_alerta(tipo, mensaje, frecuencia, email)`

**Parámetros:**
- `tipo` (string): Tipo de alerta (info, advertencia, crítica)
- `mensaje` (string): Descripción de la alerta
- `frecuencia` (string): Frecuencia de notificación (inmediata, diaria, semanal)
- `email` (string, opcional): Email para notificación

**Ejemplo de uso:**
```
Usuario: "Crea una alerta crítica si los precios suben más de 10%"
Hernando:
  - Crea alerta en Cosmos DB
  - Si tiene email: Envía notificación inmediata
  - Retorna: "Alerta creada: alerta_2026-01-30_14:30:45"
```

**Caso de uso:** Monitoreo de eventos, notificaciones automáticas, seguimiento de cambios

---

## 5️⃣ BUSCAR EN CONVERSACIONES

**Función:** `buscar_en_conversaciones(query, filtro_fecha, limite)`

**Parámetros:**
- `query` (string): Texto a buscar (ej: "precios", "batuco")
- `filtro_fecha` (string, opcional): Fecha en formato YYYY-MM-DD
- `limite` (int): Máximo de resultados (default: 10)

**Ejemplo de uso:**
```
Usuario: "Busca todas mis conversaciones sobre precios del Batuco de enero"
Hernando:
  - Busca en Cosmos DB
  - Filtro: query contiene "precios" y "batuco", fecha = enero 2026
  - Retorna: Lista con hasta 10 conversaciones ordenadas por fecha
```

**Caso de uso:** Acceder a información histórica, auditoría de conversaciones, análisis de tendencias

---

## 6️⃣ EXPORTAR DATOS

**Función:** `exportar_datos(tipo_datos, formato, filtro)`

**Parámetros:**
- `tipo_datos` (string): Tipo de datos (conversaciones, usuarios, alertas, etc.)
- `formato` (string): Formato de salida (json, csv, xlsx)
- `filtro` (string, opcional): Filtro SQL adicional

**Ejemplo de uso:**
```
Usuario: "Exporta todas las conversaciones de enero a CSV"
Hernando:
  - Consulta conversaciones con filtro de fecha
  - Convierte a CSV
  - Guarda en /exports
  - Retorna: "Exportado: export_conversaciones_20260130_143045.csv"
  - URL: https://fundomoragastorage.blob.core.windows.net/exports/...
```

**Caso de uso:** Análisis externo, respaldo de datos, compartir información en Excel

---

## 7️⃣ GENERAR REPORTE

**Función:** `generar_reporte(tipo_reporte, período, incluir_gráficos)`

**Parámetros:**
- `tipo_reporte` (string): Tipo (actividad, usuarios, ingresos, performance)
- `período` (string): Período (diario, semanal, mensual, anual)
- `incluir_gráficos` (boolean): Si incluir visualizaciones

**Ejemplo de uso:**
```
Usuario: "Genera un reporte mensual de actividad"
Hernando:
  - Calcula métricas:
    * Total de conversaciones
    * Usuarios nuevos
    * Actividad por día
    * Performance de servicios
  - Genera JSON con datos
  - Guarda en /reportes
  - Retorna: "Reporte generado: reporte_actividad_mensual_20260130.json"
```

**Caso de uso:** Análisis de rendimiento, reportes gerenciales, toma de decisiones

---

## 📱 EJEMPLOS EN CONVERSACIONES REALES

### Ejemplo 1: Flujo Completo de Reportería
```
Usuario: "Necesito un reporte mensual de actividad con los datos exportados"

Hernando:
1. generar_reporte("actividad", "mensual", True)
2. exportar_datos("conversaciones", "csv", "WHERE timestamp > '2026-01-01'")
3. guardar_documento("reporte_enero_datos.csv", contenido, "csv", "reportes")
4. enviar_email("admin@fundomoraga.com", "Reporte de Actividad", 
                 "<h1>Reporte de Enero</h1>...", url_csv)

Respuesta: "Reporte generado y enviado a tu email con CSV adjunto"
```

### Ejemplo 2: Búsqueda y Alertas
```
Usuario: "Busca conversaciones sobre precios de este mes y avisame si hay cambios"

Hernando:
1. buscar_en_conversaciones("precios", "2026-01", 20)
2. crear_alerta("advertencia", "Cambios de precio detectados", "diaria", 
                 "efrain@fundomoraga.com")

Respuesta: "Encontré 15 conversaciones. Alerta configurada para notificarte diariamente"
```

### Ejemplo 3: Documentos y Respaldo
```
Usuario: "Guarda el catálogo de Batuco y dame la lista de documentos guardados"

Hernando:
1. guardar_documento("catalogo_batuco_2026", contenido, "html", "catalogos")
2. listar_documentos_guardados("catalogos", True)

Respuesta: "Catálogo guardado. Documentos en catalogos: [lista con URLs]"
```

---

## ⚙️ CONFIGURACIÓN REQUERIDA

Para que las herramientas funcionen, asegúrate de tener:

### Variables de Entorno
```
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_ACCOUNT=fundomoragastorage
AZURE_STORAGE_CONTAINER=hernando-docs
AZURE_STORAGE_ACCOUNT_KEY=...
RESEND_API_KEY=...
COSMOS_DB_CONNECTION_STRING=...
```

### Dependencias Python
```python
from azure.storage.blob import BlobClient, BlobSasPermissions, generate_blob_sas
from cosmos_client import insert_document, query_documents
from resend_client import send_email_with_template
```

---

## 🚀 COMANDOS ÚTILES

### Ver todas las herramientas disponibles
```
Usuario: "¿Qué herramientas tienes disponibles?"
Hernando: Retorna listar_servicios_disponibles()
```

### Verificar salud de servicios
```
Usuario: "¿Funcionan todos los servicios?"
Hernando: Retorna verificar_salud_servicios()
```

### Consultar servicio específico
```
Usuario: "¿Cómo está el servicio de Storage?"
Hernando: Retorna consultar_servicio_railway("azure_storage")
```

---

## 📞 SOPORTE

Si alguna herramienta no funciona:
1. Verifica las variables de entorno
2. Comprueba la salud de servicios Railway
3. Consulta los logs de Hernando
4. Contacta con el equipo de desarrollo

**Email:** contacto@fundomoraga.com  
**WhatsApp Admin:** +56941242609

---

**Última actualización:** 30 de Enero, 2026  
**Status:** ✅ Todas las herramientas funcionales  
**Versión:** 1.0

