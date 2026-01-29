# Sistema de Conocimiento Doctoral para Efraín Moraga

## 📋 Resumen Ejecutivo

He creado un sistema de IA de **nivel doctoral** para que Hernando responda con expertise de élite cuando interactúe contigo. El sistema detecta automáticamente el área de tu consulta y activa conocimiento especializado en 11 disciplinas.

### Capacidades Premium Implementadas

- **Razonamiento doctoral**: Metodología académica rigurosa, análisis profundo, fundamentación en evidencia
- **11 áreas de expertise**: Desde tecnología hasta bricolaje, cada una con conocimiento de nivel PhD
- **Detección automática**: Keywords activan el área correcta sin necesidad de especificar
- **Modular y escalable**: Fácil agregar nuevas áreas o actualizar conocimiento

---

## 🎓 Áreas de Conocimiento Doctoral

### 1. **Tecnología**
- IA/ML (LLMs, RAG, fine-tuning, MLOps)
- Cloud Computing (Azure, AWS, serverless, Kubernetes)
- Ciberseguridad (Zero Trust, penetration testing, compliance)
- DevOps/SRE (CI/CD, observabilidad, platform engineering)
- Arquitectura de Software (DDD, microservicios, APIs)

**Ejemplo**: "¿Cómo implemento RAG para mi chatbot?" → Respuesta con arquitectura completa, embeddings, vector DB, chunking strategies, reranking

### 2. **Investigación General**
- Diseño de investigación (RCT, cuasi-experimental, mixtos)
- Metodología (muestreo, instrumentos, ética)
- Análisis estadístico (inferencial, multivariado, bayesiano)
- Revisión de literatura (PRISMA, meta-análisis)
- Escritura académica (IMRaD, peer review, grants)

**Ejemplo**: "¿Cómo diseño un estudio para evaluar X?" → Pregunta de investigación, diseño óptimo, tamaño muestral, análisis, consideraciones éticas

### 3. **Legislación de Chile (Abogado)**
- Derecho Civil (Código Civil, obligaciones, contratos, sucesiones)
- Derecho Comercial (sociedades, libre competencia, propiedad intelectual)
- Derecho Constitucional (derechos fundamentales, TC, recursos)
- Derecho Administrativo (acto administrativo, licitaciones, transparencia)
- Derecho Penal, Laboral, Tributario, Ambiental, Urbanístico

**Ejemplo**: "¿Qué permisos necesito para construir?" → Permiso edificación, factibilidad, DIA/EIA si aplica, subdivisión, normativa DOM

### 4. **Medicina**
- Medicina basada en evidencia (jerarquía, guías clínicas)
- Diagnóstico clínico (anamnesis, examen físico, diagnóstico diferencial)
- Patologías por sistemas (cardiología, respiratorio, gastro, endocrino, neurología)
- Farmacología clínica (farmacocinética, interacciones, RAM)
- Medicina preventiva y salud pública

**Ejemplo**: "Dolor torácico en hombre 55 años" → DD: SCA, TEP, disección aórtica, pericarditis, ERGE. Red flags: dolor opresivo, disnea → **EVALUACIÓN URGENTE**

### 5. **Veterinaria**
- Medicina equina (claudicaciones, cólico, reproducción, odontología)
- Medicina de ganado bovino (mastitis, reproducción, enfermedades infecciosas)
- Pequeños animales (medicina interna, cirugía)
- Enfermedades zoonóticas
- Farmacología veterinaria

**Ejemplo**: "Caballo cojo extremidad anterior" → Examen locomotor, palpación, flexiones, bloqueos diagnósticos, DD: navicular, osteoartritis, tendinitis

### 6. **Historia de Chile**
- Período precolombino (pueblos originarios, incas)
- Conquista y Colonia (1540-1810)
- Independencia (Patria Vieja, Reconquista, Patria Nueva)
- República Conservadora y Liberal (siglo XIX)
- Siglo XX (parlamentaria, radicales, Allende, dictadura, democracia)

**Ejemplo**: "¿Por qué fue importante la Guerra del Pacífico?" → Análisis multicausal (salitre, geopolítica), consecuencias territoriales, dependencia económica, legado contemporáneo

### 7. **Generación de Imágenes**
- Modelos (DALL-E 3, Midjourney, Stable Diffusion)
- Prompt engineering avanzado (estructura, componentes, técnicas)
- Teoría visual (composición, color, iluminación)
- Casos de uso (retratos, paisajes, concept art, producto)

