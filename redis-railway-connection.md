# Configuración de Redis - VSCode Extension

## Datos de Conexión

**Host (Interno Railway):** `hernando.railway.internal`
**Host (Externo - si es necesario):** Requiere Port Forwarding
**Puerto:** `6379`
**Usuario:** `default`
**Contraseña:** `gWVgRskUqCzynmeKKocQmluQJZYWAYTo`
**Base de Datos:** `0` (por defecto)

## Opción 1: Conexión a través de Railway CLI (Recomendado)

Este método es seguro porque usa la autenticación de Railway:

```bash
# Terminal PowerShell
$env:REDIS_HOST = "127.0.0.1"
$env:REDIS_PORT = "6379"

# Opcional: Crear un alias para usar fácilmente
function Connect-RedisLocal {
    & "M:\Railway\railway.exe" run redis-cli -h hernando.railway.internal -p 6379 -a gWVgRskUqCzynmeKKocQmluQJZYWAYTo
}
```

## Opción 2: VSCode Redis Extension Configuration

1. **Abre la Paleta de Comandos:** `Ctrl+Shift+P`

2. **Busca:** "Redis: Add Database Connection"

3. **Ingresa los datos:**
   - **Host:** `127.0.0.1`
   - **Port:** `6379`
   - **Username:** `default`
   - **Password:** `gWVgRskUqCzynmeKKocQmluQJZYWAYTo`
   - **Database:** `0`
   - **Connection Name:** `Fundo Moraga - Railroad`

4. **Click en "Save"**

## Opción 3: Archivo de Configuración (JSON)

Edita o crea el archivo de configuración de la extensión Redis:

**Ruta:** `%APPDATA%\Code\User\settings.json`

```json
{
  "redis.connections": [
    {
      "label": "Fundo Moraga - Railway",
      "host": "127.0.0.1",
      "port": 6379,
      "auth": "gWVgRskUqCzynmeKKocQmluQJZYWAYTo",
      "name": "default"
    }
  ]
}
```

## Paso para usar Railway CLI como proxy local

Si eliges Opción 1, primero levanta el proxy:

```powershell
# En una terminal PowerShell separada, ejecuta:
& "M:\Railway\railway.exe" run redis-cli -h hernando.railway.internal -p 6379 -a gWVgRskUqCzynmeKKocQmluQJZYWAYTo

# Esto abrirá una conexión interactiva a Redis
# Luego en otra terminal, usa redis-cli localmente
redis-cli -h 127.0.0.1 -p 6379 -a gWVgRskUqCzynmeKKocQmluQJZYWAYTo
```

## Verificar Conexión

```bash
# Usar redis-cli para probar
redis-cli -h 127.0.0.1 -p 6379 -a gWVgRskUqCzynmeKKocQmluQJZYWAYTo ping

# Debería retornar: "PONG"
```

## Comandos Útiles en Redis CLI

```bash
# Ver todas las claves
KEYS *

# Ver estadísticas
INFO

# Ver uso de memoria
INFO memory

# Limpiar todo (CUIDADO!)
FLUSHALL

# Ver tipo de dato
TYPE nombre_clave

# Ver contenido de una clave
GET nombre_clave
```

## Troubleshooting

### Error: "Connection refused"
- Verifica que el servicio Redis en Railway está activo
- Confirma credenciales

### Error: "WRONGPASS invalid username-password pair"
- Verifica que la contraseña es exacta: `gWVgRskUqCzynmeKKocQmluQJZYWAYTo`
- Recopia desde Railway si es necesario

### Error: "Cannot connect to hostname"
- Asegúrate que estás usando `hernando.railway.internal` (SOLO dentro de Railway)
- Para acceso externo, necesitas Port Forwarding o exponer Redis públicamente

---

**Última actualización:** 2026-02-01
