"""
Herramientas (Tools) disponibles para Hernando
Function Calling de OpenAI para ejecutar acciones específicas
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import requests
import inspect
from cosmos_client import get_memory_store
import private_knowledge
import language_client
import translator_client

# Vision client es opcional (requiere azure-cognitiveservices-vision-computervision)
try:
    import vision_client
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    vision_client = None

# Steel Browser client es opcional (para navegación web)
try:
    from steel_browser_client import get_steel_browser_client
    STEEL_BROWSER_AVAILABLE = True
except ImportError:
    STEEL_BROWSER_AVAILABLE = False
    get_steel_browser_client = None

# Vision Service client para análisis doctoral de imágenes
try:
    from vision_service_client import get_vision_service_client
    VISION_SERVICE_AVAILABLE = True
except ImportError:
    VISION_SERVICE_AVAILABLE = False
    get_vision_service_client = None

class HernandoTools:
    """Gestiona las herramientas disponibles para Hernando"""
    
    def __init__(self, user_id: Optional[str] = None):
        """Inicializa las herramientas"""
        self.user_id = user_id
        self.tools = self._define_tools()
        self.memory_store = get_memory_store()
        
        # Agregar herramientas privadas si el usuario está autorizado
        if private_knowledge.is_authorized_user(user_id):
            self.tools.extend(private_knowledge.get_private_knowledge_tools())
            self.tools.extend(self._define_language_tools())
            # Solo agregar herramientas de Vision si el módulo está disponible
            if VISION_AVAILABLE:
                self.tools.extend(self._define_vision_tools())
            # Agregar herramientas de navegación web si Steel Browser está disponible
            if STEEL_BROWSER_AVAILABLE:
                self.tools.extend(self._define_web_navigation_tools())
            # Agregar herramientas de búsqueda de imágenes si Vision Service está disponible
            if VISION_SERVICE_AVAILABLE:
                self.tools.extend(self._define_image_search_tools())
    
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

    def _define_language_tools(self) -> List[Dict]:
        """Herramientas de lenguaje y traducción (solo para usuarios autorizados)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analizar_sentimiento_texto",
                    "description": "Analiza el sentimiento de un texto usando el servicio de lenguaje.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "Texto a analizar"}
                        },
                        "required": ["texto"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detectar_idioma_texto",
                    "description": "Detecta el idioma de un texto usando el servicio de lenguaje.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "Texto a analizar"}
                        },
                        "required": ["texto"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extraer_frases_clave",
                    "description": "Extrae frases clave de un texto usando el servicio de lenguaje.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "Texto a analizar"}
                        },
                        "required": ["texto"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "traducir_texto",
                    "description": "Traduce un texto al idioma destino usando el servicio de traducción.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "Texto a traducir"},
                            "destino": {"type": "string", "description": "Idioma destino (ej: en, es, pt)"},
                            "origen": {"type": "string", "description": "Idioma origen (opcional, ej: es)"}
                        },
                        "required": ["texto", "destino"],
                    },
                },
            },
        ]

    def _define_vision_tools(self) -> List[Dict]:
        """Herramientas de visión computacional (solo para usuarios autorizados)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analizar_imagen_completa",
                    "description": "Analiza una imagen y detecta objetos, personas, textos y marcas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url_imagen": {"type": "string", "description": "URL de la imagen a analizar"}
                        },
                        "required": ["url_imagen"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detectar_objetos_imagen",
                    "description": "Detecta objetos, elementos y cosas en una imagen.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url_imagen": {"type": "string", "description": "URL de la imagen a analizar"}
                        },
                        "required": ["url_imagen"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detectar_personas_imagen",
                    "description": "Detecta personas en una imagen y proporciona su ubicación.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url_imagen": {"type": "string", "description": "URL de la imagen a analizar"}
                        },
                        "required": ["url_imagen"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "describir_imagen",
                    "description": "Proporciona una descripción textual de lo que hay en una imagen.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url_imagen": {"type": "string", "description": "URL de la imagen a analizar"}
                        },
                        "required": ["url_imagen"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extraer_texto_imagen",
                    "description": "Extrae texto de una imagen usando OCR.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url_imagen": {"type": "string", "description": "URL de la imagen a analizar"}
                        },
                        "required": ["url_imagen"],
                    },
                },
            },
        ]
    
    def _define_web_navigation_tools(self) -> List[Dict]:
        """Herramientas de navegación web e investigación (solo para usuarios autorizados)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "navegar_url",
                    "description": "Navega a una URL específica y extrae su contenido principal (texto, títulos, enlaces). Útil para leer páginas web, artículos, documentación.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL completa a visitar (ej: https://example.com)"
                            },
                            "wait_for": {
                                "type": "string",
                                "description": "Selector CSS a esperar antes de extraer (opcional, para contenido dinámico)"
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extraer_contenido_web",
                    "description": "Extrae contenido específico de una página usando selectores CSS. Útil cuando necesitas datos estructurados de una página.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL de la página"
                            },
                            "selector": {
                                "type": "string",
                                "description": "Selector CSS del elemento a extraer (ej: 'article', '.content', '#main')"
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar_en_google",
                    "description": "Busca información en Google y extrae contenido relevante de los primeros resultados. Ideal para investigaciones rápidas sobre temas actuales.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Consulta de búsqueda (ej: 'últimas noticias IA Chile', 'precio dolar hoy')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Número de resultados a analizar (1-10, default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "investigar_tema",
                    "description": "Realiza una investigación profunda sobre un tema: busca en múltiples fuentes, analiza contenido y sintetiza hallazgos. Usa esto para análisis exhaustivos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Tema a investigar en profundidad"
                            },
                            "depth": {
                                "type": "string",
                                "enum": ["light", "medium", "deep"],
                                "description": "Profundidad de la investigación: light (rápido, 2-3 fuentes), medium (5-7 fuentes), deep (10+ fuentes)",
                                "default": "medium"
                            }
                        },
                        "required": ["topic"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_multiples_urls",
                    "description": "Extrae contenido de varias URLs simultáneamente. Útil para comparar información de múltiples fuentes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "urls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de URLs a extraer (máximo 10)"
                            }
                        },
                        "required": ["urls"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "capturar_screenshot",
                    "description": "Captura una imagen (screenshot) de una página web. Útil para documentar visuales o compartir cómo se ve un sitio.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL de la página a capturar"
                            },
                            "full_page": {
                                "type": "boolean",
                                "description": "Si capturar página completa (true) o solo la parte visible (false)",
                                "default": False
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
        ]
    
    def _define_image_search_tools(self) -> List[Dict]:
        """Herramientas de búsqueda y análisis de imágenes con Vision Service (solo para usuarios autorizados)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "buscar_imagenes",
                    "description": "Busca imágenes en Google Images y realiza análisis doctoral de cada una con Azure Computer Vision. Proporciona URLs, descripciones academicas y análisis detallado de contenido. Ideal para investigaciones visuales con nivel académico.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Término de búsqueda (ej: 'Jeep Wrangler', 'arquitectura colonial chilena', 'célula vegetal')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Número de imágenes a buscar y analizar (1-50, default: 10)",
                                "default": 10
                            },
                            "doctoral_area": {
                                "type": "string",
                                "description": "Área doctoral para enriquecer análisis (tecnología, medicina, arquitectura, historia, etc.)",
                                "enum": ["tecnologia", "medicina", "arquitectura", "historia", "legislacion", "investigacion", "creativo", "veterinaria", "bricolaje", "construccion"]
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analizar_imagen_academico",
                    "description": "Realiza análisis de una imagen con nivel doctoral usando Azure Computer Vision. Extrae objetos, personas, descripción, tags, marcas con síntesis académica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_url": {
                                "type": "string",
                                "description": "URL de la imagen a analizar"
                            },
                            "doctoral_context": {
                                "type": "string",
                                "description": "Contexto académico para análisis especializado (ej: 'medicina', 'botánica', 'ingeniería')"
                            }
                        },
                        "required": ["image_url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extraer_texto_imagen",
                    "description": "Extrae texto de imágenes usando OCR (Optical Character Recognition). Útil para documentos, señales, capturas de pantalla.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_url": {
                                "type": "string",
                                "description": "URL de la imagen que contiene texto"
                            }
                        },
                        "required": ["image_url"],
                    },
                },
            },
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
        # Herramientas privadas (solo para usuarios autorizados)
        private_tools = [
            "list_private_documents",
            "read_private_document",
            "search_private_documents",
            "analizar_sentimiento_texto",
            "detectar_idioma_texto",
            "extraer_frases_clave",
            "traducir_texto",
            "analizar_imagen_completa",
            "detectar_objetos_imagen",
            "detectar_personas_imagen",
            "describir_imagen",
            "extraer_texto_imagen",
            "buscar_imagenes",
            "analizar_imagen_academico",
            "navegar_url",
            "extraer_contenido_web",
            "buscar_en_google",
            "investigar_tema",
            "scrape_multiples_urls",
            "capturar_screenshot",
        ]
        if tool_name in private_tools:
            if not private_knowledge.is_authorized_user(self.user_id):
                return {
                    "success": False,
                    "error": "No tienes autorización para acceder a documentos privados"
                }
            try:
                # Delegar herramientas privadas de documentos
                if tool_name in ["list_private_documents", "read_private_document", "search_private_documents"]:
                    result = private_knowledge.execute_private_knowledge_function(tool_name, arguments or {})
                    return {"success": True, "result": result}
                # Herramientas de lenguaje/traducción
                if tool_name == "analizar_sentimiento_texto":
                    texto = (arguments or {}).get("texto") or ""
                    return {"success": True, "result": language_client.analyze_sentiment(texto)}
                if tool_name == "detectar_idioma_texto":
                    texto = (arguments or {}).get("texto") or ""
                    return {"success": True, "result": language_client.detect_language(texto)}
                if tool_name == "extraer_frases_clave":
                    texto = (arguments or {}).get("texto") or ""
                    return {"success": True, "result": language_client.extract_key_phrases(texto)}
                if tool_name == "traducir_texto":
                    texto = (arguments or {}).get("texto") or ""
                    destino = (arguments or {}).get("destino") or ""
                    origen = (arguments or {}).get("origen") or None
                    return {"success": True, "result": translator_client.translate_text(texto, destino, origen)}
                
                # Herramientas de Vision Computacional (solo si está disponible)
                if tool_name in ["analizar_imagen_completa", "detectar_objetos_imagen", "detectar_personas_imagen", "describir_imagen", "extraer_texto_imagen"]:
                    if not VISION_AVAILABLE:
                        return {"success": False, "error": "Módulo de visión no disponible. Instala: pip install azure-cognitiveservices-vision-computervision"}
                    
                    url_imagen = (arguments or {}).get("url_imagen") or ""
                    
                    if tool_name == "analizar_imagen_completa":
                        return {"success": True, "result": vision_client.analyze_image(url_imagen)}
                    elif tool_name == "detectar_objetos_imagen":
                        return {"success": True, "result": vision_client.detect_objects(url_imagen)}
                    elif tool_name == "detectar_personas_imagen":
                        return {"success": True, "result": vision_client.detect_people(url_imagen)}
                    elif tool_name == "describir_imagen":
                        return {"success": True, "result": vision_client.get_image_description(url_imagen)}
                    elif tool_name == "extraer_texto_imagen":
                        return {"success": True, "result": vision_client.extract_text_from_image(url_imagen)}
                
                # Herramientas de navegación web (solo si Steel Browser está disponible)
                if tool_name in ["navegar_url", "extraer_contenido_web", "buscar_en_google", "investigar_tema", "scrape_multiples_urls", "capturar_screenshot"]:
                    if not STEEL_BROWSER_AVAILABLE:
                        return {"success": False, "error": "Steel Browser no disponible"}
                    
                    steel_client = get_steel_browser_client()
                    
                    if tool_name == "navegar_url":
                        url = (arguments or {}).get("url", "")
                        wait_for = (arguments or {}).get("wait_for")
                        result = steel_client.navigate(url, wait_for)
                        return {"success": "error" not in result, "result": result}
                    
                    elif tool_name == "extraer_contenido_web":
                        url = (arguments or {}).get("url", "")
                        selector = (arguments or {}).get("selector")
                        result = steel_client.extract_content(url, selector)
                        return {"success": "error" not in result, "result": result}
                    
                    elif tool_name == "buscar_en_google":
                        query = (arguments or {}).get("query", "")
                        max_results = (arguments or {}).get("max_results", 5)
                        result = steel_client.search_and_extract(query, max_results)
                        return {"success": "error" not in result, "result": result}
                    
                    elif tool_name == "investigar_tema":
                        topic = (arguments or {}).get("topic", "")
                        depth = (arguments or {}).get("depth", "medium")
                        result = steel_client.research(topic, depth)
                        return {"success": "error" not in result, "result": result}
                    
                    elif tool_name == "scrape_multiples_urls":
                        urls = (arguments or {}).get("urls", [])
                        result = steel_client.scrape_multiple(urls[:10])  # Limitar a 10
                        return {"success": "error" not in result, "result": result}
                    
                    elif tool_name == "capturar_screenshot":
                        url = (arguments or {}).get("url", "")
                        full_page = (arguments or {}).get("full_page", False)
                        result = steel_client.screenshot(url, full_page)
                        return {"success": "error" not in result, "result": result}
                
                # Herramientas de búsqueda y análisis de imágenes
                if tool_name in ["buscar_imagenes", "analizar_imagen_academico", "extraer_texto_imagen"]:
                    if not VISION_SERVICE_AVAILABLE:
                        return {
                            "success": False,
                            "error": "Vision Service no está disponible"
                        }
                    
                    vision_service = get_vision_service_client()
                    
                    if tool_name == "buscar_imagenes":
                        if not STEEL_BROWSER_AVAILABLE:
                            return {
                                "success": False,
                                "error": "Steel Browser no está disponible para búsqueda de imágenes"
                            }
                        
                        steel_client = get_steel_browser_client()
                        query = (arguments or {}).get("query", "")
                        max_results = min(max(1, (arguments or {}).get("max_results", 10)), 50)
                        doctoral_area = (arguments or {}).get("doctoral_area")
                        
                        # Obtener imágenes desde Steel Browser
                        search_result = steel_client.search_images(query, max_results)
                        
                        if "error" in search_result or not search_result.get("images"):
                            return {"success": False, "error": "No se encontraron imágenes", "result": search_result}
                        
                        images = search_result.get("images", [])
                        
                        # Analizar cada imagen con Vision Service para síntesis doctoral
                        analyzed_images = []
                        for i, img in enumerate(images):
                            try:
                                url = img.get("url")
                                if not url:
                                    continue
                                
                                # Análisis with doctoral synthesis
                                analysis = vision_service.analyze_with_doctorate_synthesis(url, doctoral_area)
                                
                                # Enriquecer con información de la búsqueda
                                analysis["search_index"] = i + 1
                                analysis["search_title"] = img.get("title", "")
                                analysis["search_source"] = img.get("source", "")
                                
                                analyzed_images.append(analysis)
                            except Exception as e:
                                print(f"Error analizando imagen {i+1}: {e}")
                        
                        return {
                            "success": len(analyzed_images) > 0,
                            "query": query,
                            "total_found": len(images),
                            "total_analyzed": len(analyzed_images),
                            "images": analyzed_images
                        }
                    
                    elif tool_name == "analizar_imagen_academico":
                        image_url = (arguments or {}).get("image_url", "")
                        doctoral_context = (arguments or {}).get("doctoral_context")
                        
                        result = vision_service.analyze_with_doctorate_synthesis(image_url, doctoral_context)
                        return {"success": result.get("success", True), "result": result}
                    
                    elif tool_name == "extraer_texto_imagen":
                        image_url = (arguments or {}).get("image_url", "")
                        result = vision_service.extract_text(image_url)
                        return {"success": result.get("success", True), "result": result}
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
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
        
        return f"¡Perfecto! He enviado tu solicitud con éxito. Te responderemos lo antes posible."

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


def prepare_images_for_whatsapp(
    image_urls: List[str],
    chat_id: str,
    session: str = "default"
) -> Dict[str, Any]:
    """
    Prepara y envía imágenes a WhatsApp mediante WAHA.
    
    Args:
        image_urls: Lista de URLs de imágenes a enviar
        chat_id: ID del chat de WhatsApp
        session: Sesión WAHA
    
    Returns:
        Dict con resumen de envíos
    """
    # Importar aquí para evitar circular imports
    try:
        from server import _send_waha_images_batch
        result = _send_waha_images_batch(chat_id, image_urls, session, delay_between=0.5)
        return result
    except ImportError:
        return {
            "total": len(image_urls),
            "success": 0,
            "failed": len(image_urls),
            "error": "No se pudo cargar el módulo server para enviar imágenes"
        }


def get_hernando_tools(user_id: Optional[str] = None) -> HernandoTools:
    """
    Obtiene una instancia de HernandoTools.
    
    Args:
        user_id: ID del usuario (número de WhatsApp, etc.) para habilitar herramientas privadas
    
    Returns:
        Instancia de HernandoTools con herramientas apropiadas
    """
    return HernandoTools(user_id=user_id)
