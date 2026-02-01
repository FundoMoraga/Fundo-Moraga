# 🔌 Conexión de VSCode Redis Extension a Railway Redis

## ✅ Método Recomendado: VSCode Extension UI

### Paso 1: Instalar Redis Extension
Ya está instalada: **Redis for VS Code** (redis.redis-for-vscode)

### Paso 2: Configurar Conexión
1. **Abre VSCode**
2. **Abre la paleta de comandos:** `Ctrl + Shift + P`
3. **Busca:** `Redis: Add Database Connection`
4. **Rellena los datos:**
   - **Host:** `hernando.railway.internal`
   - **Port:** `6379`
   - **Username:** `default`
   - **Password:** `gWVgRskUqCzynmeKKocQmluQJZYWAYTo`
   - **Database:** `0`
   - **Name (opcional):** `Fundo Moraga`

5. **Presiona Enter**

### Paso 3: Ver Datos
En la barra lateral de VSCode, verás la conexión activa bajo "Redis Explorer"

---

## 📋 Credenciales de Conexión

```
Host: hernando.railway.internal
Port: 6379
User: default
Password: gWVgRskUqCzynmeKKocQmluQJZYWAYTo
Database: 0
Connection String: redis://default:gWVgRskUqCzynmeKKocQmluQJZYWAYTo@hernando.railway.internal:6379/0
```

---

## 🔧 Alternativa: Configuración Manual (settings.json)

1. **Abre settings.json:**
   - `Ctrl + ,` en VSCode
   - Busca: `redis.connections`
   - Click en "Edit in settings.json"

2. **Agrega (o actualiza):**

```json
"redis.connections": [
  {
    "label": "Fundo Moraga - Railway",
    "host": "hernando.railway.internal",
    "port": 6379,
    "auth": "gWVgRskUqCzynmeKKocQmluQJZYWAYTo",
    "username": "default",
    "database": 0
  }
]
```

3. **Guarda (Ctrl + S)**
4. **Recarga VSCode (o presiona F5)**

---

## 📊 Comandos Útiles en Redis

Una vez conectado, puedes ejecutar comandos en el panel de Redis:

```redis
# Ver todas las claves
KEYS *

# Contar claves
DBSIZE

# Ver estadísticas
INFO

# Ver uso de memoria
INFO memory

# Buscar claves específicas
KEYS prompts*

# Ver tipo de una clave
TYPE nombre_clave

# Ver contenido
GET nombre_clave

# Limpiar base de datos (CUIDADO!)
FLUSHDB

# Limpiar todo (MÁS CUIDADO!)
FLUSHALL
```

---

## 🔍 Verificación de Conexión

### En VSCode:
1. Abre la **Activity Bar** en la izquierda
2. Busca el icono de Redis
3. Bajo "Redis Explorer" deberías ver "Fundo Moraga - Railway"
4. Si ves un checkmark verde ✓ = Conectado
5. Si ves rojo X = Error de conexión

### Posibles Errores:

| Error | Causa | Solución |
|-------|-------|----------|
| "Connection refused" | Redis no está corriendo | Verifica que Redis en Railway está activo |
| "WRONGPASS" | Contraseña incorrecta | Copia exactamente: `gWVgRskUqCzynmeKKocQmluQJZYWAYTo` |
| "Cannot resolve host" | Host incorrecto | Usa: `hernando.railway.internal` |
| "Port X in use" | Puerto ya ocupado | Usa puerto diferente o mata el proceso anterior |

---

## 🚀 Monitorear Cache en Tiempo Real

Una vez conectado, puedes:

1. **Expandir la conexión** para ver todas las claves
2. **Click en una clave** para ver su contenido
3. **Buscar claves** con el campo de búsqueda
4. **Monitorear cambios** en tiempo real
5. **Ejecutar comandos** personalizados

---

## 📌 Notas Importantes

- ✅ La conexión `hernando.railway.internal` es **solo interna dentro de Railway**
- ✅ VSCode debe estar corriendo **en el mismo entorno** (o con acceso a Railway)
- ✅ La contraseña es segura (Railway la genera automáticamente)
- ✅ Puedes tener múltiples conexiones Redis en VSCode

---

**Fecha:** 2026-02-01
**Extension:** Redis for VS Code
**Estado:** Listo para conectar
