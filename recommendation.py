"""
Sistema de recomendaciones personalizadas
Sugiere actividades y ofertas basadas en perfil y preferencias del usuario
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import config

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class RecommendationEngine:
    """Motor de recomendaciones personalizadas"""
    
    # Catálogo de actividades disponibles en Fundo Moraga
    ACTIVITIES_CATALOG = {
        "off_road": {
            "name": "Actividades Off-Road",
            "description": "Ruteo con autos y motos en terreno",
            "price_range": "$15000 - $50000",
            "best_season": "todo el año",
            "duration": "2-4 horas",
            "group_size": "2-20 personas",
            "intensity": "media-alta"
        },
        "eventos": {
            "name": "Eventos Corporativos",
            "description": "Reuniones, retiros, conferencias",
            "price_range": "$200000+",
            "best_season": "todo el año",
            "duration": "4-8 horas",
            "group_size": "10-500 personas",
            "intensity": "variable"
        },
        "produccion": {
            "name": "Locación para Producciones",
            "description": "Cine, fotografía, publicidad",
            "price_range": "negociable",
            "best_season": "primavera-verano",
            "duration": "variable",
            "group_size": "variable",
            "intensity": "flexible"
        },
        "visita_fundo": {
            "name": "Visitas al Fundo",
            "description": "Turismo y recorridos familiares",
            "price_range": "$5000 - $15000",
            "best_season": "primavera-verano",
            "duration": "2-3 horas",
            "group_size": "1-20 personas",
            "intensity": "baja"
        },
        "tours_historia": {
            "name": "Tours Históricos",
            "description": "Recorridos con narrativa histórica de Fundo Moraga",
            "price_range": "$8000 - $20000",
            "best_season": "todo el año",
            "duration": "2-4 horas",
            "group_size": "4-30 personas",
            "intensity": "baja"
        }
    }
    
    def __init__(self):
        self.client = None
        if _OPENAI_AVAILABLE and config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def recommend(
        self,
        user_id: str,
        user_patterns: Dict[str, Any],
        current_intent: str,
        current_message: str
    ) -> Dict[str, Any]:
        """
        Genera recomendaciones personalizadas para el usuario.
        
        Args:
            user_id: ID del usuario
            user_patterns: Patrones históricos del usuario
            current_intent: Intención detectada del mensaje
            current_message: Mensaje actual del usuario
            
        Returns:
            {
                'primary_recommendation': {
                    'activity': str,
                    'reason': str,
                    'personalized_pitch': str
                },
                'secondary_recommendations': [
                    {'activity': str, 'reason': str}
                ],
                'special_offer': str,
                'urgency': str,
                'call_to_action': str
            }
        """
        
        if not self.client:
            return self._fallback_recommend(user_patterns, current_intent)
        
        try:
            # Construir contexto de usuario
            user_context = self._build_user_context(user_patterns)
            activities_str = self._format_activities()
            
            prompt = f"""Eres un experto en recomendar experiencias en Fundo Moraga.
Basado en el perfil del cliente, sugiere las actividades más apropiadas.

PERFIL DEL CLIENTE:
{user_context}

INTENCIÓN ACTUAL: {current_intent}
MENSAJE: "{current_message}"

CATÁLOGO DISPONIBLE:
{activities_str}

