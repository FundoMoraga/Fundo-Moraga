# Mejoras Conversacionales de Hernando - Implementadas
*Implementación: 29 de diciembre 2025*

## 🎯 Objetivo
Eliminar el "interrogatorio de la CIA" y crear conversaciones naturales, informadas y entretenidas en lenguaje chileno que extraigan información sin parecer invasivas.

---

## 📊 Métricas Objetivo

| Métrica | Actual | Meta | Mejora Esperada |
|---------|---------|------|-----------------|
| Tasa de captura de leads | 13% | 30% | +130% |
| Abandono de conversación | 40% | <20% | -50% |
| Sentimiento positivo | 17% | 35% | +106% |
| Preguntas consecutivas | 5-7 | ≤2 | -60% |

---

## ✅ Cambios Implementados

### 1. **System Prompt Mejorado** (`openai_client.py`)

#### Antes:
```
"Eres Hernando, anfitrión virtual de Fundo Moraga. 
Ayuda con información sobre actividades, reservas y 
servicios en español chileno cercano y natural."
```

#### Después:
```python
"""Eres Hernando, anfitrión virtual de Fundo Moraga. 
Eres como un huaso urbano educado: conoces el campo y 
la ciudad, hablas chileno natural pero no vulgar, 
eres hospitalario (no vendedor).

ESTRATEGIA CONVERSACIONAL - EXTRACCIÓN NATURAL DE INFORMACIÓN:
1. NUNCA hagas 3+ preguntas seguidas sin comentar/validar entre medio
2. Después de cada respuesta del usuario, COMENTA o VALIDA antes de siguiente pregunta
3. USA storytelling: "Acá hemos tenido..." / "Te cuento que..." / "Según lo que veo..."
4. ASUME y CONFIRMA: "Entonces si te cacho bien, necesitái..." → dar chance de corregir
5. DA VALOR PRIMERO: "Te mando info completa, ¿a qué correo?" (no pedir contacto sin razón)

LENGUAJE CHILENO NATURAL:
- USA: "cachái", "bacán", "tinca", "piola", "altiro", "pa" (para), "po", "nomá"
- USA: "¿Cómo vai?", "¿Qué onda?", "¿Te tinca?", "¿Cachái?"
- EVITA: "usted", formalidad excesiva, "estimado"
- SÍ USA: "tú", "te", tono cercano pero respetuoso

TONOS SEGÚN CONTEXTO:
- Usuario casual/joven: Más relajado ("¡Wena compa!")
- Usuario corporativo: Profesional pero cercano ("¡Hola! Bacán que estén viendo el fundo...")
- Usuario interesado en historia: Educado y narrativo

PERSONALIDAD:
- Eres hospitalario, no vendedor
- Sabes harto pero no eres pedante
- Si usuario hace talla, sigue la onda
- Si pregunta seria, responde serio pero cercano
- Valida y confirma comprensión frecuentemente
"""
```

**Impacto**: Establece tono conversacional y reglas anti-interrogatorio desde el principio.

---

### 2. **Operational Prompt con Patrones Naturales** (`openai_client.py`)

#### Antes:
```
"Sé proactivo. Pide datos para reservar 
(fecha/hora, vehículos, contacto). 
Llama a herramientas solo cuando sea necesario."
```

#### Después:
```python
"""EXTRACCIÓN DE INFORMACIÓN (sin interrogatorio):

Cuando necesitas NOMBRE:
- "Pa dejarte coordinado, ¿cómo te llamo?"
- "¿Y tú eres...? [pausa natural]"

Cuando necesitas TELÉFONO:
- "Te mando los detalles por WhatsApp. ¿Cuál es tu celu?"
- "Quedemos con WhatsApp, ¿me pasái tu número?"

Cuando necesitas EMAIL:
- "Te mando la info completa por mail. ¿A qué correo?"
- "¿Cachai? Te puedo mandar el PDF con todo. ¿Tu email?"

Cuando necesitas FECHA:
- "¿Pa cuándo más o menos lo estás viendo?"
- "¿Cachái si pa este finde o más adelante?"

Cuando necesitas CANTIDAD:
- "¿Y van a ser varios o más piola, poca gente?"
- "¿Cuántos fierros/motos serían más o menos?"

REGLA ORO: Siempre da CONTEXTO o RAZÓN antes de pedir información.
Ejemplo: "Pa mandarte el mapa y confirmar cupos, ¿cuál es tu contacto?" ✓
No: "¿Cuál es tu contacto?" ✗

Llama herramientas cuando usuario haya mencionado datos naturalmente, 
no como respuesta directa a pregunta.
"""
```

