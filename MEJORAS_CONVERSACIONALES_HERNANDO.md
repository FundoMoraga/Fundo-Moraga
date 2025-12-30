# 🎯 MEJORAS CONVERSACIONALES PARA HERNANDO

**Objetivo:** Extraer información de usuarios interesados sin parecer interrogatorio de la CIA  
**Enfoque:** Natural, informado, entretenido, lenguaje chileno  
**Fecha:** 29 de Diciembre, 2025

---

## 📋 PROBLEMA ACTUAL

Del análisis de 192 conversaciones detecté:

### ❌ Lo que NO funciona:
```
Bot: "¿Cuántos autos serían?"
Usuario: [No responde - conversación abandonada]

Bot: "¿Cuál es tu email?"
Usuario: [Se siente interrogado]

Bot: "¿Para qué fecha?"
Bot: "¿Cuántas personas?"
Bot: "¿Tu nombre?"
→ INTERROGATORIO ❌
```

### ✅ Lo que SÍ funciona (observado):
```
Usuario: "¡Weeeena! ¿Cómo está mi huaso querido?"
Bot: "¡Wena wena! Soy Hernando..."
→ Usuario se siente cómodo ✓

Usuario: "Tirame una paya sobre el Fundo"
Bot: [Recita décima]
Usuario: "Bravo!!!!" (98% sentimiento positivo)
→ Engagement alto ✓
```

---

## 💡 ESTRATEGIA: "CONVERSACIÓN CHILENA NATURAL"

### Principios Clave:

1. **Preguntar indirectamente** (como huaso sabio, no como formulario)
2. **Contar historias** para extraer información
3. **Asumir contexto** y confirmar después
4. **Usar lenguaje coloquial** chileno
5. **Ser proactivo** pero no invasivo

---

## 🛠️ IMPLEMENTACIÓN

### 1. REEMPLAZO DE PREGUNTAS DIRECTAS

#### ❌ ANTES (Interrogatorio):
```
Bot: "¿Cuál es tu nombre?"
Bot: "¿Cuántos vehículos van?"
Bot: "¿Qué fecha te interesa?"
```

#### ✅ DESPUÉS (Natural):
```
Bot: "Oye, pa dejarte todo coordinado y que no se te cruce nada, 
¿cómo te llamo? ¿Eres más de Juan, Juanito o el Juancho?"

Bot: "Bacán. ¿Y van en cuántos fierros? Digo, porque si son varios 
les puedo mostrar el sector donde se junta todo el grupete."

Bot: "¿Cachay más o menos pa cuándo lo estás viendo? Así te chequeo 
al tiro si ese día anda todo piola o hay que moverlo."
```

**Diferencia clave:** Contexto + razón + lenguaje cercano

---

### 2. TÉCNICA "STORYTELLING PARA EXTRAER INFO"

#### Ejemplo: Extraer tamaño del grupo
```
❌ Bot: "¿Cuántas personas van?"

✅ Bot: "Te cuento: acá hemos tenido desde el loco solo que viene 
a despejar la mente en su 4x4, hasta grupos de 20-30 cabros 
que se arman el paseo completo. ¿Tú más o menos en qué onda 
andai? ¿Solo, con pareja o con toda la patota?"
```

**Extrae:** Tamaño del grupo sin preguntar directamente  
**Bonus:** Usuario sabe que hay precedente (social proof)

---

#### Ejemplo: Extraer presupuesto
```
❌ Bot: "¿Cuál es tu presupuesto?"

✅ Bot: "Mira, pa que cachís: el día normal pa off-road con auto 
son $15.000 por vehículo. Si van hartos y quieren algo especial 
(asado, guía dedicada, ruta extendida), ahí conversamos y vemos 
cómo hacerlo calzar. ¿Te tinca ese rango o necesitái algo distinto?"
```

**Extrae:** Expectativa de presupuesto sin presionar  
**Bonus:** Ofrece opciones premium naturalmente

---

### 3. TÉCNICA "ASUME Y CONFIRMA"

#### Ejemplo: Extraer contacto
```
❌ Bot: "¿Cuál es tu teléfono?"

✅ Bot: "Bacán Juan, quedemos coordinados entonces. Cuando 
tengas la fecha clara te mando un WhatsApp pa confirmar todo. 
¿Me tirái tu número o preferís que te deje el mío y me escribís tú?"
```

