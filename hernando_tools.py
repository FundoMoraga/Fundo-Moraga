"""
Herramientas (Tools) disponibles para Hernando
Function Calling de OpenAI para ejecutar acciones específicas
"""
from typing import Dict, Any, List
import json
from datetime import datetime
import requests
import inspect
from cosmos_client import get_memory_store

class HernandoTools:
    """Gestiona las herramientas disponibles para Hernando"""
    
    def __init__(self):
        """Inicializa las herramientas"""
        self.tools = self._define_tools()
        self.memory_store = get_memory_store()
    
    def _define_tools(self) -> List[Dict]:
        """
        Define las herramientas disponibles para OpenAI Function Calling
        
        Returns:
            Lista de definiciones de herramientas en formato OpenAI
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "enviar_formulario_contacto",
                    "description": "Envía un formulario de contacto al equipo de Fundo Moraga con los datos del usuario para cotizaciones, reservas o consultas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {
                                "type": "string",
                                "description": "Nombre completo del usuario"
                            },
                            "email": {
                                "type": "string",
                                "description": "Email de contacto del usuario"
                            },
                            "telefono": {
                                "type": "string",
                                "description": "Número de teléfono del usuario"
                            },
                            "tipo_solicitud": {
                                "type": "string",
                                "enum": ["evento", "actividad_offroad", "visita", "produccion", "otro"],
                                "description": "Tipo de solicitud: evento, actividad_offroad, visita, produccion, otro"
                            },
                            "mensaje": {
                                "type": "string",
                                "description": "Mensaje o consulta del usuario"
                            },
                            "fecha_tentativa": {
                                "type": "string",
                                "description": "Fecha tentativa en formatos: YYYY-MM-DD; DD/MM/YYYY; 12 enero 2026 (ejemplo); viernes (preguntar si este viernes o el próximo)"
                            }
                        },
                        "required": ["nombre", "email", "tipo_solicitud", "mensaje"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar_informacion_historica",
                    "description": "Busca información específica sobre la historia de la Familia Moraga, eventos históricos, personajes o propiedades",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tema": {
                                "type": "string",
                                "enum": [
                                    "conquista",
                                    "guerra_arauco",
                                    "independencia",
                                    "batalla_chacabuco",
                                    "rodeo_chileno",
                                    "hacienda_nancagua",
                                    "hacienda_chacabuco",
                                    "fundo_batuco",
                                    "hernando_moraga",
                                    "familia_general"
                                ],
                                "description": "Tema histórico a consultar"
                            },
                            "detalle": {
                                "type": "string",
                                "description": "Detalle específico o pregunta sobre el tema"
                            }
                        },
                        "required": ["tema"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "informar_actividades_disponibles",
                    "description": "Proporciona información detallada sobre las actividades y servicios disponibles en el Fundo Moraga",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tipo_actividad": {
                                "type": "string",
                                "enum": ["eventos", "offroad", "turismo_rural", "produccion_audiovisual", "todas"],
                                "description": "Tipo de actividad sobre la que se solicita información"
                            },
                            "numero_personas": {
                                "type": "integer",
                                "description": "Número aproximado de personas (opcional)"
                            }
                        },
                        "required": ["tipo_actividad"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "obtener_contactos_oficiales",
                    "description": "Proporciona los contactos oficiales de Fundo Moraga según el tipo de consulta",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "motivo": {
                                "type": "string",
                                "enum": ["cotizacion", "reserva", "consulta_general", "emergencia", "prensa"],
                                "description": "Motivo del contacto"
                            }
                        },
                        "required": ["motivo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verificar_acceso_fundo",
                    "description": "Verifica las condiciones y requisitos para acceder al Fundo Moraga",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "proposito": {
                                "type": "string",
                                "description": "Propósito de la visita"
                            }
                        },
                        "required": ["proposito"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "capturar_informacion_usuario",
                    "description": """Registra información que el usuario mencionó NATURALMENTE en conversación fluida. 
                    
CUÁNDO LLAMAR:
✓ Usuario dice: "Soy María González" → capturar nombre
✓ Usuario dice: "Mi email es maria@example.com" → capturar contacto
✓ Usuario dice: "Necesito para evento de 50 personas" → capturar interés

