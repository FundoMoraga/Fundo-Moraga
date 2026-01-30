# 🚀 Plan: Implementar Cache de OpenAI (-600-1200ms, -30%)

## 📋 Resumen Ejecutivo

**Objetivo:** Cachear respuestas de OpenAI para evitar llamadas innecesarias  
**Tiempo estimado:** 2 horas  
**Ganancia esperada:** -600-1200ms por consulta cacheada (30% mejora)  
**ROI:** 1:15 (excelente)

---

## 🎯 Estrategia de Cache

### Qué Cachear

Respuestas que probablemente se repiten (80% del uso):

1. **Preguntas Frecuentes Determinísticas**
   ```
   "¿Cuánto cuesta un tour?"
   "¿Qué es Batuco?"
   "¿Tienen WiFi?"
   "¿Qué vehículos se pueden usar?"
   ```
   - TTL: 24-48 horas
   - Cache hit rate: 40-60%

2. **Respuestas por Tipo de Usuario**
   ```
   Admin Efraín: "Acceso a todos los servicios"
   Usuario normal: "Acceso básico"
   Bot de IA: "Respuesta automática"
   ```
   - TTL: 7 días
   - Cache hit rate: 20-30%

3. **Preguntas sobre Ubicación/Información**
   ```
   "Dónde queda Batuco?"
   "¿Cómo llego a Fundo Moraga?"
   "¿Cuál es tu dirección?"
   ```
   - TTL: 30 días (estática)
   - Cache hit rate: 30-40%

### Qué NO Cachear

```
❌ Preguntas personalizadas (reservas específicas, historiales)
❌ Consultas dependientes de estado (¿quién soy? - depende de sesión)
❌ Análisis de imágenes (varía por imagen)
❌ Búsquedas web (contenido cambia)
❌ Información sensible (datos de pagos, números personales)
```

---

## 🔑 Estrategia de Keys de Cache

### Formato de Cache Key

```python
cache_key = f"openai:response:{hash(user_id)}:{hash(message_type)}:{hash(user_message[:100])}"

# Ejemplo:
cache_key = "openai:response:efrain:greeting:hola"
cache_key = "openai:response:usuario123:faq:que_es_batuco"
cache_key = "openai:response:admin:help:que_puedo_hacer"
```

### TTL por Tipo

| Tipo | TTL | Razón |
|------|-----|-------|
| Greeting | 7 días | "Hola" siempre es lo mismo |
| FAQ | 30 días | Información estática |
| Help | 7 días | Sistema no cambia frecuentemente |
| Info | 30 días | Ubicación, horarios = estático |
| Image Analysis | 24h | Puede cambiar modelo |
| Search | NO cachear | Contenido web cambia |
| Personal | NO cachear | Datos de usuario son únicos |

---

## 📊 Estructura de Datos en Cache

```json
{
  "key": "openai:response:...",
  "value": {
    "response": "Texto de la respuesta",
    "model": "gpt-5.2-2025-12-11",
    "created_at": "2026-01-30T14:30:00Z",
    "cached_at": "2026-01-30T14:30:05Z",
    "message_type": "greeting",
    "user_id": "efrain_moraga"
  },
  "ttl": 604800  // 7 días
}
```

---

## 🔄 Flujo de Ejecución

### Actual (sin cache): 2000-3000ms

```
Usuario: "Hola"
  ↓
generate_response()
  ↓
_build_messages()
  ↓
openai.ChatCompletion.create()  ← 2000-3000ms esperando
  ↓
Retorna: "Hola! Soy Hernando..."
```

### Con Cache: 1-10ms (en hit) o 2000-3000ms (en miss)

```
Usuario: "Hola"
  ↓
generate_response()
  ↓
_check_response_cache()  ← NUEVO
  ├─ HIT: Redis retorna en 1ms ✅ FIN
  └─ MISS: Continuar...
  ↓
_build_messages()
  ↓
openai.ChatCompletion.create()  ← 2000-3000ms
  ↓
_set_response_cache()  ← NUEVO
  ↓
Retorna: "Hola! Soy Hernando..."
```

---

## 💻 Cambios en Código

### 1. Nuevo método en `openai_client.py`: `_get_cache_key_for_response()`