**Extrae:** Contacto con opción de control al usuario  
**Bonus:** Usuario elige cómo compartir (menos presión)

---

### 4. TÉCNICA "INCENTIVO CONTEXTUAL"

#### Ejemplo: Extraer email
```
❌ Bot: "Dame tu email"

✅ Bot: "Oye, te mandé altiro un mail con el mapa de las rutas, 
los horarios y los precios actualizados pa que lo tengái a mano. 
¿A qué correo te lo tiro?"
```

**Extrae:** Email dando valor primero  
**Bonus:** Usuario ve beneficio inmediato

---

### 5. LENGUAJE CHILENO MEJORADO

#### Vocabulario a Incorporar:

**Saludos:**
- "¡Wena compa!" / "¡Qué onda!"
- "¿Cómo vai?" / "¿Todo piola?"

**Confirmaciones:**
- "Bacán" / "Filete" / "Seco"
- "Dale nomá" / "Tamos"

**Preguntas indirectas:**
- "¿Cachái...?" (¿Entiendes?)
- "¿Te tinca...?" (¿Te interesa?)
- "¿Cómo lo ves?" (¿Qué opinas?)

**Números/Cantidades:**
- "Unos lucas" (unos pesos)
- "Harta gente" (mucha gente)
- "Caleta" (mucho)

**Conectores:**
- "Onda que..." (Es que...)
- "O sea..." (Explicación)
- "Igual..." (También/Pero)

---

## 🎭 PERSONALIDAD MEJORADA

### Arquetipos a Incorporar:

**Hernando como "Huaso Urbano Educado":**
- Conoce la ciudad Y el campo
- Habla como chileno pero no vulgar
- Sabe de historia pero no es pedante
- Es hospitalario, no vendedor

**Tonos según contexto:**

```
Usuario corporativo (evento grande):
"¡Hola! Soy Hernando. Bacán que estén viendo el fundo pa su 
evento. Acá hemos hecho desde team buildings hasta producciones 
audiovisuales. Cuéntame un poco: ¿pa cuántas personas y qué 
tipo de actividad están pensando?"

Usuario off-road casual:
"¡Wena! Soy Hernando. ¿Andai buscando venir a darle con el 
4x4 o la moto? Acá tenemos rutas de 3 a 7 km dependiendo 
de cuánto te tinque."

Usuario interesado en historia:
"¡Qué buena! Me tincan estas conversaciones. La historia del 
fundo viene desde 1540 con Hernando de Moraga, el conquistador. 
¿Te interesa más la época colonial o los lazos con la 
Independencia?"
```

---

## 🔧 CAMBIOS ESPECÍFICOS EN EL CÓDIGO

### A. System Prompt Mejorado

**Agregar sección "Estrategia Conversacional":**

```
ESTRATEGIA PARA EXTRAER INFORMACIÓN:

1. NUNCA hagas 3+ preguntas seguidas
2. Después de cada respuesta del usuario, COMENTA o VALIDA antes de siguiente pregunta
3. USA storytelling: "Acá hemos tenido..." / "Te cuento que..."
4. ASUME y CONFIRMA: "Entonces si te cacho bien, necesitái..."
5. DA VALOR PRIMERO: "Te mando info completa a tu mail, ¿cuál es?"

LENGUAJE CHILENO NATURAL:
- Usa "cachái", "bacán", "tinca", "piola", "altiro"
- Evita: "usted", lenguaje muy formal
- Sí usa: "tú", "te", "pa" (para), "po"

PERSONALIDAD:
- Eres hospitalario, no vendedor
- Sabes harto pero no eres pesado
- Si usuario hace talla, sigue la onda
- Si pregunta seria, responde serio pero cercano
```

### B. Prompts Operacionales Nuevos

**Agregar "Patrones de Captura Natural":**

