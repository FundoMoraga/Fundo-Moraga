"""
Cache Personal Persistente para Efraín Moraga
Almacena contexto, preferencias y learning en Redis
Se actualiza continuamente con cada interacción
"""
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import private_knowledge
import config

try:
    from redis_cache import get_redis_cache
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class PersonalContextCache:
    """
    Cache personal persistente para usuarios especiales (Efraín).
    
    Guarda:
    - Preferencias de conversación
    - Temas recientes discutidos
    - Preguntas frecuentes de este usuario
    - Información que el usuario ha compartido
    - Estilo de comunicación aprendido
    
    TTL: Se actualiza continuamente, sin expiración
    """
    
    CACHE_PREFIX = "personal_context"
    
    def __init__(self):
        self.redis = None
        self.enabled = False
        self._init_redis()
    
    def _init_redis(self) -> None:
        """Inicializa conexión a Redis"""
        if not REDIS_AVAILABLE:
            print("⚠️ Redis no disponible para cache personal")
            self.enabled = False
            return
        
        try:
            cache = get_redis_cache()
            if cache.enabled and cache.client:
                self.redis = cache.client
                self.enabled = True
                print("✅ Cache personal persistente inicializado")
            else:
                print("⚠️ Redis no está habilitado")
                self.enabled = False
        except Exception as e:
            print(f"⚠️ Error inicializando cache personal: {e}")
            self.enabled = False
    
    def _get_user_key(self, user_id: str) -> str:
        """Genera clave de cache para un usuario"""
        return f"{self.CACHE_PREFIX}:{user_id}"
    
    def get_personal_context(self, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Obtiene el contexto personal guardado de un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Diccionario con contexto personal, o None
        """
        if not self.enabled or not user_id:
            return None
        
        try:
            key = self._get_user_key(user_id)
            cached = self.redis.get(key)
            
            if cached:
                context = json.loads(cached)
                print(f"📌 Contexto personal cargado para {user_id}")
                return context
        except Exception as e:
            print(f"⚠️ Error obteniendo contexto personal: {e}")
        
        return None
    
    def update_personal_context(
        self,
        user_id: str,
        user_message: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Actualiza el contexto personal después de cada mensaje.
        Se llama automáticamente después de cada interacción.
        
        Args:
            user_id: ID del usuario
            user_message: Mensaje del usuario
            response: Respuesta de Hernando
            metadata: Información adicional (intención, sentiment, etc.)
        """
        if not self.enabled or not user_id:
            return
        
        try:
            key = self._get_user_key(user_id)
            
            # Obtener contexto existente
            existing = self.get_personal_context(user_id)
            
            if not existing:
                # Crear nuevo contexto
                context = {
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "interaction_count": 0,
                    "topics": [],
                    "preferences": {},
                    "recent_messages": [],
                    "learning_notes": []
                }
            else:
                context = existing
            
            # Actualizar contador e información
            context["updated_at"] = datetime.now(timezone.utc).isoformat()
            context["interaction_count"] = context.get("interaction_count", 0) + 1
            context["last_user_message"] = user_message
            context["last_response"] = response
            
            # Mantener histórico reciente (últimos 20 mensajes)
            recent = context.get("recent_messages", [])
            recent.append({
                "user": user_message,
                "bot": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            })
            context["recent_messages"] = recent[-20:]  # Keep last 20
            
            # Extraer temas del mensaje
            topics = self._extract_topics(user_message)
            existing_topics = set(context.get("topics", []))
            existing_topics.update(topics)
            context["topics"] = list(existing_topics)[-30:]  # Keep last 30 unique
            
            # Guardar en Redis (sin expiración, persistente)
            self.redis.set(
                key,
                json.dumps(context),
                nx=False  # Overwrite si existe
            )
            
            print(f"✅ Contexto personal actualizado ({context['interaction_count']} interacciones)")
            
        except Exception as e:
            print(f"⚠️ Error actualizando contexto personal: {e}")
    
    def get_context_summary(self, user_id: str) -> Optional[str]:
        """
        Genera un resumen del contexto personal para usar en prompts.
        
        Ejemplo:
        "Efraín ha hablado conmigo 47 veces. Le interesa turismo, tecnología,
        y tiene un estilo directo. Ha preguntado sobre precios, vehículos 4x4."
        
        Args:
            user_id: ID del usuario
        
        Returns:
            String con resumen para inyectar en system prompt
        """
        context = self.get_personal_context(user_id)
        if not context:
            return None
        
        interaction_count = context.get("interaction_count", 0)
        topics = context.get("topics", [])[:5]  # Top 5 topics
        recent = context.get("recent_messages", [])[-3:]  # Last 3 messages
        
        # Analizar patrón de comunicación
        style = self._analyze_communication_style(recent)
        
        summary = f"""Contexto personal del usuario:
- Interacciones previas: {interaction_count}
- Temas de interés: {', '.join(topics) if topics else 'ninguno'}
- Estilo de comunicación: {style}
- Última interacción: {context.get('updated_at', 'N/A')}"""
        
        return summary
    
    def _extract_topics(self, message: str) -> List[str]:
        """
        Extrae temas principales del mensaje.
        
        Args:
            message: Mensaje del usuario
        
        Returns:
            Lista de temas identificados
        """
        topics = []
        message_lower = message.lower()
        
        # Diccionario de palabras clave → tema
        topic_keywords = {
            "turismo": ["turismo", "tour", "viaje", "visita", "excursión", "batuco"],
            "tecnología": ["código", "python", "javascript", "api", "función", "técnico", "software"],
            "precios": ["cuánto", "precio", "costo", "tarifa", "valor", "pago"],
            "vehículos": ["auto", "vehículo", "4x4", "carro", "camioneta", "moto"],
            "reservas": ["reserva", "booking", "fecha", "disponible", "agenda"],
            "información": ["qué es", "explica", "cuéntame", "información", "detalles"],
            "ayuda": ["ayuda", "help", "problema", "error", "no funciona"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _analyze_communication_style(self, recent_messages: List[Dict]) -> str:
        """
        Analiza el estilo de comunicación basado en mensajes recientes.
        
        Args:
            recent_messages: Últimos mensajes del usuario
        
        Returns:
            Descripción del estilo (ej: "directo", "formal", "conversacional")
        """
        if not recent_messages:
            return "neutral"
        
        style_indicators = {
            "directo": 0,
            "conversacional": 0,
            "formal": 0,
            "técnico": 0
        }
        
        for msg_obj in recent_messages:
            user_msg = msg_obj.get("user", "").lower()
            
            # Análisis simple
            if any(word in user_msg for word in ["hola", "cómo", "gracias", "por favor"]):
                style_indicators["conversacional"] += 1
            
            if any(word in user_msg for word in ["necesito", "quiero", "dame", "dame"]):
                style_indicators["directo"] += 1
            
            if any(word in user_msg for word in ["código", "función", "algoritmo", "api"]):
                style_indicators["técnico"] += 1
            
            if "?" not in user_msg and len(user_msg) > 30:
                style_indicators["formal"] += 1
        
        # Retornar estilo más probable
        dominant_style = max(style_indicators.items(), key=lambda x: x[1])[0]
        return dominant_style
    
    def add_learning_note(self, user_id: str, note: str) -> None:
        """
        Agrega una nota de aprendizaje sobre el usuario.
        Notas manuales que Hernando quiere recordar.
        
        Ejemplo: "Efraín prefiere respuestas técnicas y directas"
        
        Args:
            user_id: ID del usuario
            note: Nota de aprendizaje
        """
        if not self.enabled or not user_id:
            return
        
        try:
            key = self._get_user_key(user_id)
            context = self.get_personal_context(user_id)
            
            if not context:
                context = {
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "learning_notes": []
                }
            
            # Agregar nota con timestamp
            notes = context.get("learning_notes", [])
            notes.append({
                "note": note,
                "added_at": datetime.now(timezone.utc).isoformat()
            })
            
            context["learning_notes"] = notes[-20:]  # Keep last 20 notes
            context["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            self.redis.set(key, json.dumps(context))
            print(f"📝 Nota de aprendizaje agregada: {note}")
            
        except Exception as e:
            print(f"⚠️ Error agregando nota de aprendizaje: {e}")
    
    def get_learning_notes(self, user_id: str) -> List[str]:
        """
        Obtiene las notas de aprendizaje sobre este usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de notas de aprendizaje
        """
        context = self.get_personal_context(user_id)
        if not context:
            return []
        
        notes = context.get("learning_notes", [])
        return [n.get("note") for n in notes if n.get("note")]
    
    def clear_cache(self, user_id: str) -> bool:
        """
        Limpia el cache personal de un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si se limpió exitosamente
        """
        if not self.enabled or not user_id:
            return False
        
        try:
            key = self._get_user_key(user_id)
            self.redis.delete(key)
            print(f"🗑️ Cache personal limpiado para {user_id}")
            return True
        except Exception as e:
            print(f"⚠️ Error limpiando cache personal: {e}")
            return False


# Singleton instance
_personal_cache = None


def get_personal_cache() -> PersonalContextCache:
    """Obtiene instancia singleton del cache personal"""
    global _personal_cache
    if _personal_cache is None:
        _personal_cache = PersonalContextCache()
    return _personal_cache
