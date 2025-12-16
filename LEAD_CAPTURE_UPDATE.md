# ACTUALIZACIÓN: Captura Natural de Información y Envío de Leads

## Cambios Implementados

### 1. **Nueva Funcionalidad: Captura Natural de Información**

Hernando ahora puede capturar información del usuario de forma natural durante la conversación:

- **Nombre** de la persona
- **Qué quiere** (con máximos detalles)
- **Contacto** (móvil, email o ambos)

**IMPORTANTE:** La información se captura de forma orgánica en el flujo de conversación, NUNCA como un interrogatorio.

### 2. **Integración con Resend para Emails Automáticos**

Cuando se detecta que el usuario ha compartido su información, se envía automáticamente un email a `contacto@fundomoraga.com` con:

- Nombre del usuario
- Descripción detallada de su interés/consulta
- Información de contacto
- ID de conversación (para referencia en Cosmos DB)
- Plataforma de origen (Instagram/Web)
- Timestamp

### 3. **Información Actualizada de Actividades Off-Road**

Se agregó la información de horarios y precios:

```
HORARIOS Y PRECIOS OFF-ROAD:
- Lunes a Viernes: 9:00 AM - 5:00 PM
  * $15.000 automóviles
  * $10.000 motos

- Fin de Semana (Grupos):
  * $200.000 el día (por grupo, fin de semana)

- Eventos Privados/Corporativos:
  * Valores y condiciones personalizadas
  * Contactar: contacto@fundomoraga.com / +5694 1242609
```

## Archivos Modificados

### 1. **requirements.txt**
- Agregado: `resend>=0.8.0` para envío de emails

### 2. **.env y .env.example**
- Agregadas variables de entorno:
  ```
  RESEND_API_KEY=re_BrzA3z4r_QDaHQDQ988rgp3QTCnNBSBsf
  RESEND_FROM_EMAIL=hernando@fundomoraga.com
  RESEND_TO_EMAIL=contacto@fundomoraga.com
  ```

### 3. **resend_client.py** (NUEVO)
- Cliente de Resend para envío de emails
- Función `send_conversation_summary()` que envía resumen de lead
- Email con formato HTML profesional
- Manejo de errores robusto

### 4. **hernando_tools.py**
- Actualizada información de actividades Off-Road con horarios y precios
- Agregado nuevo tool: `capturar_informacion_usuario`
- Tool configurado para registrar información compartida naturalmente
- Retorna confirmación amigable al usuario

### 5. **openai_client.py**
- Actualizado system prompt con:
  - Información de horarios y precios Off-Road
  - Instrucciones detalladas para captura natural de información
  - Guías de cuándo usar la función `capturar_informacion_usuario`
  - Ejemplos de conversaciones naturales vs interrogatorios

### 6. **instagram_bot.py**
- Agregado import de `resend_client`
- Nueva función privada `_send_lead_email()` que:
  - Detecta cuando se capturó información
  - Extrae nombre, interés y contacto del historial
  - Envía email automático vía Resend
  - Maneja errores sin interrumpir el flujo

## Cómo Funciona el Flujo

1. **Usuario inicia conversación** con Hernando
2. **Usuario comparte información naturalmente**:
   - "Hola, soy Juan"
   - "Quiero cotizar un evento corporativo para 50 personas"
   - "Mi email es juan@ejemplo.com"

3. **Hernando detecta la información** compartida voluntariamente

4. **Se activa el tool** `capturar_informacion_usuario` automáticamente

5. **Hernando confirma** de forma amigable:
   ```
   ✅ Perfecto, Juan.
   
   He registrado tu consulta sobre evento corporativo para 50 personas.
   
   El equipo de Fundo Moraga recibirá esta información y te contactarán
   a través de juan@ejemplo.com para darte una atención personalizada.
   
   ¿Hay algo más en lo que pueda ayudarte?
   ```

6. **Automáticamente se envía email** a `contacto@fundomoraga.com` con:
   - Nombre: Juan
   - Interés: "Quiero cotizar un evento corporativo para 50 personas"
   - Contacto: juan@ejemplo.com
   - Plataforma: Instagram
   - ID Conversación: conv_20251215_143022_12345
   - Timestamp: 15/12/2025 14:30:22