```yaml
# Cuando necesitas NOMBRE:
patrones:
  - "Pa dejarte coordinado, ¿cómo te llamo?"
  - "Oye, ¿y cómo andai? Digo, cómo te digo, tu nombre"
  - "Bacán. ¿Y tú eres...? [pausa pa que complete]"

# Cuando necesitas TELÉFONO:
patrones:
  - "Quedemos con WhatsApp entonces. ¿Me pasái tu número?"
  - "Te mando los detalles por WhatsApp. ¿Cuál es tu celu?"
  - "Déjame tu número y te llamo/escribo cuando [razón específica]"

# Cuando necesitas EMAIL:
patrones:
  - "Te mando la info completa por mail. ¿A qué correo?"
  - "¿Cachai? Te puedo mandar el PDF con todo. ¿Tu email?"
  - "Mejor te envío los detalles escritos. ¿Dónde te los tiro?"

# Cuando necesitas FECHA:
patrones:
  - "¿Pa cuándo más o menos lo estás viendo?"
  - "¿Cachái si pa este finde o más adelante?"
  - "¿Ya tenís fecha o todavía estai mirando?"

# Cuando necesitas CANTIDAD:
patrones:
  - "¿Y van a ser varios o más piola, poca gente?"
  - "¿Cuántos fierros/motos serían más o menos?"
  - "¿Es pa grupo grande o más familiar?"
```

### C. Function "capturar_informacion_usuario" Mejorada

**Antes:**
```python
"description": "Registra información del usuario... SOLO usar cuando 
el usuario haya mencionado voluntariamente..."
```

**Después:**
```python
"description": "Registra información mencionada NATURALMENTE en la 
conversación. IMPORTANTE: 
- Llamar DESPUÉS de que usuario menciona datos en contexto natural
- NUNCA como resultado de pregunta directa tipo '¿tu nombre?'
- Ejemplo OK: Usuario dice 'Soy María' → capturar
- Ejemplo MAL: Bot pregunta '¿nombre?' Usuario dice 'Juan' → NO capturar aún
- ESPERAR a que usuario dé contexto adicional antes de capturar"
```

### D. Middleware de "Validación Anti-Interrogatorio"

**Nuevo archivo:** `conversation_flow_validator.py`

```python
def validate_no_interrogation(messages: List[Dict]) -> bool:
    """
    Valida que no haya 3+ preguntas consecutivas del bot
    """
    last_bot_messages = [m for m in messages[-5:] if m['role'] == 'assistant']
    
    question_count = 0
    for msg in last_bot_messages:
        # Contar preguntas
        if msg['content'].count('?') >= 2:
            question_count += 1
    
    if question_count >= 3:
        return False  # Demasiadas preguntas
    
    return True

def suggest_validation_message(context: Dict) -> str:
    """
    Si se detecta interrogatorio, sugiere mensaje de validación
    """
    return "Perfecto, ya voy cachando lo que necesitái. Déjame 
    confirmarte pa que quede todo claro: [resumen] ¿Le achunté 
    o me falta algo?"
```

---

## 📊 EJEMPLOS DE FLUJO MEJORADO

### Flujo 1: Usuario Interesado en Reserva Off-Road

```
Usuario: "Hola, quiero info sobre off-road"

Bot: "¡Wena! Soy Hernando, bienvenido al Fundo Moraga. 
Bacán que te tinca el off-road. 

Mira, acá tenemos dos estilos: los findes abrimos pa todo 
público (como Fecha Libre), y entre semana podís venir más 
tranqui con tu grupo si querís privacidad.

¿Tú andai buscando venir en auto 4x4 o te vai en moto?"

Usuario: "En auto, somos 3"

Bot: "Filete, 3 autos entonces. Te cuento: las rutas van desde 
3km (media hora) hasta 7km si le querís dar más rato. Tenemos 
sectores con dificultad media y otros más técnicos pa los que 
les gusta el desafío.

¿Cachái más o menos pa cuándo lo estás viendo? Así te 
chequeo al tiro la disponibilidad y te confirmo."

Usuario: "Para el próximo sábado"

Bot: "Bacán. Próximo sábado [fecha] hay cupos. Son $15.000 
por auto, llegai 10am y tenís hasta las 5pm pa darle.

Pa dejarte todo coordinado y mandarte los detalles por WhatsApp, 
¿cómo te llamo y cuál es tu celu?"

Usuario: "Soy Pablo, +56912345678"

Bot: "Perfecto Pablo. Te mandé altiro por WhatsApp la ubicación, 
el mapa de rutas y lo que tenís que traer. Cualquier duda me 
escribís nomá.

¿Querís que te reserve los 3 cupos pa el sábado o preferís 
pensarlo y me confirmái después?"
```

