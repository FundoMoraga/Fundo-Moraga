"""
Clasificador de intenciones del usuario
Identifica automáticamente el tipo de solicitud (reserva, consulta, pago, soporte, etc.)
"""
from typing import Dict, Any, List
import json
from datetime import datetime
import config
import os

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class IntentClassifier:
    """Clasifica la intención del mensaje del usuario"""
    
    # Tipos de intención soportados
    INTENT_TYPES = {
        "reserva": "Usuario quiere reservar una actividad/evento",
        "consulta": "Usuario pregunta sobre información (precios, fechas, servicios)",
        "pago": "Usuario consulta sobre pago o confirma transferencia",
        "soporte": "Usuario reporta problema o necesita ayuda técnica",
        "saludos": "Saludo o conversación casual",
        "recomendacion": "Usuario pide recomendación personalizada",
        "disponibilidad": "Usuario pregunta disponibilidad de fechas",
        "analisis_imagen": "Usuario quiere que analices una imagen (qué es, qué contiene, identificar algo)",
        "subir_archivo": "Usuario quiere guardar/almacenar un archivo en el volumen privado",
        "otro": "No encaja en otras categorías"
    }
    
    # Intenciones específicas para imágenes
    IMAGE_INTENT_KEYWORDS = {
        "analisis_imagen": [
            "qué es", "que es", "identificar", "analizar", "analiza", "dime qué",
            "reconocer", "detectar", "ver qué hay", "describe", "explica",
            "qué tiene", "que tiene", "qué contiene", "que contiene",
            "qué hay en", "que hay en", "qué aparece", "que aparece",
            "mostrar qué", "decir qué", "identificame", "analízame",
            "necesito saber", "quiero saber", "ayúdame a identificar"
        ],
        "subir_archivo": [
            "guarda", "guardar", "almacena", "almacenar", "sube", "subir",
            "archiva", "archivar", "guárdalo", "guardalo", "guardame",
            "añade", "agregar", "agrégalo", "agregalo", "ponlo en",
            "save", "upload", "store", "volumen privado"
        ]
    }
    
    def __init__(self):
        """Inicializa el clasificador"""
        self.client = None
        if _OPENAI_AVAILABLE and config.OPENAI_API_KEY and getattr(config, "ADVANCED_AI_USE_OPENAI", False):
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def classify(self, message: str, conversation_context: List[Dict] = None) -> Dict[str, Any]:
        """
        Clasifica la intención del mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            conversation_context: Lista de mensajes anteriores para contexto
            
        Returns:
            {
                'intent': str,
                'confidence': float (0-1),
                'entities': {'dates': [], 'amounts': [], 'activities': []},
                'action_needed': bool,
                'urgency': str (bajo/medio/alto),
                'followup_suggestion': str
            }
        """
        if not self.client:
            return self._fallback_classify(message)
        
        try:
            # Construir prompt para GPT
            context_str = ""
            if conversation_context:
                context_str = "\nContexto de conversación anterior:\n"
                for i, msg in enumerate(conversation_context[-3:]):  # últimos 3 mensajes
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    context_str += f"{role.capitalize()}: {content}\n"
            
            prompt = f"""Clasifica la intención del siguiente mensaje de usuario.

TIPOS DE INTENCIÓN DISPONIBLES:
{chr(10).join([f"- {intent}: {desc}" for intent, desc in self.INTENT_TYPES.items()])}

{context_str}

MENSAJE ACTUAL: "{message}"

Responde SOLO con un JSON (sin código markdown, sin explicaciones):
{{
    "intent": "<uno de los tipos arriba>",
    "confidence": 0.95,
    "urgency": "bajo|medio|alto",
    "action_needed": true|false,
    "entities": {{
        "dates": [],
        "amounts": [],
        "activities": [],
        "locations": []
    }},
    "followup_suggestion": "Pregunta sugerida para hacer al usuario si aplica"
}}"""
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_completion_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar markdown si viene envuelto
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            result['method'] = 'gpt'
            return result
            
        except Exception as e:
            print(f"⚠️ Error clasificando intención con GPT: {e}")
            return self._fallback_classify(message)
    
    def _fallback_classify(self, message: str) -> Dict[str, Any]:
        """
        Clasificación basada en palabras clave (fallback si GPT no disponible)
        """
        msg_lower = message.lower()
        
        # Patrones de palabras clave
        patterns = {
            "reserva": ["reserv", "quiero ir", "agendar", "agende", "me gustaría venir", "booking"],
            "consulta": ["cuánto cuesta", "cuál es", "dónde", "cómo", "qué", "cuando", "precio", "valor", "costo"],
            "pago": ["pago", "transferencia", "transfer", "pague", "pagué", "bancario", "confirmar pago"],
            "disponibilidad": ["disponible", "disponibilidad", "cuándo", "qué día", "qué fechas"],
            "soporte": ["error", "problema", "no funciona", "falla", "bug", "ayuda"],
            "recomendacion": ["recomiendam", "qué me recomendas", "cuál es mejor", "cuál recomiendas"],
            "saludos": ["hola", "buenos", "buenas", "hiii", "aloha", "wena", "ey", "hey"],
            "analisis_imagen": self.IMAGE_INTENT_KEYWORDS["analisis_imagen"],
            "subir_archivo": self.IMAGE_INTENT_KEYWORDS["subir_archivo"]
        }
        
        # Detectar intención
        detected_intent = "otro"
        for intent, keywords in patterns.items():
            if any(kw in msg_lower for kw in keywords):
                detected_intent = intent
                break
        
        # Calcular urgencia (simple heurística)
        urgency_markers = ["ahora", "urgente", "rápido", "inmediato", "asap", "hoy"]
        urgency = "alto" if any(m in msg_lower for m in urgency_markers) else "medio"
        
        return {
            "intent": detected_intent,
            "confidence": 0.6,
            "urgency": urgency,
            "action_needed": detected_intent in ["reserva", "pago", "soporte"],
            "entities": {
                "dates": [],
                "amounts": [],
                "activities": [],
                "locations": []
            },
            "followup_suggestion": None,
            "method": "fallback"
        }

    def classify_image_intent(self, caption_text: str, user_id: str = None) -> Dict[str, Any]:
        """
        Clasifica la intención cuando el usuario envía una imagen con texto.
        Determina si quiere ANALIZAR la imagen o GUARDARLA en el volumen privado.
        
        Args:
            caption_text: Texto que acompaña a la imagen
            user_id: ID del usuario (para verificar permisos de volumen privado)
        
        Returns:
            Dict con:
            - intent: "analisis_imagen" o "subir_archivo"
            - confidence: 0-1
            - reasoning: Explicación de por qué se eligió esa intención
        """
        import private_knowledge
        
        # Si no hay texto, asumir análisis por defecto
        if not caption_text or caption_text.strip() == "" or caption_text == "[adjunto]":
            return {
                "intent": "analisis_imagen",
                "confidence": 0.5,
                "reasoning": "No hay texto que indique intención de guardar, asumo análisis"
            }
        
        msg_lower = caption_text.lower()
        
        # Verificar keywords explícitos de análisis (mayor prioridad)
        analysis_score = 0
        for keyword in self.IMAGE_INTENT_KEYWORDS["analisis_imagen"]:
            if keyword in msg_lower:
                analysis_score += 1
        
        # Verificar keywords de subida
        upload_score = 0
        for keyword in self.IMAGE_INTENT_KEYWORDS["subir_archivo"]:
            if keyword in msg_lower:
                upload_score += 1
        
        # Si el usuario NO está autorizado, siempre análisis (no puede subir)
        is_authorized = private_knowledge.is_authorized_user(user_id) if user_id else False
        
        if not is_authorized and upload_score > 0:
            return {
                "intent": "analisis_imagen",
                "confidence": 0.9,
                "reasoning": "Usuario solicitó subir archivo pero no está autorizado para volumen privado"
            }
        
        # Decidir basado en scores
        if analysis_score > upload_score:
            confidence = min(0.95, 0.6 + (analysis_score * 0.1))
            return {
                "intent": "analisis_imagen",
                "confidence": confidence,
                "reasoning": f"Detecté {analysis_score} palabras de análisis vs {upload_score} de subida"
            }
        elif upload_score > analysis_score and is_authorized:
            confidence = min(0.95, 0.6 + (upload_score * 0.1))
            return {
                "intent": "subir_archivo",
                "confidence": confidence,
                "reasoning": f"Detecté {upload_score} palabras de subida vs {analysis_score} de análisis, usuario autorizado"
            }
        else:
            # Empate o sin keywords claros: analizar por defecto (más seguro)
            return {
                "intent": "analisis_imagen",
                "confidence": 0.7,
                "reasoning": "Sin keywords claros de intención específica, analizo por defecto"
            }


def get_intent_classifier() -> IntentClassifier:
    """Obtiene instancia singleton del clasificador"""
    global _classifier
    if '_classifier' not in globals():
        _classifier = IntentClassifier()
    return _classifier
