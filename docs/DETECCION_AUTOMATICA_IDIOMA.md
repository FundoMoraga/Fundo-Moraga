# Detección Automática de Idioma y Mejoras de Redacción

## Descripción

A partir de commit `680800f`, Hernando incluye detección automática de idioma y sugerencias de mejoras de redacción **en segundo plano** para usuarios autorizados (como Efraín).

## Cómo Funciona

### 1. **Detección Automática de Idioma**
- Cuando un usuario autorizado escribe un mensaje en **otro idioma** (no español), Hernando lo detecta automáticamente
- Se utiliza Azure Language Service para identificar el idioma del texto
- El resultado se incorpora en el system prompt para que la respuesta sea contextualmente adecuada

### 2. **Mejoras de Redacción**
- Si el mensaje está en español, se pueden sugerir mejoras de claridad y estilo
- Las sugerencias se aplican en segundo plano sin afectar la latencia de respuesta

### 3. **Integración con Herramientas Existentes**
Las herramientas utilizadas son:
- `detectar_idioma_texto`: Identifica el idioma del mensaje
- `extraer_frases_clave`: Extrae conceptos clave para análisis
- `analizar_sentimiento_texto`: Analiza tono del mensaje (opcional)

Estas herramientas están **restringidas a usuarios autorizados**:
```python
if private_knowledge.is_authorized_user(user_id):
    # Ejecutar detección de idioma
    language_analysis = self._detect_language_and_suggest_improvements(...)
```

## Ejemplos

### Caso 1: Mensaje en Portugués
```
Usuario: "Olá, gostaria de saber mais sobre as atividades de turismo"
```

**Proceso:**
1. Hernando detecta: `detectado_idioma: "pt"`
2. Se marca: `translation_needed: True`
3. Se inyecta en system prompt: "El usuario escribió en portugués. Considera responder en español y ofrecerle traducción si lo necesita."
4. Respuesta: Hernando responde en español amable con opción de traducción

### Caso 2: Mensaje en Español
```
Usuario: "necesito info sobre les cabays"
```

**Proceso:**
1. Hernando detecta: `detectado_idioma: "es"`
2. Se analiza para mejoras de redacción
3. No se marca como necesitando traducción
4. Respuesta: Responde con claridad

## Arquitectura Técnica

### Métodos Nuevos en `openai_client.py`

#### `_detect_language_and_suggest_improvements(user_message, user_id)`
```python
def _detect_language_and_suggest_improvements(self, user_message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    - Verifica si usuario está autorizado
    - Llama a language_client.detect_language()
    - Retorna dict con: detected_language, language_suggestions, translation_needed
    """
```

#### `_apply_language_analysis_to_system_prompt(system_prompt, language_analysis)`
```python
def _apply_language_analysis_to_system_prompt(self, system_prompt: str, language_analysis: Dict[str, Any]) -> str:
    """
    - Enriquece el system prompt con contexto de idioma
    - Agrega notas sobre idioma detectado
    - Retorna system prompt mejorado
    """
```

### Flujo de Integración

```
generate_response(user_message, user_id, ...)
    ↓
_detect_language_and_suggest_improvements(user_message, user_id)
    ↓ (solo si is_authorized_user)
language_client.detect_language(user_message)
    ↓
_apply_language_analysis_to_system_prompt(system_prompt, language_analysis)
    ↓
_build_messages(..., system_prompt=enriquecido)
    ↓
_generate_with_model(...) → respuesta
```

## Configuración

No requiere configuración adicional. El sistema:
- Usa `language_client` existente (con HTTP Railway o Azure fallback)
- Respeta autorizaciones de `private_knowledge`
- Se ejecuta en segundo plano sin bloquear respuesta

## Limitaciones

1. **Idiomas soportados**: Depende de Azure Language Service (85+ idiomas)
2. **Latencia**: Minimal (llamadas no bloqueantes en segundo plano)
3. **Authorization**: Solo para usuarios con `is_authorized_user() = True`
4. **Detección simple**: Basada en idioma del texto, no en contexto conversacional

## Próximas Mejoras

- [ ] Traducción automática de respuestas a idioma detectado
- [ ] Almacenamiento de preferencias de idioma por usuario
- [ ] Análisis de sentimiento más profundo
- [ ] Recomendaciones de estilo basadas en tipo de contenido

## Testing

Para verificar funcionamiento:

```python
# Test 1: Usuario no autorizado
chatbot.generate_response(
    "Hello, I need help", 
    user_id="unknown_user"
)
# → language_analysis no se ejecuta

# Test 2: Usuario autorizado en otro idioma
chatbot.generate_response(
    "Bonjour, j'ai besoin d'aide", 
    user_id="efrain_moraga"
)
# → Detecta "fr", retorna "translation_needed: True"

# Test 3: Usuario autorizado en español
chatbot.generate_response(
    "Necesito información sobre actividades", 
    user_id="efrain_moraga"
)
# → Detecta "es", retorna "translation_needed: False"
```

---

**Commit**: `680800f`  
**Fecha**: 29 de Enero, 2026  
**Autor**: Sistema Automático