```python
def _get_cache_key_for_response(
    self, 
    user_id: Optional[str], 
    user_message: str, 
    persona: Optional[str]
) -> Optional[str]:
    """
    Genera cache key para respuesta de OpenAI.
    Retorna None si la respuesta NO debe cachearse.
    
    Args:
        user_id: ID del usuario
        user_message: Mensaje original
        persona: Personalidad usada (si aplica)
    
    Returns:
        Cache key string, o None si no es cacheble
    """
    # Detectar si es consulta que debe cachearse
    msg_lower = user_message.lower().strip()
    
    # Patrones que SÍ se cachean
    cacheable_patterns = {
        "greeting": [r'^hola', r'^hi', r'^hey', r'^buenos'],
        "help": [r'^ayuda', r'^help', r'^qué puedo', r'^que me'],
        "about": [r'^qué eres', r'^quién eres', r'^que eres'],
        "faq": [r'^cómo', r'^cuánto', r'^dónde', r'^qué es'],
        "batuco": [r'batuco', r'tour', r'vehículos'],
    }
    
    message_type = None
    for msg_type, patterns in cacheable_patterns.items():
        if any(re.search(p, msg_lower) for p in patterns):
            message_type = msg_type
            break
    
    # Si no coincide con patrón cacheble, NO cachear
    if not message_type:
        return None
    
    # No cachear consultas personalizadas
    personal_keywords = ['mi reserva', 'mi número', 'mi email', 'mi nombre']
    if any(kw in msg_lower for kw in personal_keywords):
        return None
    
    # Generar key
    import hashlib
    key_parts = [
        "openai:response",
        message_type,
        user_message[:50]  # Primeros 50 caracteres
    ]
    key_hash = hashlib.md5(":".join(key_parts).encode()).hexdigest()
    return f"{':'.join(key_parts[:2])}:{key_hash}"
```

### 2. Nuevo método en `openai_client.py`: `_check_response_cache()`

```python
def _check_response_cache(self, cache_key: str) -> Optional[str]:
    """
    Busca respuesta en cache.
    
    Args:
        cache_key: Clave de cache (de _get_cache_key_for_response)
    
    Returns:
        Respuesta cacheada, o None si no existe
    """
    if not cache_key:
        return None
    
    try:
        from redis_cache import get_redis_cache_instance
        cache = get_redis_cache_instance()
        
        if not cache.enabled:
            return None
        
        cached_value = cache.client.get(cache_key)
        if cached_value:
            data = json.loads(cached_value)
            print(f"✅ Respuesta de OpenAI en caché (ahorra ~2s)")
            return data.get("response")
    except Exception as e:
        print(f"⚠️ Error al consultar cache: {e}")
    
    return None
```

### 3. Nuevo método en `openai_client.py`: `_set_response_cache()`

```python
def _set_response_cache(self, cache_key: str, response: str, message_type: str) -> None:
    """
    Guarda respuesta en cache.
    
    Args:
        cache_key: Clave de cache
        response: Texto de respuesta
        message_type: Tipo de mensaje (greeting, faq, etc.)
    """
    if not cache_key:
        return
    
    try:
        from redis_cache import get_redis_cache_instance
        cache = get_redis_cache_instance()
        
        if not cache.enabled:
            return
        
        # TTL por tipo de mensaje
        ttl_map = {
            "greeting": 7 * 24 * 3600,    # 7 días
            "help": 7 * 24 * 3600,        # 7 días
            "about": 30 * 24 * 3600,      # 30 días
            "faq": 30 * 24 * 3600,        # 30 días
            "batuco": 30 * 24 * 3600,     # 30 días
        }
        
        ttl = ttl_map.get(message_type, 7 * 24 * 3600)  # Default 7 días
        
        cache_data = {
            "response": response,
            "message_type": message_type,
            "created_at": datetime.now().isoformat(),
        }
        
        cache.client.setex(
            cache_key,
            ttl,
            json.dumps(cache_data)
        )
        print(f"💾 Respuesta guardada en caché (TTL: {ttl//3600}h)")
    except Exception as e:
        print(f"⚠️ Error al guardar en cache: {e}")
```

### 4. Modificar `generate_response()` para usar cache

```python
# Antes de generar, intentar cache:

# INSERTAR DESPUÉS de: "is_search_request = self._is_search_request(user_message)"

# Intentar obtener de cache (si es consulta cacheble)
cache_key = self._get_cache_key_for_response(user_id, user_message, persona_override)
if cached_response := self._check_response_cache(cache_key):
    return cached_response if not return_events else {
        "text": cached_response,
        "events": [],
        "model_used": "cache",
        "cached": True
    }

# ... resto del código ...

# ANTES DE: "return result if return_events else final_text"

# Cachear la respuesta si es aplicable
final_text = response_message.content or ""
if cache_key:
    message_type = cache_key.split(":")[2]
    self._set_response_cache(cache_key, final_text, message_type)
```