**Ejemplo**: "Quiero una imagen de un fundo en Chile" → Prompt completo: "Aerial view of traditional Chilean fundo estate, rolling hills with vineyards, Spanish colonial hacienda with red tile roof, Andes mountains in background, golden hour lighting..."

### 8. **Creativo**
- Escritura creativa (narrativa, poesía, microrrelato)
- Copywriting (AIDA, headlines, landing pages, SEO)
- Ideación (brainstorming, SCAMPER, pensamiento lateral)
- Storytelling (estructura, aplicación profesional)
- Diseño de conceptos (naming, slogans, campañas)

**Ejemplo**: "Dame ideas para campaña de Z" → 3 conceptos diferentes, ejecución por canal, ejemplos de piezas, justificación estratégica

### 9. **Arquitectura**
- Diseño arquitectónico (proceso, principios, composición, espacios)
- Historia y teoría (movimientos, arquitectos referentes)
- Normativa chilena (LGUC, OGUC, plano regulador, permisos)
- Sustentabilidad (LEED, CES, estrategias pasivas/activas)
- Urbanismo, BIM

**Ejemplo**: "¿Cómo diseño una casa en terreno con pendiente?" → Estrategias: terrazas escalonadas, palafitos, corte del terreno, muros contención, orientación solar, referentes

### 10. **Construcción**
- Gestión de proyectos (fases, metodologías, roles, contratos)
- Planificación (Gantt, PERT/CPM, curva S)
- Presupuesto y cubicación (partidas, APU, presupuesto)
- Procesos constructivos (hormigón, albañilería, estructuras)
- Control de calidad y seguridad

**Ejemplo**: "¿Cómo presupuesto una casa de 100m²?" → Cubicación por partidas (preliminares, fundaciones, obra gruesa, instalaciones, terminaciones), APU típicos Chile, contingencia, total

### 11. **Bricolaje**
- Carpintería (maderas, herramientas, proyectos, acabados)
- Electricidad doméstica (conceptos básicos, reparaciones permitidas, seguridad)
- Plomería (materiales, reparaciones comunes, instalación artefactos)
- Reparaciones generales (muros, cerámicas, puertas, ventanas)
- Pintura, revestimientos, herramientas esenciales

**Ejemplo**: "¿Cómo instalo una repisa flotante?" → Materiales, herramientas, pasos numerados, tips (detector vigas, peso máximo), seguridad

---

## 🏗️ Arquitectura del Sistema

### Estructura de Archivos

```
prompts_doctorales/
├── estructura_doctoral.json          # Metadata del sistema
├── prompt_base_doctoral.json         # Razonamiento doctoral base (común a todas las áreas)
├── area_tecnologia.json              # Conocimiento específico de tecnología
├── area_investigacion.json           # Metodología científica
├── area_legislacion_chile.json       # Derecho chileno
├── area_medicina.json                # Medicina basada en evidencia
├── area_veterinaria.json             # Medicina veterinaria
├── area_historia_chile.json          # Historia nacional
├── area_generacion_imagenes.json     # Prompt engineering para imágenes
├── area_creativo.json                # Escritura y creatividad
├── area_arquitectura.json            # Diseño arquitectónico
├── area_construccion.json            # Gestión de proyectos construcción
└── area_bricolaje.json               # Reparaciones y DIY
```

### Flujo de Activación

```
Usuario (Efraín) envía mensaje
         ↓
openai_client.py detecta persona "efrain_moraga"
         ↓
_detect_doctoral_area() analiza keywords en mensaje + historial
         ↓
Si detecta área (ej: "tecnología"):
    _combine_doctoral_prompts()
         ↓
    Prompt Final = Prompt Base Doctoral + Knowledge Enhancement del Área
         ↓
GPT-5.2 responde con expertise doctoral en esa área
```

### Detección Inteligente de Contexto

Cada área tiene **keywords de activación**. Ejemplos:

- **Tecnología**: "IA", "cloud", "Azure", "API", "código", "DevOps"
- **Medicina**: "síntoma", "diagnóstico", "tratamiento", "dolor", "medicamento"
- **Legislación**: "ley", "contrato", "tribunal", "permiso", "derecho"
- **Construcción**: "construcción", "presupuesto", "obra", "partida", "hormigón"

El sistema cuenta matches y activa el área con más coincidencias.

---

## 📤 Instalación y Deployment

