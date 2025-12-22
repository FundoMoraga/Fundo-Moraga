# 🔄 Actualización de Precios y Servicios - Batuco Off Road

## ⚠️ Cambios Necesarios en Cosmos DB

Necesitas actualizar el documento `hernando_personalidad_v1` en Cosmos DB con la siguiente información corregida:

---

## 📋 PRECIOS ACTUALIZADOS (Reemplazar en el Prompt)

### Ubicar en el JSON:
Busca la sección **🚙 ACTIVIDADES TODOTERRENO** y reemplaza con:

```
🚙 ACTIVIDADES TODOTERRENO:
Las actividades off-road son operadas EXCLUSIVAMENTE por Batuco Off Road:

HORARIOS:
- Lunes a Viernes: 9:00 AM - 5:00 PM
- Sábado: Solo grupos privados (reserva anticipada)
- Domingo: Generalmente cerrado, salvo "Fecha Libre" anunciada en Instagram

PRECIOS:
- Lunes a Viernes: $15.000 automóviles, $10.000 motos (por vehículo/día)
- Sábado y Domingo: $200.000 por día (arriendo completo del campo)
- EXCEPCIÓN "Fecha Libre": Cuando se anuncia por Instagram @batuco_offroad, se abre sábado o domingo con tarifa normal de semana ($15.000 vehículos / $10.000 motos)

SERVICIOS INCLUIDOS:
✅ Baño disponible en el lugar
✅ Rutas trazadas (la más larga: ~3 km, extensible hasta 7 km)
✅ Campo abierto para exploración
✅ Zona de estacionamiento

ACTIVIDADES:
- Rutas 4x4
- Enduro
- Experiencias todoterreno
- Eventos de aventura motorizada
- Eventos privados/corporativos: Valores y condiciones personalizadas

IMPORTANTE: 
- Para eventos privados/corporativos contactar: contacto@fundomoraga.com / +5699 9392122
- Las "Fechas Libres" se anuncian exclusivamente por Instagram (@batuco_offroad)
```

---

## 🎯 Información Específica sobre "Fecha Libre"

Agregar esta sección antes de "PREGUNTAS FRECUENTES":

```
## "FECHA LIBRE" - DOMINGOS ESPECIALES

¿Qué es una "Fecha Libre"?
- Son domingos especiales que abrimos al público con tarifa normal de semana
- Se anuncian con anticipación en Instagram: @batuco_offroad y @fundomoraga
- Horario: 10:00 AM - 5:00 PM
- Precio: $15.000 por automóvil, $10.000 por moto (igual que lunes a viernes)
- No es necesario arrendar el día completo

¿Cómo saber cuándo hay "Fecha Libre"?
- Revisa nuestro Instagram @batuco_offroad donde se publican con anticipación
- Síguenos para estar al tanto de estas oportunidades especiales
- Cuando pregunten por domingos, menciona esta opción y sugiere revisar Instagram

IMPORTANTE: 
- Los domingos regulares NO están disponibles (solo sábado con arriendo completo)
- "Fecha Libre" es la ÚNICA excepción para domingos
- Siempre deriva a Instagram para confirmar próximas fechas libres
```

---

## 📝 Actualización en PREGUNTAS FRECUENTES

Agregar estas dos preguntas:

```
¿Tienen baño disponible?
- Sí. Contamos con baño en el lugar para uso de visitantes.

¿Cuánto cuesta ir un fin de semana?
- Sábado y domingo: $200.000 por día (arriendo completo del campo)
- EXCEPCIÓN: En "Fechas Libres" (anunciadas por Instagram), el precio es el normal de semana: $15.000 vehículos / $10.000 motos
- Para sábados con grupos, coordinamos según disponibilidad
```

---

## 🔧 Cómo Actualizar en Cosmos DB

### Opción 1: Azure Portal
1. Ve a Azure Portal → Cosmos DB → Base de datos "Entrenamiento"
2. Contenedor "Hernando"
3. Busca item `hernando_personalidad_v1`
4. Click "Edit"
5. Reemplaza la sección de ACTIVIDADES TODOTERRENO
6. Agrega sección "FECHA LIBRE"
7. Actualiza PREGUNTAS FRECUENTES
8. Cambia `updatedAt` a fecha actual: `"2025-12-22T23:00:00Z"`
9. Click "Update"

### Opción 2: VS Code con Extension de Cosmos DB
1. Abre VS Code
2. Extension de Azure Cosmos DB
3. Navega a Entrenamiento → Hernando
4. Click derecho en `hernando_personalidad_v1` → "Edit"
5. Haz los cambios mencionados
6. Guarda

### Opción 3: Script Python (Automático)
```python
# Ejecutar desde terminal:
python scripts/actualizar_precios_batuco.py
```

---

## ✅ Verificación

Después de actualizar, prueba con Hernando:

**Prueba 1:**
```
Usuario: ¿Cuánto cuesta ir un sábado?
Hernando: Debería decir "$200.000 por día (arriendo completo)"
```

**Prueba 2:**
```
Usuario: ¿Tienen baño?
Hernando: Debería decir "Sí, contamos con baño disponible"
```

**Prueba 3:**
```
Usuario: ¿Qué es una fecha libre?
Hernando: Debería explicar domingos especiales con tarifa normal
```

---

## 📱 Nota sobre Instagram

Asegúrate de que Hernando recomiende seguir:
- @fundomoraga (contenido general del fundo)
- @batuco_offroad (anuncios de fechas libres y actividades)

---

## 🚨 CRÍTICO - Resumen de Cambios

1. ✅ **Precio sábado/domingo**: $200.000/día (arriendo completo)
2. ✅ **Fecha Libre**: Domingos especiales con $15.000 vehículos / $10.000 motos
3. ✅ **Baño**: Disponible en el lugar
4. ✅ **Anuncio**: Fechas libres se publican en Instagram @batuco_offroad