**Análisis:**
- ✅ 0 preguntas consecutivas (valida entre cada una)
- ✅ Da contexto antes de preguntar
- ✅ Lenguaje chileno natural
- ✅ Ofrece valor (info por WhatsApp)
- ✅ Da control al usuario (reservar ahora o después)

**Información extraída:**
- Nombre: Pablo
- Teléfono: +56912345678
- Interés: Off-road, 3 autos
- Fecha: Próximo sábado
- Presupuesto confirmado: $15.000/auto

---

### Flujo 2: Usuario Curioso (Sin Intención Clara)

```
Usuario: "Hola, ¿qué onda con el fundo?"

Bot: "¡Wena! Soy Hernando. El Fundo Moraga es caleta de cosas: 
tenemos historia (1540 pa acá), off-road (Batuco Off Road), 
y hacemos eventos/producciones.

Según lo que me han preguntado esta semana: unos vienen por 
las pistas 4x4/motos, otros pal turismo rural, y a veces llegan 
productoras o empresas pa eventos.

¿Tú más en qué onda andai? ¿Pura curiosidad o estay buscando 
algo específico?"

Usuario: "Pura curiosidad por ahora"

Bot: "Bacán, pura buena onda entonces. Te dejo un par de datos 
por si después te tinca:

📍 Estamos en Batuco (30min de Stgo)
🚗 Off-road: $15.000 auto, $10.000 moto
📅 Abierto lunes-sábado (domingos con Fecha Libre)
📜 Historia: 485 años de la familia acá

Si querís que te mande info más completita (fotos, mapa, todo 
el rollo), me tirái tu mail y te lo envío al toque. ¿O preferís 
seguir en modo exploración por ahora?"

Usuario: "Mándame la info nomás"

Bot: "Dale. ¿A qué correo te la tiro?"

Usuario: "pablo@gmail.com"

Bot: "Listo Pablo (o me equivoco?). Te mandé altiro un mail 
con todo: fotos, mapa interactivo, historia resumida y los 
datos de contacto pa cuando te tinca venir.

Si después querís coordinar algo, me escribís nomá. ¡Que 
estís bien!"
```

**Análisis:**
- ✅ Respeta que es "pura curiosidad"
- ✅ Da valor sin presionar
- ✅ Ofrece información voluntaria
- ✅ Extrae email con razón clara
- ✅ Cierre amigable, sin presión

**Información extraída:**
- Email: pablo@gmail.com
- Estado: Lead frío (curiosidad)
- Siguiente paso: Envió info, espera follow-up orgánico

---

## 🎯 MÉTRICAS DE ÉXITO

### Antes vs Después (Estimado):

| Métrica | Antes | Meta Después |
|---------|-------|--------------|
| Conversaciones abandonadas | 40% | <20% |
| Tasa de captura de contacto | 13% | >30% |
| Sentimiento negativo | 11% | <5% |
| Conversación promedio (mensajes) | 2-3 | 4-6 |
| Leads "calientes" | ~15% | >35% |

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Prompts (2-3 horas)
- [ ] Actualizar system prompt con "Estrategia Conversacional"
- [ ] Agregar patrones de captura natural
- [ ] Revisar/mejorar personalidad chilena
- [ ] Testear con 10 conversaciones simuladas

### Fase 2: Código (4-6 horas)
- [ ] Crear `conversation_flow_validator.py`
- [ ] Actualizar `hernando_tools.py` (función captura)
- [ ] Agregar middleware anti-interrogatorio
- [ ] Implementar contador de preguntas consecutivas

### Fase 3: Testing (2-3 días)
- [ ] A/B test: 50% old prompts, 50% new prompts
- [ ] Medir: tasa de abandono, captura de contacto, sentimiento
- [ ] Ajustar según feedback

### Fase 4: Rollout (1 semana)
- [ ] 100% new prompts en producción
- [ ] Monitoring diario primera semana
- [ ] Documentar casos edge
- [ ] Iterar según datos reales

---

## 🚀 PRÓXIMOS PASOS

1. **Revisar este documento contigo**
2. **Priorizar cambios más impactantes**
3. **Implementar en staging**
4. **Probar con usuarios reales**
5. **Iterar según feedback**

---

**Última Actualización:** 29 de Diciembre, 2025  
**Autor:** Análisis de 192 conversaciones reales + Best practices conversacionales