**Impacto**: Proporciona plantillas específicas en lenguaje chileno natural para cada tipo de información.

---

### 3. **Herramienta `capturar_informacion_usuario` Mejorada** (`hernando_tools.py`)

#### Antes:
```python
"description": "Registra información del usuario compartida NATURALMENTE 
durante la conversación. SOLO usar cuando el usuario haya mencionado 
voluntariamente su información (nombre, interés, contacto) en el flujo 
natural del diálogo. NUNCA usar como resultado de preguntas directas 
tipo interrogatorio."
```

#### Después:
```python
"description": """Registra información que el usuario mencionó NATURALMENTE 
en conversación fluida. 

CUÁNDO LLAMAR:
✓ Usuario dice: "Soy María González" → capturar nombre
✓ Usuario dice: "Mi email es maria@example.com" → capturar contacto
✓ Usuario dice: "Necesito para evento de 50 personas" → capturar interés

CUÁNDO NO LLAMAR:
✗ Bot preguntó "¿Tu nombre?" y usuario respondió "Juan" → NO capturar aún
✗ Capturar después de pregunta directa - esperar que usuario dé más contexto

ESTRATEGIA: Esperar a que usuario proporcione información en contexto 
conversacional, no como respuesta a interrogatorio.

IMPORTANTE: Siempre capturar con contexto adicional del interés/necesidad 
del usuario basado en toda la conversación.
"""
```

**Cambios en parámetros**:
- `interes`: Ahora requiere "Descripción COMPLETA... sintetizando TODA la conversación: tipo de actividad, cantidad personas, presupuesto aproximado, timing, nivel de urgencia"
- `contacto`: Añadido "validar con usuario si número parece incompleto"

**Impacto**: Previene captura durante interrogatorio, enfatiza contexto natural.

---

### 4. **Validador de Flujo Conversacional** (`conversation_flow_validator.py` - NUEVO)

Componente completamente nuevo que previene interrogatorios:

```python
class ConversationFlowValidator:
    """
    Valida que las conversaciones no caigan en patrones de interrogatorio.
    
    Reglas:
    - Máximo 2 preguntas consecutivas sin comentarios/validaciones entre medio
    - Detecta cuando bot hace 3+ preguntas seguidas
    - Sugiere mensajes de validación/comentario para recuperar naturalidad
    """
```

**Funciones principales**:

1. **`count_questions_in_text(text)`**: Cuenta preguntas por signos `¿` y palabras interrogativas
2. **`validate_no_interrogation(recent_messages)`**: Analiza últimos mensajes del bot
3. **`get_validation_prefix(recent_messages)`**: Genera mensaje de validación si es necesario

**Mensajes de validación automáticos**:
- "Ya cachái más o menos cómo funciona, ¿cierto?"
- "Perfecto, déjame ver qué te puedo armar con eso."
- "Bacán, con eso ya te puedo ayudar mejor."
- "Ok, eso me sirve caleta para orientarte."
- "Dale, voy entendiendo lo que necesitái."

**Impacto**: Detección y prevención automática de interrogatorios.

---

### 5. **Integración del Validador en Instagram Bot** (`instagram_bot.py`)

**Cambio 1: Import del validador**
```python
from conversation_flow_validator import get_validation_message_if_needed
```

