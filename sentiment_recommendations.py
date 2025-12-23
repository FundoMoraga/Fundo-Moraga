"""
Recomendaciones dinámicas basadas en sentimiento del usuario
Ajusta oferta según estado emocional actual
"""
from typing import Dict, List, Optional
from datetime import datetime
import json


class SentimentRecommender:
    """Genera recomendaciones personalizadas según sentimiento"""
    
    # Mapa de sentimientos a tipos de actividades
    SENTIMENT_PROFILES = {
        "positive": {
            "min_score": 0.6,
            "activities": ["off_road", "eventos", "tours_historia"],
            "tone": "entusiasta",
            "offers": [
                "Pack de aventura completo",
                "Descuento por múltiples actividades",
                "Experiencia VIP Fundo Moraga"
            ],
            "urgency": "media"
        },
        "neutral": {
            "min_score": 0.4,
            "activities": ["visita_fundo", "eventos", "produccion"],
            "tone": "informativo",
            "offers": [
                "Tour familiar recomendado",
                "Paquete balanceado",
                "Información sobre disponibilidades"
            ],
            "urgency": "baja"
        },
        "negative": {
            "min_score": 0.0,
            "activities": ["visita_fundo", "produccion"],
            "tone": "comprensivo",
            "offers": [
                "Experiencia relajante",
                "Descuento especial para próxima visita",
                "Consulta con especialista disponible"
            ],
            "urgency": "alta"
        }
    }
    
    # Mapeos de palabras clave a sentimientos
    SENTIMENT_TRIGGERS = {
        "positive": [
            "amo", "adorar", "genial", "perfecto", "increíble", "amor",
            "fantástico", "excelente", "maravilloso", "feliz", "emocionado",
            "entusiasta", "recomiendo", "buena onda", "wow", "yes", "si!"
        ],
        "negative": [
            "odio", "malo", "terrible", "horrible", "frustrado", "enojado",
            "decepcionado", "problema", "difícil", "caro", "no quiero",
            "no puedo", "cancelar", "devolver", "reembolso", "reclamo"
        ]
    }
    
    def __init__(self):
        """Inicializa recomendador de sentimiento"""
        self.recommendation_history = {}
    
    def get_sentiment_profile(self, sentiment_score: float) -> str:
        """
        Determina perfil de sentimiento
        
        Args:
            sentiment_score: Score entre 0 y 1
        
        Returns:
            "positive", "neutral" o "negative"
        """
        if sentiment_score >= 0.6:
            return "positive"
        elif sentiment_score >= 0.4:
            return "neutral"
        else:
            return "negative"
    
    def analyze_sentiment_keywords(self, message: str) -> Dict[str, float]:
        """
        Análisis adicional basado en palabras clave
        
        Returns:
            {"base_score": float, "keyword_boost": float, "final_score": float}
        """
        message_lower = message.lower()
        
        positive_count = sum(
            1 for keyword in self.SENTIMENT_TRIGGERS["positive"]
            if keyword in message_lower
        )
        negative_count = sum(
            1 for keyword in self.SENTIMENT_TRIGGERS["negative"]
            if keyword in message_lower
        )
        
        keyword_sentiment = 0.0
        if positive_count > 0:
            keyword_sentiment = min(0.3, positive_count * 0.1)  # Max boost +0.3
        elif negative_count > 0:
            keyword_sentiment = max(-0.3, -negative_count * 0.1)  # Max down -0.3
        
        return {
            "positive_keywords": positive_count,
            "negative_keywords": negative_count,
            "keyword_boost": keyword_sentiment
        }
    
    def get_recommendations(
        self,
        sentiment_score: float,
        user_id: str,
        previous_activities: List[str] = None,
        budget: Optional[float] = None
    ) -> Dict:
        """
        Genera recomendaciones personalizadas por sentimiento
        
        Args:
            sentiment_score: Score de sentimiento (0-1)
            user_id: ID del usuario
            previous_activities: Actividades anteriores del usuario
            budget: Presupuesto si se conoce
        
        Returns:
            {
                "profile": str,
                "recommended_activities": List[str],
                "special_offers": List[str],
                "tone": str,
                "reason": str,
                "urgency": str
            }
        """
        profile = self.get_sentiment_profile(sentiment_score)
        profile_data = self.SENTIMENT_PROFILES[profile]
        
        previous_activities = previous_activities or []
        
        # Recomendaciones diversas (evitar repetidas)
        recommended = [
            a for a in profile_data["activities"]
            if a not in previous_activities
        ]
        
        # Si todas fueron recomendadas antes, reiniciar
        if not recommended:
            recommended = profile_data["activities"][:2]
        
        # Filtrar por presupuesto si se conoce
        activities_by_price = self._filter_by_budget(recommended, budget)
        if activities_by_price:
            recommended = activities_by_price
        
        reason = self._get_recommendation_reason(profile, sentiment_score)
        
        result = {
            "sentiment_profile": profile,
            "sentiment_score": round(sentiment_score, 3),
            "recommended_activities": recommended,
            "special_offers": profile_data["offers"],
            "tone": profile_data["tone"],
            "reason": reason,
            "urgency": profile_data["urgency"],
            "confidence": min(1.0, abs(sentiment_score - 0.5) * 2),  # Mayor confianza en extremos
            "generated_at": datetime.now().isoformat()
        }
        
        # Guardar en historial
        if user_id not in self.recommendation_history:
            self.recommendation_history[user_id] = []
        
        self.recommendation_history[user_id].append(result)
        
        return result
    
    def _filter_by_budget(
        self,
        activities: List[str],
        budget: Optional[float]
    ) -> List[str]:
        """Filtra actividades por presupuesto"""
        if not budget:
            return activities
        
        activity_prices = {
            "off_road": 15000,  # Weekday
            "eventos": 200000,
            "produccion": 200000,
            "visita_fundo": 5000,  # Puede ser menor
            "tours_historia": 8000
        }
        
        return [
            a for a in activities
            if activity_prices.get(a, 0) <= budget
        ]
    
    def _get_recommendation_reason(self, profile: str, score: float) -> str:
        """Genera explicación de recomendación"""
        if profile == "positive":
            return f"Tu entusiasmo ({score:.0%}) sugiere aventuras emocionantes"
        elif profile == "neutral":
            return f"Vamos con opciones equilibradas para explorar"
        else:
            return f"Vamos con algo relajante para disfrutar"
    
    def get_contextual_offer(
        self,
        sentiment_score: float,
        activity: str,
        date: Optional[str] = None
    ) -> Dict:
        """
        Genera oferta especial contextualizada
        
        Args:
            sentiment_score: Score emocional actual
            activity: Actividad siendo consultada
            date: Fecha si se conoce
        
        Returns:
            {
                "offer": str,
                "discount_percent": int,
                "urgency_message": str,
                "expires_in_hours": int
            }
        """
        profile = self.get_sentiment_profile(sentiment_score)
        
        # Ofertas más agresivas con sentimiento negativo
        discount_base = {
            "positive": 10,      # 10% descuento
            "neutral": 15,       # 15% descuento
            "negative": 25       # 25% descuento
        }
        
        discount = discount_base.get(profile, 15)
        
        urgency_messages = {
            "positive": "¡Completa tu aventura ahora!",
            "neutral": "Disponibilidad limitada",
            "negative": "Te tenemos un especial 💙"
        }
        
        base_price = {
            "off_road": 15000,
            "eventos": 200000,
            "produccion": 200000,
            "visita_fundo": 5000,
            "tours_historia": 8000
        }
        
        price = base_price.get(activity, 15000)
        discounted = int(price * (1 - discount/100))
        
        return {
            "activity": activity,
            "original_price": price,
            "discounted_price": discounted,
            "discount_percent": discount,
            "urgency_message": urgency_messages[profile],
            "expires_in_hours": 24 if profile == "negative" else 72,
            "sentiment_based": True,
            "reason": f"Promoción especial para ti (sentimiento: {profile})"
        }
    
    def get_upsell_suggestion(
        self,
        current_activity: str,
        sentiment_score: float,
        user_history: List[str] = None
    ) -> Dict:
        """
        Sugiere actividad complementaria para aumentar valor
        
        Ejemplos:
        - Si bookean "off_road" → Sugerir "tours_historia" después
        - Si bookean "eventos" → Sugerir "produccion" tour
        """
        user_history = user_history or []
        
        upsell_matrix = {
            "off_road": {
                "next": "tours_historia",
                "pitch": "Después de la adrenalina, conoce la historia de Batuco"
            },
            "eventos": {
                "next": "produccion",
                "pitch": "Completa con nuestro tour de producción ecológica"
            },
            "visita_fundo": {
                "next": "tours_historia",
                "pitch": "Profundiza con el tour histórico completo"
            },
            "tours_historia": {
                "next": "off_road",
                "pitch": "Vive la adrenalina de nuestras actividades"
            },
            "produccion": {
                "next": "visita_fundo",
                "pitch": "Conoce el resto de nuestras instalaciones"
            }
        }
        
        upsell = upsell_matrix.get(current_activity, {})
        
        if not upsell or upsell.get("next") in user_history:
            return None
        
        # Más agresivo con sentimiento positivo
        intensity = "alta" if sentiment_score >= 0.6 else "media"
        
        return {
            "current_activity": current_activity,
            "suggested_activity": upsell.get("next"),
            "pitch": upsell.get("pitch"),
            "intensity": intensity,
            "show_now": sentiment_score >= 0.65,
            "show_later": True
        }
    
    def get_sentiment_trend(self, user_id: str) -> Dict:
        """
        Analiza tendencia de sentimiento del usuario a lo largo del tiempo
        
        Returns:
            {
                "trend": "mejorando" | "empeorando" | "estable",
                "recent_average": float,
                "change": float,
                "recommendation": str
            }
        """
        if user_id not in self.recommendation_history or len(self.recommendation_history[user_id]) < 2:
            return {"trend": "nuevo_usuario", "samples": len(self.recommendation_history.get(user_id, []))}
        
        history = self.recommendation_history[user_id]
        recent = [h.get("sentiment_score", 0.5) for h in history[-5:]]  # Últimos 5
        
        if len(recent) < 2:
            return {"trend": "insuficientes_datos"}
        
        avg_recent = sum(recent) / len(recent)
        avg_earlier = sum(recent[:-1]) / len(recent[:-1]) if len(recent) > 1 else avg_recent
        
        change = avg_recent - avg_earlier
        
        if change > 0.1:
            trend = "mejorando"
            recommendation = "Usuario muestra sentimientos más positivos - ofrece experiencias premium"
        elif change < -0.1:
            trend = "empeorando"
            recommendation = "Usuario ha mostrado sentimientos más negativos - ofrece soporte personalizado"
        else:
            trend = "estable"
            recommendation = "Usuario mantiene sentimientos consistentes"
        
        return {
            "trend": trend,
            "recent_average": round(avg_recent, 3),
            "earlier_average": round(avg_earlier, 3),
            "change": round(change, 3),
            "samples": len(recent),
            "recommendation": recommendation
        }


def get_sentiment_recommender() -> SentimentRecommender:
    """Factory function"""
    global _recommender
    if '_recommender' not in globals():
        _recommender = SentimentRecommender()
    return _recommender