## Ejemplo de Email Enviado

```html
🌿 Nuevo Lead - Fundo Moraga

Hernando ha tenido una conversación con un potencial cliente. Aquí está el resumen:

👤 Nombre: Juan Pérez

📝 Interés/Consulta:
Quiero cotizar un evento corporativo para 50 personas en febrero,
con actividades de team building y almuerzo incluido

📞 Contacto: juan.perez@empresa.com / +56 9 8765 4321

🔗 Plataforma: Instagram
🆔 ID Conversación: conv_20251215_143022_user123
📅 Fecha: 15/12/2025 14:30:22

---
Este mensaje fue generado automáticamente por Hernando, el asistente virtual de Fundo Moraga.
Para ver la conversación completa, revisa el registro en Cosmos DB con el ID proporcionado.
```

## Próximos Pasos

### 1. Instalar Nueva Dependencia
```powershell
pip install resend
```

### 2. Verificar Variables de Entorno
Las credenciales de Resend ya están configuradas en [.env](d:\repos\Fundo Moraga\FM IA\.env):
```
RESEND_API_KEY=re_BrzA3z4r_QDaHQDQ988rgp3QTCnNBSBsf
RESEND_FROM_EMAIL=hernando@fundomoraga.com
RESEND_TO_EMAIL=contacto@fundomoraga.com
```

### 3. Probar Localmente
```powershell
python instagram_bot.py
```

Simula una conversación donde compartes:
- Tu nombre
- Qué quieres hacer (evento, off-road, etc.)
- Tu email o teléfono

Verifica que:
1. Hernando responde de forma natural
2. Se imprime en consola "📋 Información capturada: ..."
3. Se envía el email (verifica en consola "✅ Email de lead enviado")
4. Recibes el email en contacto@fundomoraga.com

### 4. Desplegar a Railway
Una vez verificado localmente:
```powershell
git add .
git commit -m "feat: Captura natural de información y envío automático de leads con Resend"
git push origin main
```

Railway detectará los cambios y redesplegará automáticamente.

### 5. Configurar Dominio de Envío en Resend (Opcional pero Recomendado)

Para que los emails no vayan a spam:
1. Ve a [resend.com/domains](https://resend.com/domains)
2. Agrega el dominio `fundomoraga.com`
3. Configura los registros DNS (SPF, DKIM)
4. Verifica el dominio

## Características de Seguridad

1. **No interroga al usuario**: Todo fluye naturalmente
2. **Manejo de errores**: Si falla el envío de email, no afecta la conversación
3. **Validación de datos**: Solo envía si hay información útil
4. **Privacy**: La información solo se envía a contacto@fundomoraga.com
5. **Trazabilidad**: Cada email incluye ID de conversación para seguimiento

## Configuración de Resend

API Key ya configurada: `re_BrzA3z4r_QDaHQDQ988rgp3QTCnNBSBsf`

- **From:** hernando@fundomoraga.com
- **To:** contacto@fundomoraga.com
- **Límites (Plan Gratuito):** 3,000 emails/mes, 100 emails/día

Si necesitas aumentar límites o configurar dominio personalizado, contacta con Resend.

## Testing Checklist

- [ ] Instalar dependencia `resend`
- [ ] Verificar variables de entorno en .env
- [ ] Probar conversación local con captura de nombre
- [ ] Probar conversación local con captura de email
- [ ] Probar conversación local con captura de teléfono
- [ ] Verificar recepción de email en contacto@fundomoraga.com
- [ ] Verificar formato del email (HTML renderiza correctamente)
- [ ] Probar con consulta sobre evento corporativo
- [ ] Probar con consulta sobre actividades off-road
- [ ] Verificar precios nuevos de off-road en respuestas
- [ ] Deploy a Railway
- [ ] Probar en producción (Instagram)
- [ ] Probar en producción (Web)
- [ ] Configurar dominio en Resend (opcional)

## Soporte

Si tienes problemas:
1. Verifica que la API key de Resend esté correcta
2. Revisa los logs en consola para errores
3. Verifica que las variables de entorno estén cargadas
4. Confirma que el dominio `hernando@fundomoraga.com` esté verificado en Resend