CUÁNDO NO LLAMAR:
✗ Bot preguntó "¿Tu nombre?" y usuario respondió "Juan" → NO capturar aún (es respuesta directa)
✗ Capturar después de pregunta directa - esperar que usuario dé más contexto natural

ESTRATEGIA: Esperar a que usuario proporcione información en contexto conversacional, no como respuesta a interrogatorio.

IMPORTANTE: Siempre capturar con contexto adicional del interés/necesidad del usuario basado en toda la conversación.
""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {
                                "type": "string",
                                "description": "Nombre completo del usuario mencionado naturalmente (ej: 'Soy Pablo', 'Me llamo María')"
                            },
                            "interes": {
                                "type": "string",
                                "description": "Descripción COMPLETA de qué necesita/le interesa al usuario, sintetizando TODA la conversación: tipo de actividad, cantidad personas, presupuesto aproximado, timing, nivel de urgencia. Ejemplo: 'Off-road para 3 autos, próximo sábado, presupuesto ~45k CLP, quiere info sobre rutas técnicas'"
                            },
                            "contacto": {
                                "type": "string",
                                "description": "Email y/o teléfono si usuario los compartió voluntariamente. Formato preferido: '+56912345678' para teléfonos chilenos, validar con usuario si número parece incompleto"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "guardar_precio",
                    "description": "Guarda o actualiza el precio de un producto o servicio en la memoria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "producto": {"type": "string", "description": "Nombre del producto o servicio"},
                            "precio": {"type": "number", "description": "Precio en la moneda indicada"},
                            "moneda": {"type": "string", "description": "Moneda (ej: CLP, USD)", "default": "CLP"},
                            "fuente": {"type": "string", "description": "Origen del precio (ej: lista_oficial, promo)"},
                            "vigente_desde": {"type": "string", "description": "ISO8601 de vigencia (opcional)"},
                            "etiquetas": {"type": "array", "items": {"type": "string"}, "description": "Tags opcionales"}
                        },
                        "required": ["producto", "precio"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "guardar_hecho",
                    "description": "Guarda o actualiza un hecho/dato relevante en la memoria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "clave": {"type": "string", "description": "Identificador del hecho"},
                            "valor": {"type": "string", "description": "Contenido del hecho"},
                            "alcance": {"type": "string", "description": "Ámbito: global o por segmento", "default": "global"},
                            "etiquetas": {"type": "array", "items": {"type": "string"}, "description": "Tags opcionales"},
                            "expira_en": {"type": "string", "description": "ISO8601 de expiración (opcional)"}
                        },
                        "required": ["clave", "valor"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una herramienta específica
        
        Args:
            tool_name: Nombre de la herramienta a ejecutar
            arguments: Argumentos para la herramienta
        
        Returns:
            Resultado de la ejecución
        """
        # Mapear nombres de funciones a métodos
        tool_methods = {
            "enviar_formulario_contacto": self.enviar_formulario_contacto,
            "buscar_informacion_historica": self.buscar_informacion_historica,
            "informar_actividades_disponibles": self.informar_actividades_disponibles,
            "obtener_contactos_oficiales": self.obtener_contactos_oficiales,
            "verificar_acceso_fundo": self.verificar_acceso_fundo,
            "capturar_informacion_usuario": self.capturar_informacion_usuario,
            "guardar_precio": self.guardar_precio,
            "guardar_hecho": self.guardar_hecho,
        }
        
        if tool_name not in tool_methods:
            return {
                "success": False,
                "error": f"Herramienta '{tool_name}' no encontrada"
            }
        
        try:
            # OpenAI a veces envía `null` o tipos inesperados en `arguments`.
            if arguments is None:
                arguments = {}
            if not isinstance(arguments, dict):
                return {"success": False, "error": "Argumentos inválidos: se esperaba un objeto JSON (dict)"}

            # Tolerancia a claves extra: ejecutamos solo con los parámetros que acepta el método.
            method = tool_methods[tool_name]
            sig = inspect.signature(method)
            accepted = {
                name
                for name, param in sig.parameters.items()
                if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
            }
            filtered_args = {k: v for k, v in arguments.items() if k in accepted}

            # Normalizaciones puntuales (evita TypeError por strings numéricos, etc.)
            if tool_name == "informar_actividades_disponibles" and "numero_personas" in filtered_args:
                v = filtered_args.get("numero_personas")
                if isinstance(v, str):
                    digits = "".join(ch for ch in v if ch.isdigit())
                    filtered_args["numero_personas"] = int(digits) if digits else None

            result = method(**filtered_args)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============= IMPLEMENTACIÓN DE HERRAMIENTAS =============
    
    def enviar_formulario_contacto(
        self, 
        nombre: str, 
        email: str, 
        tipo_solicitud: str, 
        mensaje: str,
        telefono: str = None,
        fecha_tentativa: str = None
    ) -> str:
        """
        Envía un formulario de contacto al equipo
        
        En producción, esto podría:
        - Enviar un email
        - Guardar en base de datos
        - Crear ticket en sistema CRM
        - Enviar notificación a WhatsApp
        """
        # Por ahora, simula el envío y retorna confirmación
        formulario = {
            "nombre": nombre,
            "email": email,
            "telefono": telefono or "No proporcionado",
            "tipo_solicitud": tipo_solicitud,
            "mensaje": mensaje,
            "fecha_tentativa": fecha_tentativa or "No especificada",
            "timestamp": datetime.now().isoformat()
        }
        
        # TODO: Implementar envío real (email, webhook, etc.)
        print(f"📧 Formulario recibido: {json.dumps(formulario, indent=2)}")
        
        return f"""¡Perfecto! He enviado tu solicitud con éxito.

    # ----- Memoria: precios y hechos -----
    def guardar_precio(
        self,
        producto: str,
        precio: float,
        moneda: str = "CLP",
        fuente: str | None = None,
        vigente_desde: str | None = None,
        etiquetas: list[str] | None = None,
    ) -> Dict[str, Any]:
        saved = self.memory_store.upsert_price(
            product=producto,
            price=precio,
            currency=moneda,
            source=fuente,
            effective_from=vigente_desde,
            tags=etiquetas,
        )
        return {"status": "ok", "saved": saved}

    def guardar_hecho(
        self,
        clave: str,
        valor: str,
        alcance: str = "global",
        etiquetas: list[str] | None = None,
        expira_en: str | None = None,
    ) -> Dict[str, Any]:
        saved = self.memory_store.upsert_fact(
            key=clave,
            value=valor,
            scope=alcance,
            tags=etiquetas,
            expires_at=expira_en,
        )
        return {"status": "ok", "saved": saved}

Tu consulta sobre {tipo_solicitud} ya está en las mejores manos: las del equipo del Fundo Moraga. 
Pronto recibirás noticias en tu email ({email}) o por teléfono ({telefono}).

Recuerda que también puedes contactarnos cuando quieras en:
📧 contacto@fundomoraga.com
📱 WhatsApp: +5699 9392122

¡Gracias por pensar en nosotros para tu proyecto! Nos ilusiona mucho la idea.
"""
    
    def buscar_informacion_historica(self, tema: str, detalle: str = None) -> str:
        """
        Busca información histórica específica
        """
        info_historica = {
            "conquista": """
**Conquista de Chile (1551)**

Hernando Galindo de Moraga llegó a Chile en 1551 bajo las órdenes de Francisco de Villagra.
Participó activamente en:
- Fundación de Valdivia (1552)
- Fundación de Osorno (1558)
- Batalla de Marihueño (1554)
- Guerra de Arauco

Fue Alcalde Ordinario de Osorno y recibió encomiendas en el sur.
            """,
            "guerra_arauco": """
**Guerra de Arauco**

La familia Moraga participó en la Guerra de Arauco, uno de los conflictos más prolongados 
de la historia colonial americana (1550-1818).

Hernando de Moraga combatió en la Batalla de Marihueño (1554) donde las fuerzas españolas 
perdieron 95 de 150 soldados. Tras el Desastre de Curalaba (1598), la familia perdió 
todas sus propiedades en el sur y se trasladó a Santiago.
            """,
            "independencia": """
**Participación en la Independencia**

Fray José María Moraga y Fuenzalida tuvo un papel destacado:
- Asistió al Cabildo Abierto de 1810
- Firmó el Reglamento Constitucional Provisorio de 1812
- Ofició el primer Te Deum tras la Independencia (12 de febrero de 1818)
- Fue orador en la reapertura del Instituto Nacional (1819)

Ignacio José de Aránguiz Mendieta fue Teniente Coronel y diputado en el Primer Congreso Nacional.
            """,
            "batalla_chacabuco": """
**Batalla de Chacabuco (1817)**

La Hacienda de Chacabuco, propiedad de la familia, fue escenario clave:
- Cuartel General del Ejército de los Andes
- Refugio de San Martín y O'Higgins tras la batalla
- Hospital de sangre para heridos
- Sitio estratégico en el camino a Santiago

La familia apoyó activamente la causa patriota.
            """,
            "rodeo_chileno": """
**Tradición en el Rodeo Chileno**

La familia Moraga tiene profunda tradición en el rodeo:

**Ramón Cardemil Moraga** (1917-2017):
- 7 veces Campeón Nacional (1962, 1963, 1965, 1967, 1968, 1973, 1981)
- Mejor Jinete del Siglo XX
- Récord de 29 puntos en 1968

**Hugo Cardemil Moraga** (1925-2019):
- 4 veces Campeón Nacional (1986, 1990, 1991, 1993)
- Tercer jinete con más títulos de Chile
            """,
            "hacienda_nancagua": """
**Hacienda de Nancagua**

Francisco de Aránguiz y Moraga (1726-1796) fue dueño de esta extensa estancia en Colchagua.

En 1789, junto a su esposa María de la Concepción Mendieta, donaron los terrenos para 
la construcción de la Iglesia Parroquial de Nancagua, bajo la advocación de Nuestra 
Señora de la Merced.

Fue Alcalde de Santiago (1779) y Tesorero de la Santa Cruzada (1783).
            """,
            "hacienda_chacabuco": """
**Hacienda de Chacabuco**

Propiedad histórica de la familia, ubicada en la Cuesta de Chacabuco, fue:
- Centro productivo desde el siglo XVIII
- Cuartel General en la Batalla de Chacabuco (1817)
- Casa patronal y capilla reconstruidas tras el terremoto de 1730
- Declarada Monumento Histórico

Las casas y capilla aún se conservan como testimonio patrimonial.
            """,
            "fundo_batuco": """
**Fundo Moraga - Batuco**

Establecido en el siglo XX en la Provincia de Chacabuco, ha sido:

Producción agrícola:
- Trigo y cebada (convenio INIA-CCU)
- Frutas frescas

Valor histórico:
- Campo de pruebas de cañones (1866, 1876) previo a la Guerra del Pacífico
- Proveedor de madera para cureñas de la Independencia
- Fuente de piedras de granito para la Capilla Nuestra Señora del Trabajo

Hoy mantiene actividades agrícolas, eventos y conservación patrimonial.
            """,
            "hernando_moraga": """
**Hernando Galindo de Moraga (1522-1604)**

Fundador del linaje en Chile:
- Nacido en Cáceres, Extremadura
- Llegó a Chile en 1551
- Participó en Virreinato del Perú antes de Chile
- Combatió en las batallas de Guarina y en el Callao
- Casado con Elvira de Ribera Mendoza y Grijalva
- Padre de Mencía de Moraga, quien perpetuó el apellido

Su descendencia ha mantenido presencia ininterrumpida por casi 500 años.
            """,
            "familia_general": """
**Familia Moraga - Historia General**

Presencia documentada de casi 1600 años:
- Siglo IV: General Moragas bajo el Emperador Honorio (Imperio Romano)
- Siglo XV: Casa Solar en Cáceres, España
- 1212: Arias Moragas en la Batalla de las Navas de Tolosa
- 1551: Llegada a Chile con Hernando de Moraga
- 1810-1818: Participación en la Independencia
- Siglo XX-XXI: Mantiene propiedades agrícolas en RM

Una de las familias fundadoras de Chile con mayor continuidad histórica.
            """
        }
        
        respuesta = info_historica.get(tema, "No se encontró información sobre ese tema específico.")
        
        if detalle:
            respuesta += f"\n\n🔍 Buscaste específicamente sobre: '{detalle}'.\n"
            respuesta += "¡Espero que esta información te sea de gran utilidad! Si te pica el bichito de la curiosidad y quieres saber más, no dudes en escribirle a nuestro equipo a contacto@fundomoraga.com. ¡Nos fascina compartir las historias y secretos de este lugar!"
        
        return respuesta
    
    def informar_actividades_disponibles(
        self, 
        tipo_actividad: str, 
        numero_personas: int = None
    ) -> str:
        """
        Proporciona información sobre actividades disponibles
        """
        actividades = {
            "eventos": """
🌿 **EVENTOS EN FUNDO MORAGA**

Disponemos de extensas áreas para:
- Eventos corporativos y empresariales
- Eventos privados (matrimonios, celebraciones)
- Jornadas de team building
- Lanzamientos de productos
- Actividades outdoor y deportivas

Capacidad: Flexible según el tipo de evento
Espacios: Áreas abiertas, zonas naturales, sectores específicos

📷 Ver ejemplos: @fundomoraga y @batuco_offroad en Instagram (¡y síguenos para ver más!)

Para cotizar tu evento:
📧 contacto@fundomoraga.com
📱 WhatsApp: +5694 1242609
            """,
            "offroad": """
🚙 **ACTIVIDADES OFF-ROAD**

HORARIOS Y PRECIOS:
📅 **Lunes a Viernes**: 9:00 AM - 5:00 PM
   💵 $15.000 automóviles (4x4, SUVs, camionetas)
   💵 $10.000 motos

📅 **Sábados y domingo (Grupos)**:
   💵 $200.000 el día (por grupo)

📅 **Este domingo (fecha libre)**:
   🕙 10:00 AM - 5:00 PM
   💵 $15.000 por vehículo / $10.000 por moto

📅 **Eventos Privados/Corporativos**:
   💵 Valores y condiciones personalizadas
   📞 Contactar al equipo de ventas

Operadas EXCLUSIVAMENTE por Batuco Off Road:
- Rutas 4x4 profesionales
- Experiencias de enduro
- Eventos de aventura motorizada
- Circuitos para diferentes niveles
- Terrenos diversos ideales para todoterreno
- Clases 4x4 con pilotos profesionales (consultar disponibilidad)

REQUISITOS:
- Vehículo en buenas condiciones mecánicas
- Seguro vigente
- Respeto por el entorno natural e histórico

📷 Ver más: @batuco_offroad en Instagram (¡y síguenos para ver rutas, fechas y novedades!)

RESERVAS Y CONSULTAS:
📧 contacto@fundomoraga.com
📱 +5699 9392122

Si quieres, lo coordinamos al tiro 😊 ¿Qué día te gustaría venir y a qué hora te acomoda llegar (según el horario del día)? ¿Vienes en auto o moto, y cuántos? Si me dejas un teléfono o correo, el equipo puede confirmarte sin vueltas.
            """,
            "turismo_rural": """
🏞️ **TURISMO RURAL Y EXPERIENCIAS DE NATURALEZA**

Experiencias disponibles:
- Caminatas por el campo histórico
- Exploración del entorno natural
- Avistamiento de aves (cerca del Humedal de Batuco)
- Conocer la historia de la familia y el fundo
- Actividades educativas patrimoniales

Ideal para grupos que buscan:
- Conexión con la naturaleza
- Experiencias rurales auténticas
- Conocer patrimonio histórico chileno

Consultas: contacto@fundomoraga.com
            """,
            "produccion_audiovisual": """
🎬 **PRODUCCIONES AUDIOVISUALES**

El Fundo Moraga ofrece:
- Locaciones rurales auténticas
- Paisajes abiertos y naturales
- Infraestructura histórica
- Acceso controlado y privacidad
- Cercanía a Santiago (Batuco, Lampa)

Ideal para:
- Películas y series
- Comerciales
- Videoclips
- Producciones fotográficas
- Documentales

Coordinación: contacto@fundomoraga.com
            """,
            "todas": """
✨ **TODAS LAS ACTIVIDADES - FUNDO MORAGA**

El Fundo Moraga ofrece:

🌿 EVENTOS:
Corporativos, privados, team building, lanzamientos

🚙 OFF-ROAD:
Rutas 4x4, enduro (operado por Batuco Off Road)

🏞️ TURISMO RURAL:
Caminatas, naturaleza, patrimonio histórico

🎬 PRODUCCIONES:
Locaciones para cine, TV, fotografía

📍 Ubicación: Batuco, Lampa, Región Metropolitana
🏛️ Valor patrimonial: 470+ años de historia familiar

Ver ejemplos: @fundomoraga, @batuco_offroad @fundomoraga en YouTube (¡y síguenos para no perderte lo que hacemos!)

Contacto:
📧 contacto@fundomoraga.com
📱 +5699 9392122
            """
        }
        
        respuesta = actividades.get(tipo_actividad, actividades["todas"])
        
        if numero_personas:
            respuesta += f"\n\n👥 ¡Excelente! Veo que son un grupo de {numero_personas} personas. ¡Podemos preparar algo inolvidable para ustedes! "
            respuesta += "Conversemos por nuestros canales de contacto para diseñar juntos una experiencia a la medida de lo que buscan. ¡Será un placer!"
        
        return respuesta
    
    def obtener_contactos_oficiales(self, motivo: str) -> str:
        """
        Proporciona los contactos oficiales según el motivo
        """
        contactos_base = """
📧 **Email**: contacto@fundomoraga.com
📱 **WhatsApp**: +5694 1242609
📍 **Ubicación**: Batuco, Lampa, Región Metropolitana
        """
        
        mensajes = {
            "cotizacion": f"""
**COTIZACIONES Y PRESUPUESTOS**

¡Claro que sí! Para darte una cotización a tu medida, cuéntanos un poco más sobre tu idea:
- ¿Qué tipo de evento o actividad tienes en mente?
- ¿En qué fecha te gustaría realizarlo?
- ¿Cuántas personas asistirán?
- ¿Tienes algún requerimiento especial?

Con esta información, prepararemos algo increíble para ti.

{contactos_base}

Nuestro equipo te responderá en un plazo de 24 a 48 horas hábiles. ¡Estamos ansiosos por ayudarte a crear un momento inolvidable!
            """,
            "reserva": f"""
**RESERVAS**

¡Estupendo! Para reservar tu experiencia en Fundo Moraga, solo necesitamos que nos contactes con los siguientes datos:
1. Las fechas que tienes en mente.
2. El tipo de actividad que te gustaría realizar.
3. El número de personas que participarán.

{contactos_base}

Te responderemos a la brevedad con la disponibilidad y los siguientes pasos. ¡Estamos muy contentos de que nos consideres para tu próxima aventura!
            """,
            "consulta_general": f"""
**CONSULTAS GENERALES**

¡Por supuesto! Estamos aquí para responder todas tus dudas sobre:
- La fascinante historia de nuestro fundo y la familia Moraga.
- Las entretenidas actividades que ofrecemos.
- Nuestros servicios y cómo podemos adaptarnos a tus necesidades.
- Cómo llegar y todo sobre nuestra ubicación.

{contactos_base}

¡No dudes en preguntar, nos encanta conversar sobre Fundo Moraga!
            """,
            "emergencia": f"""
**CONTACTO DE EMERGENCIA**

Para cualquier situación urgente durante tu visita o evento, por favor, utiliza estos canales:

{contactos_base}

Tu seguridad y bienestar son nuestra máxima prioridad.
            """,
            "prensa": f"""
**CONTACTO DE PRENSA**

Si eres de un medio de comunicación y necesitas información, ¡estamos a tu disposición!

{contactos_base}

Por favor, en el asunto de tu correo indica: "Prensa - [Nombre de tu medio]".

Podemos facilitarte:
- Información histórica detallada y documentada.
- Material fotográfico de alta calidad.
- Coordinar entrevistas con nuestro equipo.

¡Gracias por tu interés en difundir la historia de Fundo Moraga!
            """
        }
        
        return mensajes.get(motivo, contactos_base)
    
    def verificar_acceso_fundo(self, proposito: str) -> str:
        """
        Verifica condiciones de acceso al fundo
        """
        return f"""
🚧 **SOBRE EL ACCESO AL FUNDO MORAGA**

¡Qué bueno que preguntas! El Fundo Moraga es un tesoro privado que cuidamos con enorme cariño, y por eso, el acceso siempre se coordina con antelación.

✅ **Eres bienvenido a ingresar si tienes**:
- Una autorización formal de nuestro equipo. ¡Te esperamos con los brazos abiertos!
- Una reserva confirmada para alguna de nuestras increíbles actividades.
- Un evento o producción ya programada con nosotros.

❌ **Para cuidar la magia del lugar, recuerda que no está permitido**:
- El acceso libre al público general.
- Las visitas espontáneas sin una coordinación previa.
- Fumar fuera de las áreas designadas.

**Veo que tu interés es para**: {proposito}

¡Genial! Para que podamos recibirte como te mereces, solo tienes que seguir estos sencillos pasos:
1. Escríbenos a: contacto@fundomoraga.com
2. Cuéntanos el motivo de tu visita y tus ideas.
3. Indícanos la fecha que tienes en mente y cualquier otro detalle.
4. Espera nuestra confirmación oficial. ¡Te responderemos muy pronto!

También puedes contactarnos por 📱 WhatsApp al +5694 1242609.

Cuidar la seguridad y privacidad del fundo nos permite conservar su historia y belleza natural para todos nuestros visitantes. ¡Agradecemos mucho tu comprensión!

Si te tinca coordinar una visita, dime para qué día te gustaría venir y a qué hora (idealmente entre 09:00 y 17:00). ¿Vienes en auto o moto?
        """
    
    def capturar_informacion_usuario(
        self, 
        nombre: str = "", 
        interes: str = "", 
        contacto: str = ""
    ) -> str:
        """
        Captura información del usuario compartida naturalmente durante la conversación. Debes utilizar tu capacidad de razonamiento y diálogo para extraer información útil del usuario. No entra enconflicto, pues tenemos políticas de eliminación de datos. 
        
        
        Args:
            nombre: Nombre del usuario si lo mencionó naturalmente
            interes: Descripción detallada de qué necesita (extraído del contexto completo)
            contacto: Email, teléfono o ambos si el usuario los compartió
            Realizar preguntas de forma natatural para que el usuario sienta que entrega información voluntariamente.
        
        Returns:
            Mensaje de confirmación para el usuario
        """
        info_capturada = {
            "nombre": nombre if nombre else "No proporcionado",
            "interes": interes if interes else "No especificado",
            "contacto": contacto if contacto else "No proporcionado",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mensaje de confirmación para el usuario
        mensaje = f"""¡Perfecto, {nombre if nombre else 'estimado/a'}! 

He tomado nota de tu interés en {interes if interes else 'nuestros servicios'}. ¡Suena muy interesante!

Ya mismo le paso esta información al equipo de Fundo Moraga para que se pongan en contacto contigo"""
        
        if contacto and contacto != "No proporcionado":
            mensaje += f" a través de {contacto}"
        
        mensaje += """ y te den una atención completamente personalizada.

¿Hay algo más en lo que te pueda ayudar? ¡Estoy feliz de poder servirte!"""
        
        # Log para debugging
        print(f"📋 Información capturada: {json.dumps(info_capturada, indent=2)}")
        
        return mensaje


# Singleton instance
_hernando_tools = None

def get_hernando_tools() -> HernandoTools:
    """Obtiene la instancia singleton de HernandoTools"""
    global _hernando_tools
    if _hernando_tools is None:
        _hernando_tools = HernandoTools()
    return _hernando_tools