### Estado Actual

✅ **Archivos creados**: 13 archivos JSON en `prompts_doctorales/`
✅ **Código integrado**: `openai_client.py` modificado con detección y combinación automática
✅ **Script de upload**: `scripts/upload_prompts_doctorales.py` listo
❌ **Pendiente**: Subir prompts a Cosmos DB

### Pasos para Completar

#### Opción 1: Upload Manual desde Railway Dashboard

1. Conectar a Railway service "hernando" via SSH:
   ```bash
   railway shell
   ```

2. Dentro del shell, ejecutar:
   ```bash
   python scripts/upload_prompts_doctorales.py
   ```

3. Confirmar cuando pregunte (s/n)

#### Opción 2: Deploy via Git + Railway Auto-deploy

1. Commit y push los cambios:
   ```bash
   git add prompts_doctorales/ scripts/upload_prompts_doctorales.py openai_client.py docs/
   git commit -m "feat: Sistema de conocimiento doctoral con 11 áreas de expertise"
   git push origin main
   ```

2. Railway auto-desplegará el código actualizado

3. Ejecutar script manualmente una vez via Railway Shell:
   ```bash
   railway shell
   python scripts/upload_prompts_doctorales.py
   ```

#### Opción 3: Ejecutar Localmente (requiere Python + dependencias)

Si tienes Python instalado localmente con las dependencias del proyecto:

```bash
cd M:\VSC\Fundo-Moraga
python scripts/upload_prompts_doctorales.py
```

El script:
- ✅ Carga los 13 archivos JSON
- ✅ Valida estructura de cada prompt
- ✅ Se conecta a Cosmos DB (Database: "Entrenamiento", Container: "Hernando")
- ✅ Hace upsert (crea si no existe, actualiza si existe)
- ✅ Lista los prompts subidos como confirmación

---

## 🧪 Cómo Probar el Sistema

### 1. Después de Upload a Cosmos DB

Envía mensajes a Hernando desde tu WhatsApp (+56941242609):

**Probar Tecnología:**
```
"¿Cómo implemento vector search en Cosmos DB para RAG?"
```
Esperado: Respuesta con arquitectura técnica, MongoDB vCore, embeddings, chunking, código ejemplo

**Probar Medicina:**
```
"Tengo un caballo con claudicación en la mano izquierda, ¿qué podría ser?"
```
Esperado: Examen locomotor, diagnóstico diferencial (navicular, tendinitis, osteoartritis), pasos diagnósticos

**Probar Legislación:**
```
"¿Qué pasos legales necesito para constituir una SpA en Chile?"
```
Esperado: Escritura pública, estatutos, publicación, inscripción RCS, RUT, inicio actividades SII

**Probar Creativo:**
```
"Necesito un nombre creativo para una app de delivery de comida saludable"
```
Esperado: 5 opciones con diferentes enfoques (descriptivo, metafórico, inventado), explicación, verificación dominio

### 2. Verificar Detección de Área

Revisa logs de Railway para confirmar que se activa el área correcta:

```
🎓 Área doctoral detectada: tecnologia (3 keywords)
```

### 3. Comparar Respuestas

**Antes (sin sistema doctoral):**
Respuesta genérica, superficial, sin profundidad técnica

**Después (con sistema doctoral):**
Respuesta de experto PhD: análisis profundo, trade-offs, fundamentación, ejemplos concretos, recomendaciones accionables

---

## 🔧 Mantenimiento y Expansión

### Agregar Nueva Área de Conocimiento

1. Crear archivo JSON en `prompts_doctorales/`:

```json
{
  "id": "efrain_moraga_doctoral_NUEVA_AREA",
  "persona": "efrain_moraga_doctoral",
  "area": "nueva_area",
  "nivel": "doctoral_elite",
  "version": "1.0",
  "knowledge_enhancement": "**MODO DOCTORAL: NUEVA ÁREA**\n\n[Contenido experto aquí]",
  "keywords_activacion": ["keyword1", "keyword2", "keyword3"]
}
```

2. Ejecutar script de upload:
```bash
python scripts/upload_prompts_doctorales.py
```

3. El sistema automáticamente detectará y usará la nueva área

### Actualizar Conocimiento Existente

1. Editar el archivo JSON correspondiente en `prompts_doctorales/`
2. Ejecutar script de upload (hace upsert, no duplica)
3. El cambio es inmediato (próximo mensaje usa nueva versión)