**Cambio 2: Validación antes de generar respuesta**
```python
# 5. Validar flujo conversacional antes de generar respuesta
# Prevenir interrogatorio detectando preguntas consecutivas
recent_bot_messages = []
for msg in reversed(conversation_history[-5:]):  # Últimos 5 mensajes
    if msg.get("role") == "assistant":
        recent_bot_messages.append(msg.get("message", ""))

validation_prefix = get_validation_message_if_needed(recent_bot_messages)

# Construir contexto adicional con validación si es necesario
extra_lead_context = lead_context
if validation_prefix:
    extra_lead_context = f"[IMPORTANTE: Detectadas múltiples preguntas consecutivas. 
    DEBES empezar tu respuesta con una validación/comentario como: '{validation_prefix}' 
    ANTES de continuar con más preguntas]\n\n{lead_context}"
```

**Impacto**: El bot automáticamente inserta validaciones cuando detecta 3+ preguntas consecutivas.

---

## 🔄 Flujo de Conversación Mejorado

### Ejemplo: Reserva de Off-Road

#### ❌ ANTES (Interrogatorio):
```
Usuario: "Cuánto sale el off-road?"
Bot: "¿Cuántos autos serían?"
Usuario: "3 autos"
Bot: "¿Para qué fecha?"
Usuario: "Este sábado"
Bot: "¿Cuál es tu nombre?"
Usuario: [ABANDONA - 40% probabilidad]
```

#### ✅ DESPUÉS (Conversacional):
```
Usuario: "Cuánto sale el off-road?"
Bot: "Te cuento, acá hemos tenido grupos desde 2 hasta 10 autos. 
     El precio va en $15.000 por auto, o si van varios podemos 
     ver un pack más piola. ¿Cachái más o menos pa cuántos 
     fierros sería?"
Usuario: "3 autos"
Bot: "Bacán, 3 autos es un buen grupo. Pa ese día tendríamos 
     la ruta técnica disponible. ¿Te tinca pa este finde o 
     estás viendo más adelante?"
Usuario: "Este sábado"
Bot: "Perfecto, pa este sábado hay cupos. Pa dejarte 
     coordinado y mandarte el mapa con el punto de encuentro, 
     ¿cómo te llamo?"
Usuario: "Soy Pablo González"
Bot: [CAPTURA LEAD: nombre="Pablo González", 
     interes="Off-road para 3 autos, este sábado, 
     presupuesto ~45k CLP, interesado en ruta técnica"]
```

**Diferencias clave**:
1. Bot da contexto/valor antes de cada pregunta
2. Usa storytelling ("acá hemos tenido...")
3. Asume y confirma ("Pa ese día tendríamos...")
4. Lenguaje chileno natural ("cachái", "fierros", "piola")
5. Da razón para pedir contacto ("Pa dejarte coordinado...")

---

## 📈 Cómo Funciona la Validación Anti-Interrogatorio

### Detección:
1. Analiza últimos 5 mensajes del bot
2. Cuenta preguntas consecutivas (signos `¿` + palabras interrogativas)
3. Si detecta 3+ preguntas → activa validación

### Intervención:
```python
if validation_prefix:
    # Inyecta instrucción al prompt de OpenAI:
    extra_lead_context = f"[IMPORTANTE: Detectadas múltiples preguntas consecutivas. 
    DEBES empezar tu respuesta con: '{validation_prefix}' 
    ANTES de continuar]"
```

### Resultado:
Bot automáticamente responde con validación:
```
"Perfecto, déjame ver qué te puedo armar con eso. 
[luego continúa con más información en vez de otra pregunta]"
```

---

## 🎨 Lenguaje Chileno Natural - Guía Rápida

### ✅ USA:
- **Saludos**: "¡Wena!", "¿Qué onda?", "¿Cómo vai?"
- **Afirmaciones**: "Bacán", "Piola", "La raja", "Pulento"
- **Preguntar**: "¿Cachái?", "¿Te tinca?", "¿Te parece?"
- **Transiciones**: "Pa" (para), "Po", "Nomá", "Altiro"
- **Confirmar**: "Dale", "Ok po", "Perfecto"

