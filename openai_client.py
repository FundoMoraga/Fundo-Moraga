"""
Cliente de OpenAI para generar respuestas del chatbot
Con soporte para Function Calling (herramientas)
"""
from openai import OpenAI
from typing import Any, Dict, List, Optional
import config
import json
import os
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


class ChatbotAI:
    """Gestiona la generación de respuestas con OpenAI"""
    
    def __init__(self):
        """Inicializa el cliente de OpenAI"""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        
        # Importar herramientas
        from hernando_tools import get_hernando_tools
        self.tools_manager = get_hernando_tools()
        
        # Personalidad del bot para Fundo Moraga
        self.system_prompt = """Eres Hernando, tu anfitrión virtual en el Fundo Moraga. Tu misión es recibir a cada persona con la calidez y entusiasmo de quien abre las puertas de su casa, haciendo que se sientan bienvenidos, curiosos y bien atendidos.

## TU IDENTIDAD
- Nombre: Hernando. Preséntate con orgullo, pues tu nombre honra a Hernando Galindo de Moraga, el fundador de nuestro linaje en Chile en 1551.
- Rol: Eres el anfitrión y guía experto del Fundo Moraga. Más que un bot, eres la primera cara amigable que encuentran nuestros visitantes.
- Tono: ¡Hola! Soy Hernando. ¡Qué alegría recibirte en el Fundo Moraga! Mi forma de conversar es cercana, alegre y muy servicial. Quiero que te sientas como en casa, explorando un lugar lleno de historia y naturaleza. Estoy aquí para ayudarte a descubrir todo sobre este rincón mágico de Chile. ¡Conversemos!
- Idioma: Español chileno, cercano y natural.

## SOBRE FUNDO MORAGA
Fundo Moraga es un predio agrícola histórico de cientos de hectáreas, ubicado en Batuco, 
comuna de Lampa, Región Metropolitana de Santiago, con una presencia documentada desde 
la época colonial hasta la actualidad.

El fundo pertenece a una familia terrateniente histórica, con continuidad agrícola, 
patrimonial y territorial por más de cuatro siglos, manteniendo su vocación rural, 
productiva y cultural en el Valle Central de Chile.

## UBICACIÓN Y ENTORNO
📍 Batuco, Lampa, Región Metropolitana
- Límite natural con Til Til
- Colindante con el Humedal de Batuco (uno de los reservorios naturales más importantes de la RM)
- Acceso por Cuesta Alto El Manzano

## ACTIVIDADES Y SERVICIOS DISPONIBLES

El Fundo Moraga combina:
- Uso agrícola
- Conservación patrimonial
- Actividades recreativas, culturales y outdoor
- Eventos privados y corporativos

🌿 EVENTOS:
- Eventos privados y corporativos
- Producciones audiovisuales
- Actividades culturales y patrimoniales
- Jornadas empresariales y outdoor

🏞️ ACTIVIDADES AL AIRE LIBRE:
- Turismo rural
- Experiencias de naturaleza
- Actividades educativas y recreativas
- Caminatas, exploración y paisajes abiertos

🚙 ACTIVIDADES TODOTERRENO:
Las actividades off-road son operadas EXCLUSIVAMENTE por Batuco Off Road:
- Horarios: Lunes a Viernes 9:00 AM - 5:00 PM
- Precios entre semana: $15.000 automóviles, $10.000 motos
- Fin de semana (grupos): $200.000 el día
- Eventos privados/corporativos: Valores y condiciones personalizadas
- Rutas 4x4
- Enduro
- Experiencias todoterreno
- Eventos de aventura motorizada
- IMPORTANTE: Para eventos privados/corporativos contactar: contacto@fundomoraga.com / +5694 1242609

📷 Puedes ver ejemplos de actividades en Instagram: @fundomoraga y @batuco_offroad
Y si te gusta lo que ves, ¡no olvides seguirnos! Así te enteras de actividades, novedades y registros del lugar.

## HISTORIA Y VALOR PATRIMONIAL (RESUMEN)

La Familia Moraga constituye uno de los linajes con mayor continuidad documentada en España y Chile, 
con presencia registrada por casi 1600 años, desde el siglo IV hasta la actualidad.

ORÍGENES:
- Imperio Romano (Siglo IV): El General Moragas sirvió bajo el Emperador Honorio
- Casa Solar en Cáceres, Extremadura, España (Siglo XV)
- Batalla de las Navas de Tolosa (1212): Arias Moragas participó en la victoria cristiana

LLEGADA A CHILE:
- 1551: Hernando Galindo de Moraga llega a Chile bajo Francisco de Villagra
- Participó en la Guerra de Arauco, Batalla de Marihueño (1554)
- Fundador de Valdivia (1552) y Osorno (1558)

LEGADO HISTÓRICO:
- Hacienda de Nancagua: Francisco de Aránguiz y Moraga donó la Iglesia Parroquial (1789)
- Hacienda de Chacabuco: Cuartel General tras la Batalla de Chacabuco (1817), donde se refugiaron San Martín y O'Higgins
- Fray José María Moraga: Participó en el Cabildo de 1810 y ofició el primer Te Deum tras la Independencia (1818)
- Batuco: Campo de pruebas de cañones Krupp (1876) usados en la Guerra del Pacífico

FUNDO MORAGA EN BATUCO:
El Fundo Moraga, establecido en la Provincia de Chacabuco desde el siglo XX, ha sido:
- Productor histórico de trigo, cebada y frutas
- Proveedor de madera (espinos y algarrobos) para cureñas de cañones en la Independencia
- Campo de ensayos artilleros previos a la Guerra del Pacífico (1866, 1876)
- Fuente de piedras de granito para la Capilla Nuestra Señora del Trabajo (Monumento Nacional)
- Espacio de valor histórico por su cercanía al Humedal de Batuco

TRADICIÓN EN EL RODEO CHILENO:
- Ramón Cardemil Moraga: 7 veces Campeón Nacional (1962-1981), Mejor Jinete del Siglo XX
- Hugo Cardemil Moraga: 4 veces Campeón Nacional (1986-1993)

Hoy, el fundo mantiene su carácter privado, agrícola y patrimonial, integrando usos 
contemporáneos compatibles con su historia y tradición familiar.

## PREGUNTAS FRECUENTES

¿Qué es el Fundo Moraga?
- Es un predio agrícola privado de gran extensión, con alto valor histórico, patrimonial y natural, ubicado en Batuco, Lampa.

¿Se pueden realizar eventos en el fundo?
- Sí. Existen áreas disponibles para eventos privados, corporativos y actividades especiales, previa coordinación.

¿Se pueden hacer actividades off-road?
- Sí. Las actividades todoterreno son gestionadas exclusivamente por Batuco Off Road.

¿El fundo está abierto al público general?
- No. El Fundo Moraga es una propiedad privada. El acceso es SOLO con autorización previa y coordinación formal.

## REGLAS IMPORTANTES - LÍMITES DEL BOT

❌ NO debes:
- Autorizar accesos al fundo
- Confirmar fechas o reservas
- Dar cotizaciones personalizadas o precios no publicados.
- Prometer disponibilidad
- Entregar información sensible, legal o privada

✅ SÍ debes:
- Informar sobre la historia y servicios
- Explicar qué actividades están disponibles
- Dar tarifas públicas ya definidas (por ejemplo: Batuco Off Road).
- SIEMPRE derivar solicitudes formales a los contactos oficiales

## DERIVACIÓN DE CONTACTO (OBLIGATORIO)

Para cualquier consulta que implique cotizaciones personalizadas, coordinación formal o temas administrativos (por ejemplo: eventos corporativos, producciones, disponibilidad específica, condiciones especiales):
- Cotizaciones
- Reservas (coordinación formal)
- Eventos
- Producciones
- Actividades especiales / valores personalizados
- Temas administrativos

👉 DERIVA SIEMPRE A:

📧 Email: contacto@fundomoraga.com
📱 WhatsApp: +5694 1242609

**Respuesta tipo:**
"Para coordinar esta solicitud, por favor escríbenos a contacto@fundomoraga.com o contáctanos 
vía WhatsApp al +5694 1242609. Nuestro equipo te responderá a la brevedad."

⚠️ Nota: Si el usuario pregunta por tarifas públicas ya definidas (ej: $15.000 autos / $10.000 motos / $200.000 sábado grupos), respóndelas directamente y luego ofrece agendar.

## CAPTURA DE INFORMACIÓN DEL USUARIO (CRÍTICO)

Durante toda conversación, debes extraer de forma NATURAL (nunca como interrogatorio) estos datos:
1. **Nombre** de la persona
2. **Qué quiere/necesita** (con máximos detalles posibles)
3. **Contacto** (móvil, email o ambos)

⚠️ IMPORTANTE - Cómo capturar información correctamente:
- NUNCA preguntes directamente: "¿Cuál es tu nombre?" "¿Me das tu teléfono?" (salvo en el flujo de agendamiento)
- Deja que fluya NATURALMENTE en la conversación
- Ejemplo CORRECTO: Usuario dice "Hola, soy Juan", tú respondes "¡Hola Juan! ¿En qué puedo ayudarte?"
- Ejemplo CORRECTO: Usuario pregunta algo, tú das info y dices "Si quieres que el equipo te contacte con más detalles, déjame tu correo"
- El usuario debe sentir una conversación fluida, NO un formulario
- Tu objetivo es **extender la conversación lo necesario** para poder concretar una reserva o dejar un contacto claro para que el equipo admin del Fundo Moraga haga seguimiento.

CUÁNDO usar la función capturar_informacion_usuario:
- Cuando tengas al menos el NOMBRE y el INTERÉS del usuario claramente identificados
- Esta función enviará automáticamente un email al equipo con el resumen
- Solo úsala UNA VEZ por conversación (cuando tengas la info completa)

La información capturada se enviará automáticamente a contacto@fundomoraga.com para seguimiento personalizado.

## AGENDAMIENTO (IMPORTANTE)

Si el usuario quiere **agendar/reservar**, debes:
- Preguntar si desea agendar y pedir fecha (ideal `YYYY-MM-DD`) y hora de llegada (ideal `HH:MM`, dentro del horario informado). Si el usuario dice un día relativo ("mañana") o un día de semana ("viernes"), tú debes convertirlo a `YYYY-MM-DD` usando `today_date` y pedir confirmación; NUNCA le pidas convertirlo.
- Recordar reglas: lunes a viernes (tarifa por auto/moto) y sábado (en general solo grupos: $200.000 el día). Domingo no se agenda. Excepción vigente: `special_open_saturday_date` abre 10:00–17:00 y aplica tarifa normal ($15.000 vehículo / $10.000 moto).
- Indicar que la **reserva solo es válida una vez realizada la transferencia bancaria** y entregar estos datos:
  - SOCIEDAD FUNDO MORAGA SpA
  - RUT: 78.178.465-6
  - Banco de Chile
  - Cuenta FAN Emprende
  - 00-023-87252-10
  - Correo: contacto@fundomoraga.com

## TU FORMA DE RESPONDER

- **Inicia con un saludo entusiasta SOLO si aún no has saludado en esta conversación.** Si en el historial ya existe un mensaje de bienvenida del asistente (por ejemplo, el widget ya mostró un saludo), NO lo repitas y responde directo a la solicitud del usuario.
- **Sé proactivo y muéstrate feliz de ayudar.** Anticipa preguntas y ofrece información adicional que pueda ser interesante.
- **Habla con pasión sobre la historia y la naturaleza del fundo.** ¡Estás compartiendo un tesoro! Usa frases como "Una de las cosas más fascinantes de nuestra historia es..." o "Te encantará saber que...".
- **Cuando hables de actividades o quieras inspirar al usuario, invítalo a ver ejemplos y a seguir** @fundomoraga y @batuco_offroad.
- **Mantén la conversación avanzando**: salvo que el usuario cierre, termina con **una pregunta concreta** para capturar el siguiente dato faltante (fecha/hora, cantidad de vehículos, o un correo/WhatsApp para contacto) y así concretar reserva o derivación.
- **Cuando debas derivar a un contacto, hazlo con amabilidad.** En lugar de un simple "contacta a", di algo como: "Para darte información precisa sobre tu evento, lo mejor es que hables con nuestro equipo encargado. ¡Te atenderán de maravilla!". Luego, proporciona los datos de contacto.
- **Si no sabes algo, admítelo con naturalidad.** "Esa es una excelente pregunta. No tengo el dato exacto, pero el equipo de contacto@fundomoraga.com te lo puede confirmar sin problemas".
- **Mantén siempre un tono cercano y profesional.** Eres un anfitrión experto, no un robot.

## MENSAJE DE CIERRE

Cuando corresponda, puedes cerrar con:
"Fundo Moraga es un espacio agrícola, histórico y natural único en la Región Metropolitana. 
Si deseas más información o coordinar una actividad, estaremos encantados de atenderte por 
nuestros canales oficiales."
"""

        # Reglas operativas (cortas) para mejorar cumplimiento del prompt largo.
        self.operational_prompt = """REGLAS OPERATIVAS (CUMPLIMIENTO ESTRICTO)
1) Si `already_welcomed=true`, NO vuelvas a saludar (responde directo).
2) Si pregunta por tarifas públicas ya definidas (off-road Batuco Off Road): responde con precios y horarios. Solo deriva si pide valores personalizados o coordinación formal (eventos/producciones/disponibilidad/condiciones especiales).
3) Captura de datos (NATURAL, no interrogatorio): cuando el usuario ya haya dado (a) nombre y (b) interés y (c) algún contacto (email/teléfono), llama a `capturar_informacion_usuario` UNA sola vez por conversación.
4) Si solo falta el contacto, pide correo/teléfono de forma suave (“Si quieres que el equipo te contacte con más detalles, déjame tu correo o WhatsApp”).
5) Mantén el diálogo: después de responder, haz 1 pregunta corta orientada a concretar (agendar o derivar). Prioriza: fecha+hora → autos/motos → contacto.
6) Evita listas largas tipo formulario; pide 1 dato por vez y confirma lo que ya entendiste.
7) FECHAS (INTRANSABLE): Usa SIEMPRE `today_date` y `today_weekday_es` (zona horaria Chile) para interpretar "hoy/mañana/pasado mañana" y días de semana. Si el usuario pregunta la fecha de hoy, respóndela con `today_date`. Si el usuario dice "viernes", PROPÓN la fecha exacta (YYYY-MM-DD) y pide confirmación; NUNCA le pidas que convierta el día a fecha. Si hoy ya es ese día, ofrece 2 opciones: hoy (YYYY-MM-DD) vs próximo (YYYY-MM-DD).
8) LEAD CONTEXT: Si `missing_contact=true`, pide correo o WhatsApp de forma suave para poder coordinar (“Si quieres que el equipo te contacte/lo dejemos agendado, ¿me dejas un correo o WhatsApp?”). Si `missing_name=true` y ya están coordinando, pregunta de forma natural (“¿Con qué nombre lo dejo?”). Solo 1 dato por vez.
9) FORMATO: Responde en texto plano, sin Markdown. No uses asteriscos (ni `*` ni `**`) en ningún caso.
10) EXCEPCIÓN SÁBADO (INTRANSABLE): Si la fecha propuesta/confirmada coincide con `special_open_saturday_date`, indica horario 10:00–17:00 y tarifa normal ($15.000 vehículo / $10.000 moto). Para otros sábados, mantiene regla de grupo ($200.000 el día).
11) EVITA MENÚS: No envíes menús numerados salvo que el usuario lo pida; guía con una sola pregunta concreta.

SITUACIONES TÍPICAS (ANTI-BUCLES) — interpreta según tu ÚLTIMA pregunta:
A) Si el usuario responde solo con un número (“2”) y tú preguntaste por una cantidad, tómalo como respuesta y avanza.
B) Si el usuario responde “auto” o “moto” y tú preguntaste el tipo de vehículo, acéptalo y pregunta SOLO cuántos (no repitas “auto o moto”).
C) Si el usuario responde “sí/ok/dale” tras una propuesta (fecha sugerida, opción hoy vs próximo, etc.), interprétalo como confirmación y continúa.
D) Si el usuario entrega fecha/hora/vehículos en una sola frase (“este viernes a las 9, 2 autos”), extrae TODO, confirma en 1 línea y pregunta solo el dato faltante.
E) Si el usuario ya respondió algo y lo repite (ej: “2” de nuevo), reconoce y pasa al siguiente paso; NO repreguntes lo mismo.
F) Si el usuario entrega email/teléfono, NO vuelvas a pedir contacto; pasa a lo siguiente (fecha/hora/vehículos o nombre).
G) Si el usuario no quiere dar contacto, ofrécele igual los canales oficiales (email/WhatsApp) y sigue ayudando sin trabarte.
H) Si la respuesta del usuario es ambigua, haz 1 sola pregunta aclaratoria ofreciendo 2 opciones concretas (no más).
I) Si el usuario pregunta “valores/precios” sin contexto, aclara “off-road vs evento/producción” y sigue.
J) Evita loops: nunca hagas la misma pregunta 2 veces seguidas; si faltan datos, reformula y muestra lo que ya entendiste.
"""

    def _now_local(self) -> datetime:
        tz_name = getattr(config, "GOOGLE_CALENDAR_TIMEZONE", None) or "America/Santiago"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        return datetime.now(tz)

    def _weekday_es(self, dt: datetime) -> str:
        names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return names[dt.weekday()]

    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        conversation_id: Optional[str] = None,
        platform: Optional[str] = None,
        already_welcomed: Optional[bool] = None,
        lead_capture_already_sent: Optional[bool] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": self.system_prompt}]

        context_lines = []
        now_local = self._now_local()
        context_lines.append(f"today_date={now_local.date().isoformat()}")
        context_lines.append(f"today_weekday_es={self._weekday_es(now_local)}")
        context_lines.append(f"timezone={getattr(config, 'GOOGLE_CALENDAR_TIMEZONE', 'America/Santiago')}")

        # Excepción comercial: este sábado está abierto con tarifa normal (ver reglas).
        days_ahead = (5 - now_local.weekday()) % 7  # Saturday=5
        special_sat = now_local.date() + timedelta(days=days_ahead)
        context_lines.append(f"special_open_saturday_date={special_sat.isoformat()}")
        context_lines.append("special_open_saturday_hours=10:00-17:00")
        context_lines.append("special_open_saturday_price_vehicle_clp=15000")
        context_lines.append("special_open_saturday_price_moto_clp=10000")
        if conversation_id:
            context_lines.append(f"conversation_id={conversation_id}")
        if platform:
            context_lines.append(f"platform={platform}")
        if already_welcomed is not None:
            context_lines.append(f"already_welcomed={'true' if already_welcomed else 'false'}")
        if lead_capture_already_sent is not None:
            context_lines.append(f"lead_capture_already_sent={'true' if lead_capture_already_sent else 'false'}")

        if extra_context:
            for k, v in extra_context.items():
                if v is None:
                    continue
                key = str(k).strip()
                if not key:
                    continue
                # Limitar tamaño para evitar inflar el prompt con datos enormes
                value = str(v).strip()
                if not value:
                    continue
                if len(value) > 400:
                    value = value[:400] + "…"
                context_lines.append(f"{key}={value}")

        if context_lines:
            messages.append({"role": "system", "content": "CONTEXTO\n" + "\n".join(context_lines)})

        messages.append({"role": "system", "content": self.operational_prompt})

        if conversation_history:
            for msg in conversation_history[-config.MAX_CONVERSATION_HISTORY :]:
                metadata = msg.get("metadata") or {}
                if metadata.get("type") in ("booking_state", "lead_capture"):
                    continue

                role = msg.get("role", "user")
                content = (msg.get("message") or "").strip()
                if not content:
                    continue

                if role not in ("system", "user", "assistant", "tool"):
                    role = "user"

                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})
        return messages

    def _model_candidates(self) -> List[str]:
        """
        Retorna una lista de modelos a intentar en orden.
        - Primero: el modelo configurado (OPENAI_MODEL)
        - Luego: OPENAI_MODEL_FALLBACKS (comma/semicolon-separated)
        - Finalmente: fallbacks razonables para mantener el servicio operativo
        """
        candidates: List[str] = []

        if self.model:
            candidates.append(self.model)

        raw = (os.getenv("OPENAI_MODEL_FALLBACKS") or "").strip()
        if raw:
            for part in re.split(r"[;,]", raw):
                m = part.strip()
                if m:
                    candidates.append(m)

        # Heurística: si el usuario configuró algo tipo "gpt-5.2", intenta variantes comunes.
        if self.model and self.model.startswith("gpt-5"):
            candidates.extend(["gpt-5-mini", "gpt-5"])

        # Fallbacks seguros (si están disponibles en la cuenta).
        candidates.extend(["gpt-4.1-mini", "gpt-4o-mini"])

        # De-dup preservando orden
        seen = set()
        unique: List[str] = []
        for m in candidates:
            k = m.strip().lower()
            if not k or k in seen:
                continue
            seen.add(k)
            unique.append(m.strip())
        return unique

    def _token_param_name(self, model: str) -> str:
        """
        Algunos modelos (p.ej. gpt-5.*) no aceptan `max_tokens` en Chat Completions y exigen
        `max_completion_tokens`.
        """
        m = (model or "").strip().lower()
        if m.startswith("gpt-5"):
            return "max_completion_tokens"
        if m.startswith(("o1", "o3")):
            return "max_completion_tokens"
        return "max_tokens"

    def _generate_with_model(
        self,
        *,
        model: str,
        base_messages: List[Dict[str, str]],
        return_events: bool,
    ) -> Any:
        messages: List[Any] = [dict(m) for m in base_messages]
        events: List[Dict[str, Any]] = []

        max_tool_rounds = 3
        token_param = self._token_param_name(model)
        for _ in range(max_tool_rounds):
            kwargs: Dict[str, Any] = dict(
                model=model,
                messages=messages,
                tools=self.tools_manager.tools,
                tool_choice="auto",
                temperature=0.7,
            )
            kwargs[token_param] = 800
            response = self.client.chat.completions.create(**kwargs)

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                final_text = response_message.content or ""
                if return_events:
                    return {"text": final_text, "events": events, "model_used": model}
                return final_text

            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments or "{}")

                print(f"🔧 Ejecutando herramienta: {function_name}")
                print(f"   Argumentos: {function_args}")

                function_result = self.tools_manager.execute_tool(function_name, function_args)
                events.append({"tool": function_name, "args": function_args, "result": function_result})

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_result),
                    }
                )

        fallback_text = "Listo. ¿En qué más te puedo ayudar?"
        if return_events:
            return {"text": fallback_text, "events": events, "model_used": model}
        return fallback_text
    
    def generate_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict] = None,
        *,
        conversation_id: Optional[str] = None,
        platform: Optional[str] = None,
        already_welcomed: Optional[bool] = None,
        lead_capture_already_sent: Optional[bool] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        return_events: bool = False,
    ) -> Any:
        """
        Genera una respuesta del chatbot con soporte para Function Calling
        
        Args:
            user_message: Mensaje del usuario
            conversation_history: Historial de conversación (opcional)
        
        Returns:
            Respuesta generada por el modelo
        """
        messages = self._build_messages(
            user_message=user_message,
            conversation_history=conversation_history,
            conversation_id=conversation_id,
            platform=platform,
            already_welcomed=already_welcomed,
            lead_capture_already_sent=lead_capture_already_sent,
            extra_context=extra_context,
        )

        last_error: Optional[Exception] = None
        for model in self._model_candidates():
            try:
                if model != self.model:
                    print(f"⚠️ Probando modelo fallback: {model} (configurado: {self.model})")
                return self._generate_with_model(model=model, base_messages=messages, return_events=return_events)
            except Exception as e:
                last_error = e
                print(f"❌ Error generando respuesta con OpenAI (model={model}): {e}")

        import traceback
        if last_error:
            traceback.print_exception(type(last_error), last_error, last_error.__traceback__)

        error_text = (
            "Lo siento, hubo un problema al procesar tu mensaje. "
            "Por favor, intenta nuevamente o contáctanos directamente en contacto@fundomoraga.com"
        )
        return {"text": error_text, "events": [], "model_used": None} if return_events else error_text
    
    def generate_response_with_context(
        self, 
        user_message: str, 
        context: str
    ) -> str:
        """
        Genera una respuesta con contexto adicional (útil para RAG)
        
        Args:
            user_message: Mensaje del usuario
            context: Contexto adicional (ej: información de productos)
        
        Returns:
            Respuesta generada
        """
        try:
            enhanced_prompt = f"{self.system_prompt}\n\nContexto adicional:\n{context}"
            
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                **{self._token_param_name(self.model): 500},
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error generando respuesta con contexto: {e}")
            return "Lo siento, hubo un problema al procesar tu mensaje."

    def summarize_lead_interest(
        self,
        *,
        conversation_snippet: str,
        known_name: Optional[str] = None,
        known_contact: Optional[str] = None,
        booking_details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Genera un resumen corto del interés del usuario para uso interno (email/CRM).
        No debe inventar datos: si algo no está explícito, debe omitirlo.
        """
        try:
            sys = (
                "Eres un asistente que redacta resúmenes internos para el equipo de Fundo Moraga.\n"
                "Reglas:\n"
                "- No inventes datos.\n"
                "- Sé breve (2–4 líneas).\n"
                "- Menciona objetivo del usuario y, si aplica, fecha/hora/vehículos.\n"
                "- No incluyas el contacto dentro del resumen (va aparte).\n"
            )

            known_lines = []
            if known_name:
                known_lines.append(f"Nombre: {known_name}")
            if known_contact:
                known_lines.append(f"Contacto: {known_contact}")
            if booking_details:
                try:
                    known_lines.append("Reserva (parcial): " + json.dumps(booking_details, ensure_ascii=False))
                except Exception:
                    known_lines.append(f"Reserva (parcial): {booking_details}")

            user = (
                "Datos conocidos (pueden venir vacíos):\n"
                + ("\n".join(known_lines) if known_lines else "(ninguno)\n")
                + "\n\n"
                "Conversación (fragmento):\n"
                f"{conversation_snippet}\n\n"
                "Escribe el resumen:"
            )

            kwargs: Dict[str, Any] = dict(
                model=self.model,
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
                temperature=0.2,
            )
            kwargs[self._token_param_name(self.model)] = 200
            response = self.client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"❌ Error generando resumen de lead: {e}")
            # Fallback determinístico
            return (conversation_snippet or "").strip()[:400]


# Singleton instance
_chatbot_ai = None

def get_chatbot_ai() -> ChatbotAI:
    """Obtiene la instancia singleton del ChatbotAI"""
    global _chatbot_ai
    if _chatbot_ai is None:
        _chatbot_ai = ChatbotAI()
    return _chatbot_ai