### Ajustar Detección de Keywords

Si un área no se activa cuando debería:

1. Editar `keywords_activacion` en el JSON del área
2. Agregar más keywords relacionados
3. Re-upload a Cosmos DB

---

## 📊 Estructura de Datos en Cosmos DB

### Database: `Entrenamiento`
### Container: `Hernando`
### Partition Key: `/persona`

Cada documento tiene:

```json
{
  "id": "efrain_moraga_doctoral_tecnologia",
  "persona": "efrain_moraga_doctoral",
  "area": "tecnologia",
  "nivel": "doctoral_elite",
  "version": "1.0",
  "knowledge_enhancement": "...",
  "keywords_activacion": [...]
}
```

**Prompts existentes en Cosmos DB después del upload:**

- `efrain_moraga_doctoral_base` (prompt base común)
- `efrain_moraga_doctoral_tecnologia`
- `efrain_moraga_doctoral_investigacion`
- `efrain_moraga_doctoral_legislacion_chile`
- `efrain_moraga_doctoral_medicina`
- `efrain_moraga_doctoral_veterinaria`
- `efrain_moraga_doctoral_historia_chile`
- `efrain_moraga_doctoral_generacion_imagenes`
- `efrain_moraga_doctoral_creativo`
- `efrain_moraga_doctoral_arquitectura`
- `efrain_moraga_doctoral_construccion`
- `efrain_moraga_doctoral_bricolaje`

---

## 🎯 Beneficios del Sistema

### Para Efraín (Usuario Profesional)

- **Respuestas de élite**: Nivel académico superior en todas las áreas
- **Sin necesidad de especificar**: Sistema detecta automáticamente el contexto
- **Rigor intelectual**: Fundamentación, análisis profundo, múltiples perspectivas
- **Accionabilidad**: No solo teoría, sino pasos concretos y recomendaciones prácticas

### Para Hernando (Asistente)

- **Versatilidad**: De tecnología avanzada a reparaciones domésticas
- **Consistencia**: Metodología doctoral uniforme en todas las áreas
- **Escalabilidad**: Fácil agregar nuevas áreas sin modificar código
- **Mantenibilidad**: Actualizar conocimiento editando JSON, no código

### Técnicamente

- **Modular**: Cada área es independiente
- **Performance**: Lazy loading (carga solo cuando se necesita)
- **Caching**: Prompts se cachean en memoria después de primera carga
- **Fallback**: Si Cosmos DB falla, usa prompts embebidos estándar

---

## 📝 Notas Finales

### Disclaimers Importantes

Los prompts de **Medicina** y **Veterinaria** incluyen disclaimers claros:
- NO son diagnósticos definitivos
- NO reemplazan evaluación clínica presencial
- Emergencias requieren atención profesional inmediata

Los prompts de **Legislación** aclaran:
- NO constituyen asesoría legal formal
- Casos complejos requieren consulta con abogado
- Leyes pueden cambiar, verificar vigencia

### Limitaciones del Sistema

- **Detección de área**: Basada en keywords simple. Si mensaje es ambiguo, puede activar área incorrecta (o ninguna)
- **Un área a la vez**: No combina múltiples áreas en una respuesta (aunque el área puede cruzar conocimientos)
- **Conocimiento estático**: Requiere actualización manual de JSONs para nuevo conocimiento

### Próximas Mejoras Posibles

1. **Detección semántica**: Usar embeddings en lugar de keywords para detección más precisa
2. **Multi-área**: Combinar conocimiento de múltiples áreas cuando la consulta lo requiera
3. **RAG sobre conocimiento doctoral**: Indexar documentos académicos y papers para fundamentación dinámica
4. **Versionado**: Sistema de versiones para A/B testing de prompts
5. **Analytics**: Tracking de qué áreas se activan más frecuentemente

---

## ✅ Checklist de Implementación

- [x] Diseñar estructura modular
- [x] Crear prompt base doctoral
- [x] Generar 11 prompts especializados
- [x] Crear script de upload
- [x] Modificar openai_client.py
- [ ] **Ejecutar upload a Cosmos DB** ← **PENDIENTE**
- [x] Documentar sistema completo
- [ ] Probar con mensajes reales
- [ ] Ajustar keywords según uso real

---

**Creado**: 29 de enero de 2026
**Autor**: GitHub Copilot (Claude Sonnet 4.5)
**Para**: Efraín Moraga, Fundo Moraga
