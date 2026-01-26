"""
Integración de módulos de inteligencia avanzada
Conecta clasificador de intenciones, aprendizaje continuo, predicción y recomendaciones
al flujo del bot sin modificar el código existente
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import config
from intent_classifier import get_intent_classifier
from continuous_learning import get_continuous_learning
from prediction import get_prediction_engine
from recommendation import get_recommendation_engine
from entity_extractor import get_entity_extractor


class AdvancedAIIntegration:
    """Integración de todos los módulos de IA avanzada"""
    
    def __init__(self):
        self.intent_classifier = get_intent_classifier()
        self.learning_system = get_continuous_learning()
        self.prediction_engine = get_prediction_engine()
        self.recommendation_engine = get_recommendation_engine()
        self.entity_extractor = get_entity_extractor()
    
    def enrich_user_message(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict] = None,
        sentiment: Optional[str] = None,
        user_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Enriquece el mensaje del usuario con análisis avanzado.
        
        Returns:
            {
                'intent': {'intent': str, 'confidence': float, ...},
                'entities': {'dates': [], 'prices': [], ...},
                'entity_summary': str,
                'user_patterns': {...},
                'predictions': {...},
                'recommendations': {...},
                'enriched_context': str,
                'timestamp': ISO
            }
        """
        
        try:
            # 1. Clasificar intención
            intent_result = self.intent_classifier.classify(
                message,
                conversation_history
            )
            
            # 2. Extraer entidades
            entities = self.entity_extractor.extract_entities(message)
            entity_summary = self.entity_extractor.get_entity_summary(entities)
            
            # 3. Obtener patrones del usuario
            user_patterns = self.learning_system.get_user_patterns(user_id)
            
            # 4. Predicción de necesidades
            predictions = self.prediction_engine.predict_next_need(
                user_id,
                user_patterns,
                message,
                conversation_history
            )
            
            # Calcular días desde última interacción
            last_interaction = user_patterns.get('last_interaction')
            days_since = self._calculate_days_since(last_interaction) if last_interaction else 0
            
            # 5. Predicción de churn
            churn_prediction = self.prediction_engine.predict_churn_risk(
                user_patterns,
                days_since
            )
            
            # 6. Recomendaciones
            recommendations = self.recommendation_engine.recommend(
                user_id,
                user_patterns,
                intent_result.get('intent', 'otro'),
                message
            )
            
            # Construir contexto enriquecido para el bot
            enriched_context = self._build_enriched_context(
                intent_result,
                entity_summary,
                user_patterns,
                predictions,
                recommendations
            )
            
            return {
                'intent': intent_result,
                'entities': entities,
                'entity_summary': entity_summary,
                'user_patterns': user_patterns,
                'predictions': predictions,
                'churn_prediction': churn_prediction,
                'recommendations': recommendations,
                'enriched_context': enriched_context,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️ Error en enriquecimiento: {e}")
            return {
                'intent': {'intent': 'otro', 'confidence': 0.0},
                'entities': {},
                'entity_summary': 'Sin análisis',
                'user_patterns': {},
                'predictions': {},
                'churn_prediction': {},
                'recommendations': {},
                'enriched_context': '',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def log_interaction_result(
        self,
        user_id: str,
        message: str,
        bot_response: str,
        intent: str,
        sentiment: Optional[str],
        response_time_ms: int,
        user_satisfaction: Optional[int] = None,
        user_action: Optional[str] = None,
        enrichment_data: Optional[Dict] = None
    ) -> bool:
        """
        Registra el resultado de la interacción para aprendizaje continuo.
        """
        try:
            interaction_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'intent': intent,
                'sentiment': sentiment or 'neutral',
                'bot_response': bot_response,
                'response_time_ms': response_time_ms,
                'user_satisfaction': user_satisfaction,
                'entities_extracted': enrichment_data.get('entities', {}) if enrichment_data else {},
                'user_action': user_action
            }
            
            return self.learning_system.log_interaction(user_id, interaction_log)
            
        except Exception as e:
            print(f"⚠️ Error registrando interacción: {e}")
            return False
    
    def should_proactively_reach_out(self, user_id: str) -> Dict[str, Any]:
        """
        Determina si debe hacerse un contacto proactivo con el usuario
        (ej: re-engagement, churn recovery)
        
        Returns:
            {
                'should_reach_out': bool,
                'reason': str,
                'message_suggestion': str,
                'best_time': str
            }
        """
        try:
            patterns = self.learning_system.get_user_patterns(user_id)
            
            if not patterns or patterns.get('total_interactions', 0) == 0:
                return {
                    'should_reach_out': False,
                    'reason': 'Nuevo usuario',
                    'message_suggestion': None,
                    'best_time': None
                }
            
            last_interaction = patterns.get('last_interaction')
            days_since = self._calculate_days_since(last_interaction) if last_interaction else 0
            
            churn_risk = self.prediction_engine.predict_churn_risk(patterns, days_since)
            
            # Decidir si hacer alcance
            should_reach = churn_risk['churn_risk'] in ['medio', 'alto']
            
            return {
                'should_reach_out': should_reach,
                'reason': f"Riesgo de churn: {churn_risk['churn_risk']}",
                'message_suggestion': churn_risk.get('re_engagement_message'),
                'best_time': self.prediction_engine.predict_best_offer_time(patterns)
            }
            
        except Exception as e:
            print(f"⚠️ Error evaluando re-engagement: {e}")
            return {
                'should_reach_out': False,
                'reason': 'Error en análisis',
                'message_suggestion': None,
                'best_time': None
            }
    
    def get_system_insights(self) -> Dict[str, Any]:
        """
        Obtiene insights globales del sistema para analytics/dashboard
        
        Returns:
            {
                'trending_intents': [...],
                'system_health': {...},
                'recommendations_for_improvement': [...]
            }
        """
        try:
            trending = self.learning_system.get_trending_intents()
            
            return {
                'trending_intents': trending,
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Use para analytics y dashboards'
            }
            
        except Exception as e:
            print(f"⚠️ Error obteniendo insights: {e}")
            return {}
    
    def _build_enriched_context(
        self,
        intent: Dict[str, Any],
        entity_summary: str,
        patterns: Dict[str, Any],
        predictions: Dict[str, Any],
        recommendations: Dict[str, Any]
    ) -> str:
        """
        Construye un contexto enriquecido para pasar al LLM.
        Este contexto ayuda al bot a generar respuestas más inteligentes.
        """
        context_parts = []
        
        # Intención detectada
        if intent.get('intent') != 'otro':
            context_parts.append(
                f"Usuario intenta: {intent['intent']} (confianza: {intent.get('confidence', 0):.0%})"
            )
        
        # Entidades extraídas
        if entity_summary and entity_summary != "Sin entidades específicas":
            context_parts.append(f"Detalles: {entity_summary}")
        
        # Historial del usuario
        total_ints = patterns.get('total_interactions', 0)
        if total_ints > 0:
            common_intents = [i[0] for i in patterns.get('common_intents', [])[:2]]
            context_parts.append(
                f"Cliente con {total_ints} interacciones previas. Interesado en: {', '.join(common_intents)}"
            )
        
        # Urgencia
        urgency = intent.get('urgency', 'medio')
        if urgency in ['alto', 'bajo']:
            context_parts.append(f"Urgencia: {urgency}")
        
        # Recomendación sugerida
        if recommendations and recommendations.get('primary_recommendation'):
            primary = recommendations['primary_recommendation']
            context_parts.append(
                f"Recomendar: {primary.get('activity')} - {primary.get('personalized_pitch', '')}"
            )
        
        return " | ".join(context_parts) if context_parts else ""
    
    def _calculate_days_since(self, iso_timestamp: Optional[str]) -> int:
        """Calcula días desde un timestamp ISO"""
        if not iso_timestamp:
            return 999  # Muy antiguo
        try:
            last_dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            now = datetime.utcnow().replace(tzinfo=None)
            last_dt_naive = last_dt.replace(tzinfo=None)
            return (now - last_dt_naive).days
        except:
            return 999


def get_advanced_ai_integration() -> AdvancedAIIntegration:
    """Obtiene instancia singleton de integración"""
    global _integration
    if '_integration' not in globals():
        _integration = AdvancedAIIntegration()
    return _integration