---

## 📈 Beneficios Esperados

### Cache Hit Scenarios

```
Escenario 1: Usuario Nuevo
├─ "Hola" → MISS (genera respuesta)
├─ "¿Qué es Batuco?" → MISS (genera respuesta)
├─ "Cuánto cuesta?" → MISS (genera respuesta)
└─ RESULT: 3 × 2000ms = 6000ms

Escenario 2: Usuario Después de 1 Hora
├─ "Hola" → HIT (1ms)
├─ "¿Qué es Batuco?" → HIT (1ms)
├─ "Cuánto cuesta?" → HIT (1ms)
└─ RESULT: 3 × 1ms = 3ms (99.95% mejora)

Escenario 3: Conversación Típica
├─ "Hola" → MISS (2000ms) → CACHEA
├─ Más preguntas...
├─ Mismo usuario regresa al día siguiente
├─ "Hola de nuevo" → HIT (1ms) = -1999ms
└─ RESULT: -80% de latencia en segundo contacto
```

### Impacto en Usuarios

```
Usuario Típico: 5 mensajes por sesión
├─ MISS 1: 2500ms
├─ MISS 2: 2000ms
├─ MISS 3: 2200ms
├─ HIT 4: 1ms (cache)
├─ HIT 5: 1ms (cache)
└─ TOTAL: 6700ms (vs 10700ms sin cache) = -37%

Para usuario que regresa al día siguiente:
├─ HIT 1: 1ms (cache)
├─ HIT 2: 1ms (cache)
├─ HIT 3: 1ms (cache)
├─ MISS 4: 2200ms (nueva pregunta)
└─ TOTAL: 2204ms (vs 10700ms primer día) = -79% mejora
```

---

## 🧪 Testing

### Test 1: Verificar cache key generation

```python
def test_cache_key_generation():
    """Verifica que las claves se generan correctamente"""
    client = ChatbotAI()
    
    # Should cachear
    key1 = client._get_cache_key_for_response("user1", "Hola", None)
    assert key1 is not None
    
    key2 = client._get_cache_key_for_response("user2", "¿Cuánto cuesta?", None)
    assert key2 is not None
    
    # Should NOT cachear
    key3 = client._get_cache_key_for_response("user1", "Mi reserva es mañana", None)
    assert key3 is None
```

### Test 2: Verificar cache hit/miss

```python
def test_cache_hit():
    """Verifica que el cache funciona"""
    client = ChatbotAI()
    
    # First call: MISS
    resp1 = client.generate_response("Hola", ...)
    
    # Second call: HIT
    start = time.time()
    resp2 = client.generate_response("Hola", ...)
    duration = time.time() - start
    
    assert resp1 == resp2  # Misma respuesta
    assert duration < 0.05  # Menos de 50ms (hit)
```

---

## 📋 Checklist de Implementación

```
[ ] Leer generate_response() completo
[ ] Implementar _get_cache_key_for_response()
[ ] Implementar _check_response_cache()
[ ] Implementar _set_response_cache()
[ ] Modificar generate_response() para usar cache
[ ] Agregar imports necesarios (json, hashlib, etc.)
[ ] Testing manual: Mensaje repetido
[ ] Testing manual: Verificar TTL
[ ] Verificar redis_cache.py tiene get_redis_cache_instance()
[ ] Hacer commit: "Agregar cache de respuestas OpenAI"
[ ] Verificar en Railway que Redis está conectado
```

---

## ⏱️ Timeline

```
1. Lectura de código:        15 min
2. Implementar métodos:       30 min
3. Modificar generate_response(): 20 min
4. Testing local:             20 min
5. Commit + Push:             10 min
────────────────────────────
TOTAL:                        95 min (~1.5 horas)
```

---

## 📊 Métricas de Éxito

```
✅ Cache Hit Rate: > 30%
✅ Latencia en HIT: < 10ms
✅ Latencia en MISS: 2000-3000ms (sin cambio)
✅ Error Rate: 0% (fallback correcto)
✅ Memory Usage: < 100MB en Redis (típico para cache)
```

---

**Status:** Ready to implement  
**Prioridad:** HIGH  
**Esfuerzo:** 2 horas  
**Ganancia:** -600-1200ms (-30%)  
