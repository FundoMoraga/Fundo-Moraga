"""
Wrapper mejorado para InstagramBot que integra capacidades de IA avanzada
"""
from instagram_bot import InstagramBot
from advanced_ai_integration import get_advanced_ai_integration
from typing import Optional
import config


class InstagramBotEnhanced(InstagramBot):
    """
    Extensión de InstagramBot con capacidades de IA avanzada integradas.
    
    Características adicionales:
    - Clasificación de intenciones
    - Extracción de entidades
    - Predicciones de necesidades
    - Recomendaciones personalizadas
    - Aprendizaje continuo
    """
    
    def __init__(self):
        """Inicializa el bot mejorado"""
        super().__init__()
        self.ai_integration = get_advanced_ai_integration()
        print("🚀 Bot mejorado inicializado con IA avanzada")
    
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
        Procesa un mensaje con capacidades de IA avanzada.
        
        Flujo:
        1. Análisis de sentimiento (heredado)
        2. NUEVO: Clasificación de intención
        3. NUEVO: Extracción de entidades
        4. NUEVO: Análisis de patrones de usuario
        5. NUEVO: Predicciones de necesidades
        6. NUEVO: Recomendaciones personalizadas
        7. Procesamiento normal del mensaje
        8. NUEVO: Registro de interacción para aprendizaje
        """
        
        # Obtener análisis de sentimiento antes de llamar al padre
        from language_client import analyze_sentiment
        sentiment_data = analyze_sentiment(message_text)
        
        # Obtener historial para enriquecimiento
        conversation_id = self.conversation_store.get_latest_conversation_id(user_id)
        if conversation_id:
            conversation_history = self.conversation_store.get_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=config.MAX_CONVERSATION_HISTORY
            )
        else:
            conversation_history = []
        
        # Enriquecer mensaje con IA avanzada
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
            print(f"   Intent: {intent_info.get('intent', 'unknown')} " 
                  f"({intent_info.get('confidence', 0):.0%})")
            
            entities = ai_enrichment.get('entities', {})
            if entities.get('dates'):
                print(f"   Fechas detectadas: {entities['dates']}")
            if entities.get('prices'):
                print(f"   Precios detectados: {entities['prices']}")
            if entities.get('activities'):
                print(f"   Actividades: {entities['activities']}")
            
            predictions = ai_enrichment.get('predictions', {})
            if predictions.get('predicted_needs'):
                needs = predictions['predicted_needs']
                if needs:
                    print(f"   Predicción: {needs[0]}")
            
            recommendations = ai_enrichment.get('recommendations', {})
            primary_rec = recommendations.get('primary_recommendation')
            if primary_rec:
                print(f"   Recomendación: {primary_rec.get('activity')}")
            
            # Guardar enriquecimiento como metadata en Cosmos DB
            if conversation_id:
                try:
                    self.conversation_store.save_message(
                        user_id=user_id,
                        role="system",
                        message=f"IA Analysis: {ai_enrichment.get('enriched_context', '')[:200]}...",
                        conversation_id=conversation_id,
                        metadata={
                            "type": "ai_enrichment",
                            "intent": intent_info.get('intent'),
                            "confidence": intent_info.get('confidence'),
                            "platform": platform
                        }
                    )
                except Exception as e:
                    print(f"⚠️ No se pudo guardar enriquecimiento: {e}")
                    
        except Exception as e:
            print(f"⚠️ Error en enriquecimiento IA: {e}")
            import traceback
            traceback.print_exc()
        
        # Llamar al proceso normal del padre
        response = super().process_message(
            user_id=user_id,
            message_text=message_text,
            platform=platform,
            source=source,
            message_id=message_id
        )
        
        # Registrar interacción para aprendizaje continuo
        if ai_enrichment:
            try:
                # Determinar satisfacción basada en sentimiento
                satisfaction_score = 0.5  # neutral por defecto
                if sentiment_data:
                    if sentiment_data.get('positive', 0) > 0.6:
                        satisfaction_score = 0.8
                    elif sentiment_data.get('negative', 0) > 0.6:
                        satisfaction_score = 0.2
                
                self.ai_integration.log_interaction_result(
                    user_id=user_id,
                    intent=ai_enrichment['intent']['intent'],
                    was_successful=(satisfaction_score > 0.5),
                    satisfaction_score=satisfaction_score,
                    response_generated=bool(response and len(response) > 10)
                )
                print(f"📊 Interacción registrada (satisfacción: {satisfaction_score:.0%})")
            except Exception as e:
                print(f"⚠️ Error registrando interacción: {e}")
        
        return response


def get_instagram_bot():
    """
    Factory function para obtener instancia del bot mejorado.
    Compatible con el código existente.
    """
    return InstagramBotEnhanced()
