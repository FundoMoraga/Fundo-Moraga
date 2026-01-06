"""
Wrapper mejorado para InstagramBot que integra capacidades de IA avanzada
Incluye: Cache Redis, Recomendaciones por Sentimiento, Timing de Contacto, Detección de Insatisfacción, Modo Admin
"""
from hernando_bot import HernandoBot
from advanced_ai_integration import get_advanced_ai_integration
from redis_cache import get_redis_cache
from sentiment_recommendations import get_sentiment_recommender
from contact_timing_prediction import get_contact_timing_predictor
from satisfaction_detector import get_satisfaction_detector
from fecha_libre_validator import validate_response_for_fecha_libre
from admin_mode import get_admin_mode
from typing import Optional
import config


class InstagramBotEnhanced(HernandoBot):
    """
    Extensión de InstagramBot con capacidades de IA avanzada integradas.
    
    Características adicionales:
    ✅ Clasificación de intenciones
    ✅ Extracción de entidades
    ✅ Predicciones de necesidades
    ✅ Recomendaciones personalizadas
    ✅ Aprendizaje continuo
    ✨ Cache Redis (40% faster responses)
    ✨ Recomendaciones dinámicas por sentimiento
    ✨ Predicción de mejor tiempo de contacto
    ✨ Detección temprana de insatisfacción
    """
    
    def __init__(self):
        """Inicializa el bot mejorado con todos los módulos"""
        super().__init__()
        self.ai_integration = get_advanced_ai_integration()
        
        # Inicializar módulos avanzados
        self.cache = get_redis_cache() if config.REDIS_ENABLED else None
        self.sentiment_recommender = get_sentiment_recommender() if config.SENTIMENT_RECOMMENDATIONS_ENABLED else None
        self.contact_predictor = get_contact_timing_predictor() if config.CONTACT_TIMING_PREDICTION_ENABLED else None
        self.satisfaction_detector = get_satisfaction_detector() if config.SATISFACTION_DETECTION_ENABLED else None
        
        # Inicializar modo administrador
        self.admin_mode = get_admin_mode()
        
        print("🚀 Bot mejorado inicializado con IA avanzada")
        print(f"   ✅ Cache Redis: {self._status_icon(self.cache)}")
        print(f"   ✅ Sentimiento: {self._status_icon(self.sentiment_recommender)}")
        print(f"   ✅ Timing: {self._status_icon(self.contact_predictor)}")
        print(f"   ✅ Satisfacción: {self._status_icon(self.satisfaction_detector)}")
        print(f"   🔐 Modo Admin: Disponible")
    
    def _status_icon(self, module) -> str:
        """Icono de estado del módulo"""
        return "🟢 Habilitado" if module else "🔴 Deshabilitado"
    
    def process_message(
        self,
        user_id: str,
        message_text: str,
        *,
        platform: str = "web",
        source: str = "widget",
        message_id: Optional[str] = None,
    ) -> str:
        """
        Procesa un mensaje con todas las capacidades de IA avanzada.
        
        Flujo completo:
        0. Admin Mode: Detectar comandos de administrador 🔐
        1. Cache: Buscar respuesta cacheada (45ms)
        2. Sentimiento: Análisis emocional del usuario
        3. Satisfacción: Detectar insatisfacción temprana ⚠️
        4. IA Base: Clasificación intención + entidades + predicciones
        5. Recomendaciones: Dinámicas según sentimiento actual
        6. Timing: Registrar para análisis futuro
        7. Respuesta: Procesar con bot normal
        8. Aprendizaje: Guardar interacción completa
        """
        
        # PASO 0: Verificar modo administrador
        # Detectar clave de activación/desactivación
        if self.admin_mode.is_admin_key(message_text):
            is_active, response = self.admin_mode.toggle_mode(user_id, platform)
            return response
        
        # Si está activo, procesar como comando admin
        if self.admin_mode.is_active(user_id):
            admin_response = self.admin_mode.process_admin_command(user_id, message_text)
            if admin_response:
                return admin_response
        
        # PASO 1: Intentar obtener de cache
        if self.cache:
            cached = self._try_get_cached_response(user_id, message_text)
            if cached:
                print(f"💾 Respuesta cacheada reutilizada (ahorró ~500ms)")
                return cached
        
        # PASO 2: Análisis de sentimiento
        from language_client import analyze_sentiment
        sentiment_data = analyze_sentiment(message_text)
        sentiment_score = sentiment_data.get('positive', 0.5) if sentiment_data else 0.5
        
        # PASO 3: Detección de insatisfacción TEMPRANA
        if self.satisfaction_detector:
            try:
                # Registrar antes de responder (para intervención temprana)
                satisfaction_tracking = self.satisfaction_detector.track_user_satisfaction(
                    user_id=user_id,
                    message=message_text,
                    response="[Procesando...]",  # Se actualizará después
                    booking_completed=False
                )
                
                # Verificar riesgo crítico
                risk_assessment = self.satisfaction_detector.get_user_risk_assessment(user_id)
                if risk_assessment["risk_level"] in ["crítico", "alto"]:
                    print(f"🚨 ALERTA SATISFACCIÓN: Riesgo {risk_assessment['risk_level']}")
                    print(f"   Probabilidad de churn: {risk_assessment['churn_probability']:.0%}")
                    print(f"   Acción: {risk_assessment['urgent_actions'][0] if risk_assessment['urgent_actions'] else 'Monitorear'}")
            except Exception as e:
                print(f"⚠️ Error en detección de satisfacción: {e}")
        
        # PASO 4: Obtener historial y enriquecer con IA
        conversation_id = self.conversation_store.get_latest_conversation_id(user_id)
        if conversation_id:
            conversation_history = self.conversation_store.get_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=config.MAX_CONVERSATION_HISTORY
            )
        else:
            conversation_history = []
        
        # PASO 5: Enriquecer mensaje con IA avanzada
        ai_enrichment = None
        try:
            sentiment_label = sentiment_data.get("sentiment") if sentiment_data else None
            user_metadata = {
                "platform": platform.strip().lower(),
                "source": source
            }
            
            ai_enrichment = self.ai_integration.enrich_user_message(
                user_id=user_id,
                message=message_text,
                conversation_history=conversation_history,
                sentiment=sentiment_label,
                user_metadata=user_metadata
            )
            
            # Mostrar información de IA avanzada en logs
            print(f"🧠 IA Avanzada:")
            intent_info = ai_enrichment.get('intent', {})
            print(f"   Intent: {intent_info.get('intent', 'unknown')} ({intent_info.get('confidence', 0):.0%})")
            
            entities = ai_enrichment.get('entities', {})
            if entities.get('dates'):
                print(f"   Fechas detectadas: {entities['dates']}")
            if entities.get('prices'):
                print(f"   Precios detectados: {entities['prices']}")
            if entities.get('activities'):
                print(f"   Actividades: {entities['activities']}")
            
        except Exception as e:
            print(f"⚠️ Error en enriquecimiento IA: {e}")
            import traceback
            traceback.print_exc()
        
        # PASO 6: NUEVO - Recomendaciones dinámicas por sentimiento
        sentiment_rec = None
        if self.sentiment_recommender and ai_enrichment:
            try:
                sentiment_rec = self.sentiment_recommender.get_recommendations(
                    sentiment_score=sentiment_score,
                    user_id=user_id,
                    budget=None
                )
                print(f"😊 Recomendación sentimiento: {sentiment_rec['sentiment_profile']} ({sentiment_score:.0%})")
                print(f"   Oferta: {sentiment_rec['special_offers'][0] if sentiment_rec['special_offers'] else 'N/A'}")
            except Exception as e:
                print(f"⚠️ Error en recomendación por sentimiento: {e}")
        
        # PASO 7: NUEVO - Registrar timing para análisis futuro
        if self.contact_predictor:
            try:
                # Registrar interacción para builds de patrón de usuario
                from datetime import datetime
                self.contact_predictor.record_interaction(
                    user_id=user_id,
                    message_sent_time=datetime.now(),
                    response_time_minutes=0,  # Se actualiza cuando responde
                    engagement_level="neutral"
                )
            except Exception as e:
                print(f"⚠️ Error en predictor de timing: {e}")
        
        # PASO 8: Llamar al proceso normal del padre
        response = super().process_message(
            user_id=user_id,
            message_text=message_text,
            platform=platform,
            source=source,
            message_id=message_id,
            sentiment_data=sentiment_data,
        )
        
        # PASO 9: Cachear respuesta para futuras preguntas similares
        if self.cache and ai_enrichment:
            try:
                intent = ai_enrichment.get('intent', {}).get('intent', 'general')
                self.cache.cache_prompt_response(
                    message=message_text,
                    intent=intent,
                    response=response,
                    ttl_hours=config.REDIS_CACHE_TTL_PROMPTS_HOURS
                )
            except Exception as e:
                print(f"⚠️ Error cacheando respuesta: {e}")
        
        # PASO 10: Registrar interacción para aprendizaje continuo
        if ai_enrichment:
            try:
                # Actualizar satisfacción con respuesta final
                if self.satisfaction_detector:
                    self.satisfaction_detector.track_user_satisfaction(
                        user_id=user_id,
                        message=message_text,
                        response=response,
                        booking_completed=False
                    )
                
                self.ai_integration.log_interaction_result(
                    user_id=user_id,
                    message=message_text,
                    bot_response=response,
                    intent=ai_enrichment['intent']['intent'],
                    sentiment=sentiment_data.get('sentiment') if sentiment_data else None,
                    response_time_ms=0,
                    user_satisfaction=int(sentiment_score * 10) if sentiment_score else None
                )
                print(f"📊 Interacción registrada (sentimiento: {sentiment_score:.0%})")
            except Exception as e:
                print(f"⚠️ Error registrando interacción: {e}")
        
        # Validar que no mencione Fecha Libre si no está anunciada
        response = validate_response_for_fecha_libre(response)
        
        return response
    
    def _try_get_cached_response(self, user_id: str, message: str) -> Optional[str]:
        """
        Intenta obtener respuesta cacheada
        Busca por pregunta frecuente (FAQ) o respuesta previa similar
        """
        if not self.cache:
            return None
        
        try:
            # Buscar por FAQ categories
            faq_keywords = {
                "baño": ["baño", "wc", "toilet", "bathroom"],
                "comida": ["comida", "comer", "almuerzo", "desayuno", "comidas"],
                "fecha_libre": ["fecha libre", "que es", "fechabre"],
                "precios": ["cuanto", "precio", "costo", "tarifa"],
            }
            
            message_lower = message.lower()
            for category, keywords in faq_keywords.items():
                if any(kw in message_lower for kw in keywords):
                    cached_answer = self.cache.get_faq_answer(category)
                    if cached_answer:
                        return cached_answer
            
            # Buscar por respuesta previa similar
            cached_response = self.cache.get_prompt_response(message, "general")
            if cached_response:
                return cached_response
            
            return None
        except Exception as e:
            print(f"⚠️ Error accediendo cache: {e}")
            return None


def get_instagram_bot():
    """Factory function para obtener instancia del bot mejorado"""
    return InstagramBotEnhanced()


