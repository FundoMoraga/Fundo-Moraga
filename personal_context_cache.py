"""
Cache Personal Persistente para Efraín Moraga
Almacena contexto, preferencias, learning y prompts de Cosmos DB en Redis
Se actualiza continuamente con cada interacción
Accesible 24/7 con instrucciones estructuradas
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

try:
    from redis_cache import get_redis_cache
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from hernando_instructions_manual import get_instructions_manual, format_manual_for_prompt
    INSTRUCTIONS_AVAILABLE = True
except ImportError:
    INSTRUCTIONS_AVAILABLE = False
    get_instructions_manual = None

try:
    from prompts_loader import get_prompts_loader
    PROMPTS_LOADER_AVAILABLE = True
except ImportError:
    PROMPTS_LOADER_AVAILABLE = False
    get_prompts_loader = None


class PersonalContextCache:
    """
    Cache personal persistente para usuarios especiales (Efraín).
    
    CARACTERÍSTICAS ESTRUCTURALES (24/7):
    - Carga prompts de personalidad desde Cosmos DB
    - Carga manual de instrucciones para todas las capacidades
    - Almacena contexto, preferencias y learning
    - Sin expiración: permanente hasta que se limpie manualmente
    - Accesible a nivel aplicación para cualquier interacción
    
    DATOS GUARDADOS:
    - Prompts de personalidad desde Cosmos DB (actualizado cada 1h)
    - Manual de instrucciones (capacidades, procedimientos, ejemplos)
    - Preferencias de conversación
    - Temas recientes discutidos
    - Preguntas frecuentes de este usuario
    - Información compartida por el usuario
    - Estilo de comunicación aprendido
    - Notas de aprendizaje
    
    TTL: Sin expiración (persistente en Redis)
    Actualización: Continua con cada interacción + periódica para prompts
    """
    
    CACHE_PREFIX = "personal_context"
    COSMOS_PROMPTS_CACHE_TTL = 3600  # 1 hora para prompts de Cosmos
    COSMOS_PROMPTS_CACHE_KEY = f"{CACHE_PREFIX}:global:cosmos_prompts"
    INSTRUCTIONS_CACHE_KEY = f"{CACHE_PREFIX}:global:instructions_manual"
    
    def __init__(self):
        self.redis = None
        self.enabled = False
        self.cosmos_prompts_loaded_at = None
        self._cosmos_prompts_cache = {}
        self._instructions_manual = {}
        self._init_redis()
        self._load_instructions_manual()
        
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
                print("✅ Cache personal persistente inicializado (24/7)")
            else:
                print("⚠️ Redis no está habilitado")
                self.enabled = False
        except Exception as e:
            print(f"⚠️ Error inicializando cache personal: {e}")
            self.enabled = False
    
    def _load_instructions_manual(self) -> None:
        """
        Carga el manual de instrucciones al inicializar.
        Está disponible 24/7 en memoria sin necesidad de Redis.
        """
        if not INSTRUCTIONS_AVAILABLE:
            print("⚠️ Manual de instrucciones no disponible")
            self._instructions_manual = {}
            return
        
        try:
            if self.enabled and self.redis:
                cached = self.redis.get(self.INSTRUCTIONS_CACHE_KEY)
                if cached:
                    self._instructions_manual = json.loads(cached)
                    print("✅ Manual de instrucciones cargado desde Redis")
                    return

            self._instructions_manual = get_instructions_manual()
            if self.enabled and self.redis and self._instructions_manual:
                self.redis.set(self.INSTRUCTIONS_CACHE_KEY, json.dumps(self._instructions_manual))
            print(f"✅ Manual de instrucciones cargado ({len(self._instructions_manual)} capacidades)")
        except Exception as e:
            print(f"⚠️ Error cargando manual de instrucciones: {e}")
            self._instructions_manual = {}
    
    def _load_cosmos_prompts(self, force_reload: bool = False) -> Dict[str, str]:
        """
        Carga los prompts de personalidad desde Cosmos DB.
        Los mantiene en cache por 1 hora.
        
        Args:
            force_reload: Forzar recarga aunque esté en cache
        
        Returns:
            Dict con 'system' y 'operational' prompts
        """
        if not PROMPTS_LOADER_AVAILABLE:
            print("⚠️ Prompts loader no disponible")
            return {}
        
        # Verificar si tenemos cache válido (memoria)
        if not force_reload and self._cosmos_prompts_cache and self.cosmos_prompts_loaded_at:
            elapsed = (datetime.now(timezone.utc) - self.cosmos_prompts_loaded_at).total_seconds()
            if elapsed < self.COSMOS_PROMPTS_CACHE_TTL:
                return self._cosmos_prompts_cache

        # Verificar cache global en Redis (persistente 24/7)
        if not force_reload and self.enabled and self.redis:
            cached = self.redis.get(self.COSMOS_PROMPTS_CACHE_KEY)
            if cached:
                try:
                    payload = json.loads(cached)
                    cached_at = payload.get("cached_at")
                    prompts = payload.get("prompts") or {}
                    if cached_at:
                        cached_time = datetime.fromisoformat(cached_at)
                        if cached_time.tzinfo is None:
                            cached_time = cached_time.replace(tzinfo=timezone.utc)
                        elapsed = (datetime.now(timezone.utc) - cached_time).total_seconds()
                        if elapsed < self.COSMOS_PROMPTS_CACHE_TTL:
                            self._cosmos_prompts_cache = prompts
                            self.cosmos_prompts_loaded_at = cached_time
                            print("✅ Prompts de Cosmos DB cargados desde Redis")
                            return prompts
                except Exception as e:
                    print(f"⚠️ Error leyendo cache de prompts en Redis: {e}")
        
        try:
            loader = get_prompts_loader()
            prompts = loader.get_prompts(
                persona="Hernando",
                fallback_system_prompt="",
                fallback_operational_prompt=""
            )
            
            self._cosmos_prompts_cache = prompts
            self.cosmos_prompts_loaded_at = datetime.now(timezone.utc)
            if self.enabled and self.redis:
                payload = {
                    "cached_at": self.cosmos_prompts_loaded_at.isoformat(),
                    "prompts": prompts,
                }
                self.redis.set(self.COSMOS_PROMPTS_CACHE_KEY, json.dumps(payload))
            print(f"✅ Prompts de Cosmos DB cargados para cache personal")
            return prompts
        
        except Exception as e:
            print(f"⚠️ Error cargando prompts de Cosmos DB: {e}")
            return self._cosmos_prompts_cache  # Devolver último cache válido si falla
    
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
        Incluye información de Cosmos DB y manual de instrucciones.
        
        Ejemplo:
        "Efraín ha hablado conmigo 47 veces. Le interesa turismo, tecnología,
        y tiene un estilo directo. Ha preguntado sobre precios, vehículos 4x4.
        Tiene acceso a [web_search, image_analysis, report_generation, ...]"
        
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
        
        # Cargar prompts de Cosmos DB
        cosmos_prompts = self._load_cosmos_prompts()
        prompts_info = f"Sistema personalizado de Cosmos DB ({len(cosmos_prompts)} prompts)"
        
        # Información del manual de instrucciones
        capabilities = list(self._instructions_manual.keys())
        capabilities_info = f"Acceso a {len(capabilities)} capacidades: {', '.join(capabilities[:5])}..."
        
        summary = f"""Contexto personal de Efraín Moraga:
