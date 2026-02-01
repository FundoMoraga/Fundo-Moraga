# 🔧 Redis en Railway - Guía de Configuración

## 📊 Estado Actual

### ❌ Problema Detectado
```
⚠️ No se pudo conectar a Redis: Error 111 connecting to hernando.railway.internal:6379. Connection refused.
```

### ✅ Variables Configuradas Correctamente
- `REDIS_ENABLED=true`
- `REDIS_URL=redis://default:gWVgRskUqCzynmeKKocQmluQJZYWAYTo@hernando.railway.internal:6379`
- `REDISHOST=hernando.railway.internal`
- `REDISPORT=6379`
- `REDISUSER=default`
- `REDISPASSWORD=gWVgRskUqCzynmeKKocQmluQJZYWAYTo`

## 🎯 Solución: Agregar Servicio Redis

El problema es que **no existe un servicio Redis activo en Railway**. Las variables están configuradas, pero el servicio no está levantado.

### Paso 1: Agregar Redis desde Railway Dashboard

1. **Acceder al proyecto en Railway**
   - Ir a: https://railway.app/
   - Seleccionar proyecto: "Fundo Moraga"
   - Entorno: "Hernando"

2. **Agregar nuevo servicio Redis**
   - Click en "+ New Service"
   - Seleccionar "Database"
   - Elegir "Redis"
   - Nombrar: `redis-hernando` (o similar)

3. **Railway automáticamente creará:**
   - ✅ `REDIS_URL` con credenciales
   - ✅ `REDIS_PRIVATE_URL` para uso interno
   - ✅ Variables `REDISHOST`, `REDISPORT`, `REDISUSER`, `REDISPASSWORD`

4. **Verificar que la URL privada use `.railway.internal`**
   - Debería ser algo como: `redis://default:password@redis.railway.internal:6379`

### Paso 2: Actualizar Variables en Servicio Hernando

Railway puede auto-inyectar las variables, pero si es necesario:

```bash
railway variables --set REDIS_URL=${{redis-hernando.REDIS_URL}}
```

O desde el dashboard:
- Ir a servicio "Hernando"
- Variables → Add Variable Reference
- Seleccionar `redis-hernando.REDIS_URL`

### Paso 3: Reiniciar Servicio

```bash
railway up --service Hernando
```

O desde dashboard:
- Servicio "Hernando" → Settings → Restart

## ✅ Verificación

Después del deploy, los logs deberían mostrar:

```
✅ Cache Redis conectado
```

En lugar de:

```
⚠️ No se pudo conectar a Redis: Error 111 connecting to...
```

## 📊 Beneficios de Redis Activado

Con Redis funcionando, el sistema tendrá:

1. **✅ Cache de Prompts** (TTL: 1 hora)
   - Respuestas frecuentes cacheadas
   - Reduce latencia en ~500ms por request

2. **✅ Cache de FAQs** (TTL: 30 días)
   - Preguntas comunes guardadas
   - Reduce llamadas a OpenAI

3. **✅ Cache Personal** (Habilitado)
   - Contexto de conversaciones
   - Memoria entre sesiones

4. **✅ Reducción de costos**
   - Menos llamadas a APIs externas
   - Respuestas instantáneas para queries comunes

## 🔍 Comandos Útiles

### Ver logs en tiempo real
```bash
railway logs --service Hernando
```

### Ver estado de servicios
```bash
railway status
```

### Ver variables actuales
```bash
railway variables
```

### Conectar a Redis CLI (si está corriendo)
```bash
railway run redis-cli -h redis.railway.internal -p 6379 -a $REDISPASSWORD
```

## 📝 Notas Importantes

1. **Railway maneja automáticamente DNS interno**
   - Los servicios pueden comunicarse usando `.railway.internal`
   - No se requiere configuración adicional de red

2. **Redis es opcional pero recomendado**
   - El bot funciona sin Redis (usa memoria local)
   - Pero pierde capacidades de cache persistente

3. **Costo de Redis**
   - Railway cobra por uso de recursos
   - Redis básico es relativamente económico
   - Considerar plan según tráfico esperado

## 🚀 Estado Post-Implementación

Una vez configurado Redis, el startup mostrará:

```
🔧 Configurando middleware de optimización...
✅ Security headers configurados
✅ Compresión gzip configurada
✅ Cache headers configurados
✅ Middleware configurado completamente

✅ Cache Redis conectado          ← ¡NUEVO!
✅ Manual de instrucciones cargado (10 capacidades)
✅ Cache personal habilitado      ← ¡NUEVO!

🚀 Bot mejorado inicializado con IA avanzada
   ✅ Cache Redis: 🟢 Habilitado  ← ¡NUEVO!
   ✅ Sentimiento: 🟢 Habilitado
   ✅ Timing: 🟢 Habilitado
   ✅ Satisfacción: 🟢 Habilitado
   🔐 Modo Admin: Disponible
```

---

**Fecha de creación**: 2026-02-01  
**Última actualización**: 2026-02-01  
**Estado**: Redis no configurado - Requiere acción manual en Railway
