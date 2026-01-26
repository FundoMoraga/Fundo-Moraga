"""
Sistema de aprendizaje continuo
Registra patrones de interacción y ajusta respuestas futuras basado en análisis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from cosmos_client import get_memory_store
import json
import config


class ContinuousLearning:
    """Gestiona el aprendizaje continuo del bot"""
    
    def __init__(self):
        self.memory_store = get_memory_store()
    
    def log_interaction(self, user_id: str, interaction: Dict[str, Any]) -> bool:
        """
        Registra una interacción para análisis posterior.
        
        Args:
            user_id: ID del usuario
            interaction: {
                'timestamp': ISO timestamp,
                'message': str,
                'intent': str,
                'sentiment': str,
                'bot_response': str,
                'response_time_ms': int,
                'user_satisfaction': int (0-5, si aplica),
                'entities_extracted': dict,
                'user_action': str (clicked, reserved, etc.)
            }
        """
        try:
            # Crear documento de patrón para Cosmos
            pattern_id = f"interaction#{user_id}#{datetime.utcnow().isoformat()}"
            
            doc = {
                "id": pattern_id,
                "Categoria": "InteractionLog",
                "type": "user_interaction",
                "user_id": user_id,
                "timestamp": interaction.get('timestamp', datetime.utcnow().isoformat()),
                "message": interaction.get('message', ''),
                "intent": interaction.get('intent', ''),
                "sentiment": interaction.get('sentiment', ''),
                "bot_response": interaction.get('bot_response', ''),
                "response_time_ms": interaction.get('response_time_ms', 0),
                "user_satisfaction": interaction.get('user_satisfaction'),
                "entities_extracted": interaction.get('entities_extracted', {}),
                "user_action": interaction.get('user_action'),
                "ttl": 7776000  # 90 días
            }
            
            self.memory_store.upsert_item(doc)
            return True
        except Exception as e:
            print(f"⚠️ Error registrando interacción: {e}")
            return False
    
    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Analiza los patrones de un usuario específico.
        
        Returns:
            {
                'total_interactions': int,
                'common_intents': [('reserva', 5), ('consulta', 3)],
                'avg_satisfaction': float,
                'preferred_activities': [('off-road', 3)],
                'common_sentiment': str,
                'typical_time_of_day': str,
                'last_interaction': str,
                'conversion_rate': float
            }
        """
        try:
            query = f"""
            SELECT * FROM c
            WHERE c.Categoria = 'InteractionLog' AND c.user_id = '{user_id}'
            ORDER BY c.timestamp DESC
            """
            
            items = list(self.memory_store.query_items(query, limit=100))
            
            if not items:
                return {
                    'total_interactions': 0,
                    'common_intents': [],
                    'avg_satisfaction': None,
                    'preferred_activities': [],
                    'common_sentiment': None,
                    'last_interaction': None
                }
            
            # Calcular estadísticas
            intents = {}
            sentiments = {}
            satisfaction_scores = []
            activities = {}
            hours = {}
            actions_taken = 0
            
            for item in items:
                # Contabilizar intenciones
                intent = item.get('intent', 'otro')
                intents[intent] = intents.get(intent, 0) + 1
                
                # Contabilizar sentimientos
                sentiment = item.get('sentiment', 'neutral')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
                
                # Satisfacción
                if item.get('user_satisfaction') is not None:
                    satisfaction_scores.append(item['user_satisfaction'])
                
                # Actividades mencionadas (simplificado)
                for entity in item.get('entities_extracted', {}).get('activities', []):
                    activities[entity] = activities.get(entity, 0) + 1
                
                # Hora del día
                try:
                    ts = datetime.fromisoformat(item.get('timestamp', ''))
                    hour = ts.hour
                    period = 'mañana' if 6 <= hour < 12 else 'tarde' if 12 <= hour < 18 else 'noche'
                    hours[period] = hours.get(period, 0) + 1
                except:
                    pass
                
                # Acciones completadas
                if item.get('user_action'):
                    actions_taken += 1
            
            # Determinar sentimiento más común
            most_common_sentiment = max(sentiments, key=sentiments.get) if sentiments else 'neutral'
            
            return {
                'total_interactions': len(items),
                'common_intents': sorted(intents.items(), key=lambda x: x[1], reverse=True),
                'avg_satisfaction': sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None,
                'preferred_activities': sorted(activities.items(), key=lambda x: x[1], reverse=True),
                'common_sentiment': most_common_sentiment,
                'preferred_time': max(hours, key=hours.get) if hours else None,
                'last_interaction': items[0].get('timestamp') if items else None,
                'conversion_rate': actions_taken / len(items) if items else 0
            }
            
        except Exception as e:
            print(f"⚠️ Error analizando patrones: {e}")
            return {}
    
    def get_trending_intents(self) -> List[tuple]:
        """
        Obtiene intenciones más comunes globales (últimos 7 días)
        Útil para identificar tendencias
        
        Returns:
            [('reserva', 25), ('consulta', 18), ...]
        """
        try:
            from datetime import timedelta
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            query = f"""
            SELECT c.intent, COUNT(1) as count FROM c
            WHERE c.Categoria = 'InteractionLog' AND c.timestamp > '{week_ago}'
            GROUP BY c.intent
            ORDER BY count DESC
            """
            
            results = list(self.memory_store.query_items(query))
            return [(r['intent'], r['count']) for r in results]
        except Exception as e:
            print(f"⚠️ Error obteniendo intenciones trending: {e}")
            return []
    
    def should_improve_response(self, intent: str, avg_satisfaction: Optional[float]) -> bool:
        """
        Determina si una respuesta tipo debe mejorarse basado en satisfacción
        """
        if avg_satisfaction is None:
            return False
        return avg_satisfaction < 3.0  # Menos de 3/5 estrellas
    
    def get_improvement_suggestions(self, user_id: str) -> List[str]:
        """
        Genera sugerencias de mejora basadas en patrones
        """
        patterns = self.get_user_patterns(user_id)
        suggestions = []
        
        if patterns.get('avg_satisfaction', 5) and patterns['avg_satisfaction'] < 3:
            suggestions.append("Necesita respuestas más personalizadas")
        
        if patterns.get('conversion_rate', 0) < 0.3:
            suggestions.append("Bajo engagement - revisar claridad de respuestas")
        
        if patterns.get('common_sentiment') == 'negative':
            suggestions.append("Usuarios frecuentemente negativos - revisar tono")
        
        return suggestions


def get_continuous_learning() -> ContinuousLearning:
    """Obtiene instancia singleton de aprendizaje continuo"""
    global _learning
    if '_learning' not in globals():
        _learning = ContinuousLearning()
    return _learning