- Interacciones previas: {interaction_count}
- Temas de interés: {', '.join(topics) if topics else 'ninguno'}
- Estilo de comunicación: {style}
- {prompts_info}
- {capabilities_info}
- Última interacción: {context.get('updated_at', 'N/A')}"""
        
        return summary
    
    def get_cosmos_prompts(self, force_reload: bool = False) -> Dict[str, str]:
        """
        Obtiene los prompts de personalidad desde Cosmos DB.
        Cacheados por 1 hora.
        
        Args:
            force_reload: Forzar recarga
        
        Returns:
            Dict con 'system' y 'operational' keys
        """
        return self._load_cosmos_prompts(force_reload)
    
    def get_instructions_for_capability(self, capability: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene instrucciones detalladas para una capacidad específica.
        Útil para inyectar en contexto cuando se detecta una necesidad.
        
        Args:
            capability: Nombre de la capacidad (ej: "web_search", "image_analysis")
        
        Returns:
            Dict con instrucciones detalladas, o None
        """
        return self._instructions_manual.get(capability)
    
    def get_all_capabilities(self) -> List[str]:
        """
        Obtiene lista de todas las capacidades disponibles.
        
        Returns:
            Lista de nombres de capacidades
        """
        return list(self._instructions_manual.keys())
    
    def get_instructions_summary(self) -> str:
        """
        Obtiene un resumen formateado del manual completo.
        Útil para inyectar en prompts cuando es necesario.
        
        Returns:
            String con manual formateado
        """
        if not INSTRUCTIONS_AVAILABLE:
            return "Manual de instrucciones no disponible"
        
        try:
            return format_manual_for_prompt()
        except Exception as e:
            print(f"⚠️ Error formateando resumen de instrucciones: {e}")
            return ""

    def refresh_instructions_manual(self) -> None:
        """
        Fuerza la recarga del manual de instrucciones desde el archivo local
        y lo persiste en Redis para acceso 24/7.
        """
        if not INSTRUCTIONS_AVAILABLE:
            return

        try:
            self._instructions_manual = get_instructions_manual()
            if self.enabled and self.redis and self._instructions_manual:
                self.redis.set(self.INSTRUCTIONS_CACHE_KEY, json.dumps(self._instructions_manual))
            print(f"✅ Manual de instrucciones recargado ({len(self._instructions_manual)} capacidades)")
        except Exception as e:
            print(f"⚠️ Error recargando manual de instrucciones: {e}")
    
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