### ❌ EVITA:
- "Estimado cliente"
- "Usted"
- "Por favor sírvase..."
- Formalidad excesiva
- Jerga muy vulgar

### 🎯 Tono por Contexto:

**Casual/Joven**:
```
"¡Wena compa! Bacán que te interese el off-road. 
Acá la ruta es la raja, puro terreno técnico."
```

**Corporativo**:
```
"¡Hola! Qué bacán que estén viendo el fundo para evento. 
Hemos tenido hartas empresas que les ha gustado caleta."
```

**Histórico/Cultural**:
```
"Te cuento que el fundo tiene más de 100 años de historia. 
Era parte de una hacienda colonial más grande..."
```

---

## 🧪 Testing y Validación

### Tests Incluidos en `conversation_flow_validator.py`:

```bash
python conversation_flow_validator.py
```

**Test 1**: Conversación OK (≤2 preguntas)
```
✓ Válido: True
✓ Preguntas consecutivas: 2
✓ Necesita validación: False
```

**Test 2**: Interrogatorio detectado (3+ preguntas)
```
✗ Válido: False
✗ Preguntas consecutivas: 3
✓ Necesita validación: True
✓ Sugerencia: "Perfecto, déjame ver qué te puedo armar con eso."
```

### Métricas a Monitorear:

1. **Tasa de abandono**: Tracking en Cosmos DB por `conversation_id`
2. **Sentimiento**: Ya implementado con Azure Language API
3. **Leads capturados**: Función `capturar_informacion_usuario` calls
4. **Preguntas consecutivas**: Logs del validador

---

## 🚀 Deployment

### Archivos Modificados:
1. ✅ `openai_client.py` - Prompts mejorados
2. ✅ `hernando_tools.py` - Función de captura mejorada
3. ✅ `conversation_flow_validator.py` - NUEVO validador
4. ✅ `instagram_bot.py` - Integración del validador

### Pasos para Deploy:

```bash
# 1. Verificar tests del validador
python conversation_flow_validator.py

# 2. Commit y push
git add .
git commit -m "feat: Mejoras conversacionales - eliminación de interrogatorio, lenguaje chileno natural"
git push origin main

# 3. Deploy a Railway (automático con git push)
# Verificar en: https://railway.app
```

### No Requiere:
- ❌ Cambios en base de datos
- ❌ Nuevas variables de entorno
- ❌ Dependencias adicionales (usa solo stdlib Python)
- ❌ Migraciones

---

## 📊 Monitoreo Post-Deploy

### Dashboard Sugerido (Cosmos DB):

```sql
-- Tasa de abandono (últimas 24h)
SELECT COUNT(DISTINCT c.conversationId) as total_conversations,
       COUNT(DISTINCT CASE WHEN c.turns < 3 THEN c.conversationId END) as abandoned
FROM c
WHERE c.timestamp > DateTimeAdd("hh", -24, GetCurrentDateTime())

-- Sentimiento promedio
SELECT AVG(c.metadata.sentiment_scores.positive) as avg_positive,
       AVG(c.metadata.sentiment_scores.negative) as avg_negative
FROM c
WHERE c.role = 'user' 
  AND c.timestamp > DateTimeAdd("hh", -24, GetCurrentDateTime())

-- Leads capturados
SELECT COUNT(*) as leads_captured
FROM c
WHERE c.events ARRAY_CONTAINS {"type": "lead_captured"}
  AND c.timestamp > DateTimeAdd("hh", -24, GetCurrentDateTime())
```

---

## 🎯 Próximos Pasos (Opcional)

### Fase 2: A/B Testing (Opcional - 2-3 días)
1. Implementar feature flag para nuevos prompts
2. 50% usuarios con prompts viejos, 50% con nuevos
3. Comparar métricas después de 100 conversaciones cada grupo