Responde con JSON (sin markdown):
{{
    "primary_recommendation": {{
        "activity": "nombre de la actividad",
        "reason": "por qué esta es la mejor opción para este cliente",
        "personalized_pitch": "propuesta personalizada y atractiva (máx 2 líneas)"
    }},
    "secondary_recommendations": [
        {{"activity": "nombre", "reason": "por qué"}},
        {{"activity": "nombre", "reason": "por qué"}}
    ],
    "special_offer": "Oferta especial basada en historial (ej: '10% descuento en tu próxima reserva')",
    "best_timing": "ahora|este fin de semana|próxima semana",
    "call_to_action": "Frase motivadora para que reserve/consulte"
}}"""
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500
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
            print(f"⚠️ Error en recomendaciones con GPT: {e}")
            return self._fallback_recommend(user_patterns, current_intent)
    
    def get_seasonal_recommendations(self, user_patterns: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Recomendaciones basadas en la época del año.
        """
        current_month = datetime.now().month
        
        # Determinar temporada
        if current_month in [12, 1, 2]:
            season = "verano"
        elif current_month in [3, 4, 5]:
            season = "otoño"
        elif current_month in [6, 7, 8]:
            season = "invierno"
        else:
            season = "primavera"
        
        recommendations = []
        for activity_key, activity in self.ACTIVITIES_CATALOG.items():
            if season in activity['best_season'] or activity['best_season'] == 'todo el año':
                recommendations.append({
                    'activity': activity['name'],
                    'seasonal_reason': f"Perfecta para {season}: {activity['description']}",
                    'best_time': activity['best_season']
                })
        
        return recommendations
    
    def get_group_recommendations(
        self,
        estimated_group_size: Optional[int],
        user_patterns: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Recomendaciones basadas en tamaño de grupo.
        """
        if not estimated_group_size:
            return []
        
        recommendations = []
        for activity_key, activity in self.ACTIVITIES_CATALOG.items():
            min_size, max_size = self._parse_group_size(activity['group_size'])
            if min_size <= estimated_group_size <= max_size:
                recommendations.append({
                    'activity': activity['name'],
                    'group_fit': f"Perfecta para grupos de {activity['group_size']}",
                    'capacity': activity['group_size']
                })
        
        return recommendations
    
    def get_price_range_recommendations(
        self,
        max_budget: Optional[float],
        user_patterns: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Recomendaciones basadas en presupuesto del cliente.
        """
        if not max_budget:
            return []
        
        recommendations = []
        for activity_key, activity in self.ACTIVITIES_CATALOG.items():
            if self._fits_budget(activity['price_range'], max_budget):
                recommendations.append({
                    'activity': activity['name'],
                    'price': activity['price_range'],
                    'budget_fit': 'Dentro de presupuesto'
                })
        
        return recommendations
    
    def _build_user_context(self, patterns: Dict[str, Any]) -> str:
        """Convierte patrones en descripción textual"""
        intents = [i[0] for i in patterns.get('common_intents', [])[:3]]
        activities = [a[0] for a in patterns.get('preferred_activities', [])[:3]]
        
        context = f"""Número de interacciones: {patterns.get('total_interactions', 0)}
Interesado en: {', '.join(intents) if intents else 'exploración general'}
Actividades previas: {', '.join(activities) if activities else 'sin historial'}
Sentimiento general: {patterns.get('common_sentiment', 'positivo')}
Satisfacción: {patterns.get('avg_satisfaction', 'N/A')} / 5
Tasa de conversión: {round((patterns.get('conversion_rate', 0) * 100), 1)}%"""
        return context
    
    def _format_activities(self) -> str:
        """Formatea catálogo de actividades"""
        text = ""
        for key, activity in self.ACTIVITIES_CATALOG.items():
            text += f"\n{activity['name']}:\n"
            text += f"  - {activity['description']}\n"
            text += f"  - Precio: {activity['price_range']}\n"
            text += f"  - Duración: {activity['duration']}\n"
        return text
    
    def _parse_group_size(self, size_str: str) -> tuple:
        """Parsea string de tamaño de grupo"""
        try:
            parts = size_str.split('-')
            return (int(parts[0].strip()), int(parts[1].strip()))
        except:
            return (1, 500)
    
    def _fits_budget(self, price_range: str, budget: float) -> bool:
        """Verifica si precio encaja en presupuesto"""
        try:
            if "negociable" in price_range.lower():
                return True
            min_price = int(price_range.split('-')[0].replace('$', '').replace('.', ''))
            return min_price <= budget
        except:
            return True
    
    def _fallback_recommend(
        self,
        patterns: Dict[str, Any],
        intent: str
    ) -> Dict[str, Any]:
        """Recomendación basada en reglas si GPT no disponible"""
        
        intents = patterns.get('common_intents', [])
        activities = patterns.get('preferred_activities', [])
        
        # Mapeo intención → actividad
        intent_activity_map = {
            'reserva': 'off_road',
            'consulta': 'visita_fundo',
            'evento': 'eventos',
            'produccion': 'produccion',
            'tours': 'tours_historia'
        }
        
        recommended_key = intent_activity_map.get(intent, 'visita_fundo')
        recommended = self.ACTIVITIES_CATALOG[recommended_key]
        
        return {
            'primary_recommendation': {
                'activity': recommended['name'],
                'reason': 'Basada en tu historial de interés',
                'personalized_pitch': f"Te recomendamos {recommended['name'].lower()}. {recommended['description']}"
            },
            'secondary_recommendations': [
                {
                    'activity': self.ACTIVITIES_CATALOG['tours_historia']['name'],
                    'reason': 'Complementa la experiencia'
                },
                {
                    'activity': self.ACTIVITIES_CATALOG['visita_fundo']['name'],
                    'reason': 'Perfecta para conocer el lugar'
                }
            ],
            'special_offer': 'Consulta por ofertas especiales de temporada',
            'best_timing': 'próxima semana',
            'call_to_action': '¿Te interesa conocer más detalles?',
            'method': 'fallback'
        }


def get_recommendation_engine() -> RecommendationEngine:
    """Obtiene instancia singleton del motor de recomendaciones"""
    global _recommender
    if '_recommender' not in globals():
        _recommender = RecommendationEngine()
    return _recommender
