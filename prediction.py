"""
Sistema de predicción inteligente
Anticipa necesidades del cliente basado en historial y patrones
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import config

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class PredictionEngine:
    """Motor de predicción de necesidades futuras"""
    
    def __init__(self):
        self.client = None
        if _OPENAI_AVAILABLE and config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def predict_next_need(
        self, 
        user_id: str,
        user_patterns: Dict[str, Any],
        current_message: str,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Predice la próxima necesidad del usuario basado en patrones.
        
        Args:
            user_id: ID del usuario
            user_patterns: Dict con patrones históricos del usuario
            current_message: Mensaje actual del usuario
            conversation_history: Historial conversacional
            
        Returns:
            {
                'predicted_needs': ['reserva próximo fin de semana', 'información de precios'],
                'confidence': float,
                'suggested_actions': ['Ofrecer disponibilidad de fin de semana', 'Enviar catálogo de precios'],
                'proactive_offer': str,
                'best_time_to_offer': str
            }
        """
        
        if not self.client:
            return self._fallback_predict(user_patterns)
        
        try:
            # Construir contexto para GPT
            patterns_summary = self._summarize_patterns(user_patterns)
            
            prompt = f"""Analiza el patrón de comportamiento de este cliente y predice sus próximas necesidades.

DATOS DEL CLIENTE:
{patterns_summary}

MENSAJE ACTUAL: "{current_message}"

Considera:
1. Intenciones históricas más comunes
2. Actividades preferidas
3. Frecuencia de interacción
4. Tiempo del año o del día
5. Nivel de satisfacción anterior

Responde con un JSON (sin markdown):
{{
    "predicted_needs": ["necesidad 1", "necesidad 2"],
    "confidence": 0.85,
    "suggested_actions": ["acción 1 para anticipar", "acción 2"],
    "proactive_offer": "Oferta o sugerencia proactiva para hacer al usuario",
    "best_time_to_offer": "inmediatamente|después de confirmar|mañana|fin de semana",
    "reasoning": "Explicación breve de por qué predices esto"
}}"""
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_completion_tokens=400
            )
            
            import json
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            result['method'] = 'gpt'
            return result
            
        except Exception as e:
            print(f"⚠️ Error en predicción con GPT: {e}")
            return self._fallback_predict(user_patterns)
    
    def predict_churn_risk(
        self,
        user_patterns: Dict[str, Any],
        days_since_last_interaction: int
    ) -> Dict[str, Any]:
        """
        Predice riesgo de pérdida de cliente (churn).
        
        Returns:
            {
                'churn_risk': 'bajo|medio|alto',
                'risk_score': float (0-1),
                'days_inactive': int,
                'retention_suggestion': str,
                're_engagement_message': str
            }
        """
        
        # Heurística simple
        interactions = user_patterns.get('total_interactions', 0)
        last_interaction = user_patterns.get('last_interaction')
        avg_satisfaction = user_patterns.get('avg_satisfaction', 3)
        
        # Calcular riesgo
        risk_score = 0.0
        
        # Factor: inactividad
        if days_since_last_interaction > 30:
            risk_score += 0.4
        elif days_since_last_interaction > 14:
            risk_score += 0.2
        
        # Factor: baja satisfacción
        if avg_satisfaction and avg_satisfaction < 2.5:
            risk_score += 0.3
        elif avg_satisfaction and avg_satisfaction < 3.5:
            risk_score += 0.1
        
        # Factor: poca interacción
        if interactions < 3:
            risk_score += 0.2
        
        # Normalizar
        risk_score = min(risk_score, 1.0)
        
        # Clasificar riesgo
        if risk_score < 0.3:
            churn_risk = "bajo"
        elif risk_score < 0.6:
            churn_risk = "medio"
        else:
            churn_risk = "alto"
        
        # Generar sugerencias
        retention_suggestions = {
            "bajo": "Cliente leal. Mantener experiencia de calidad.",
            "medio": "Enviar oferta personalizada o novedades sobre sus actividades favoritas.",
            "alto": "Alcance proactivo con oferta especial o solicitar feedback sobre experiencia anterior."
        }
        
        re_engagement_messages = {
            "bajo": "Te hemos echado de menos! Tenemos nuevas actividades que te van a encantar.",
            "medio": "Tiempo de volver al Fundo! Te dejamos una sorpresa especial solo para ti.",
            "alto": "¡Te queremos de vuelta! Cuéntanos qué te falta para volver a Fundo Moraga."
        }
        
        return {
            'churn_risk': churn_risk,
            'risk_score': risk_score,
            'days_inactive': days_since_last_interaction,
            'retention_suggestion': retention_suggestions[churn_risk],
            're_engagement_message': re_engagement_messages[churn_risk]
        }
    
    def predict_best_offer_time(self, user_patterns: Dict[str, Any]) -> str:
        """
        Predice el mejor momento para hacer una oferta al cliente.
        """
        preferred_time = user_patterns.get('preferred_time', 'tarde')
        
        time_map = {
            'mañana': '09:00 AM',
            'tarde': '03:00 PM',
            'noche': '08:00 PM'
        }
        
        return time_map.get(preferred_time, '03:00 PM')
    
    def _summarize_patterns(self, patterns: Dict[str, Any]) -> str:
        """Convierte patrones en texto descriptivo"""
        summary = f"""Total de interacciones: {patterns.get('total_interactions', 0)}
Intenciones comunes: {', '.join([intent[0] for intent in patterns.get('common_intents', [])[:3]])}
Actividades preferidas: {', '.join([activity[0] for activity in patterns.get('preferred_activities', [])[:3]])}
Sentimiento típico: {patterns.get('common_sentiment', 'neutral')}
Satisfacción promedio: {patterns.get('avg_satisfaction', 'N/A')} / 5
Hora preferida: {patterns.get('preferred_time', 'tarde')}
Última interacción: {patterns.get('last_interaction', 'Nunca')}
Tasa de conversión: {round((patterns.get('conversion_rate', 0) * 100), 1)}%"""
        return summary
    
    def _fallback_predict(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Predicción basada en reglas si GPT no está disponible"""
        
        intents = patterns.get('common_intents', [])
        activities = patterns.get('preferred_activities', [])
        
        predicted_needs = []
        if 'reserva' in [i[0] for i in intents]:
            predicted_needs.append("Hacer una reserva próximamente")
        if activities:
            predicted_needs.append(f"Más información sobre {activities[0][0]}")
        
        return {
            'predicted_needs': predicted_needs or ["Consulta sobre disponibilidad"],
            'confidence': 0.65,
            'suggested_actions': ["Ofrecer disponibilidad actualizada", "Enviar promoción relevante"],
            'proactive_offer': f"Tenemos disponibilidad especial para {activities[0][0] if activities else 'las actividades que te interesan'}",
            'best_time_to_offer': 'tarde',
            'method': 'fallback'
        }


def get_prediction_engine() -> PredictionEngine:
    """Obtiene instancia singleton del motor de predicción"""
    global _engine
    if '_engine' not in globals():
        _engine = PredictionEngine()
    return _engine