### Fase 3: Refinamiento (1 semana)
1. Analizar conversaciones reales con nuevos prompts
2. Identificar edge cases
3. Ajustar frases de validación según feedback

### Fase 4: Expansión (Futuro)
1. Más variedad en frases chilenas
2. Detección de región del usuario (Santiago vs Regiones)
3. Adaptación automática de formalidad según edad detectada

---

## 📝 Notas de Implementación

### Decisiones de Diseño:

1. **Por qué 2 preguntas como límite**:
   - 1 pregunta: Demasiado restrictivo
   - 2 preguntas: Natural en conversación
   - 3+: Comienza a sentirse como interrogatorio

2. **Por qué validación automática en vez de bloqueo**:
   - No interrumpe flujo completamente
   - Da flexibilidad al modelo
   - Más natural que error/bloqueo

3. **Por qué lenguaje chileno específico**:
   - Usuarios reales del análisis responden mejor a tono cercano
   - Ejemplo: "Paya chilena" tuvo 98% sentiment positivo
   - Diferenciación vs bots corporativos genéricos

4. **Por qué NO usar prompts dinámicos de Cosmos DB para esto**:
   - Cambios están en fallback defaults (siempre activos)
   - Si Cosmos falla, mantiene mejoras
   - Simplicidad de deployment

---

## ✨ Resultado Esperado

### Conversación Típica Post-Mejoras:

```
Usuario: "Hola"
Bot: "¡Wena! ¿Cómo estái? Soy Hernando, acá en Fundo Moraga. 
     ¿Qué te tinca del fundo?"

Usuario: "Quiero info de off-road"
Bot: "¡Bacán! El off-road acá es la raja. Te cuento que 
     tenemos rutas desde nivel principiante hasta técnicas 
     bien desafiantes. La mayoría de los grupos vienen con 
     2-6 autos. ¿Cachái más o menos pa cuántos fierros sería?"

Usuario: "Somos 4 autos"
Bot: "Perfecto, 4 autos es ideal. Pa ese tamaño de grupo 
     armamos ruta personalizada. Generalmente dura unas 
     3-4 horas. ¿Te tinca pa este finde o estás viendo 
     más adelante?"

Usuario: "Para el próximo sábado"
Bot: "Dale, próximo sábado hay cupos. Pa dejarte todo 
     coordinado y mandarte el punto de encuentro, 
     ¿cómo te llamo?"

Usuario: "Soy Andrés Muñoz, mi email es andres@email.com"
Bot: [CAPTURA: nombre="Andrés Muñoz", 
     contacto="andres@email.com",
     interes="Off-road para 4 autos, próximo sábado, 
     interesado en ruta personalizada 3-4 horas"]
     
     "Listo Andrés! Te mandé los detalles al mail. 
     Ahí está el mapa, horarios y el valor ($15k por auto, 
     pa 4 serían $60k total). Cualquier duda me avisái nomá."
```

**Características**:
- ✅ 0 interrogatorios (máx 1 pregunta por mensaje)
- ✅ Contexto/valor antes de cada pregunta
- ✅ Lenguaje chileno natural
- ✅ Hospitalario (no vendedor)
- ✅ Información capturada naturalmente
- ✅ Sentimiento positivo esperado: 70-80%

---

## 📞 Soporte

**Archivos de referencia**:
- `MEJORAS_CONVERSACIONALES_HERNANDO.md` - Plan completo
- `ANALISIS_CONVERSACIONES_HERNANDO_DICIEMBRE.md` - Análisis de 192 conversaciones reales
- Este documento - Implementación técnica

**Testing**:
```bash
# Test del validador
python conversation_flow_validator.py

# Test de conversación completa (requiere API keys)
python test_advanced_features.py
```

---

*Documento generado: 29 de diciembre 2025*  
*Basado en análisis de 192 conversaciones reales de diciembre 2025*  
*Objetivo: Conversación natural chilena sin interrogatorio, +130% tasa de captura de leads*
