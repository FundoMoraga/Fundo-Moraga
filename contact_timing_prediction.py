"""
Predicción de mejor tiempo para contactar a cada usuario
Optimiza respuesta y conversión maximizando probabilidad de engagement
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json


class ContactTimingPredictor:
    """Predice ventanas óptimas de contacto por usuario"""
    
    # Patrones de comportamiento predeterminados por tipo de usuario
    DEFAULT_PATTERNS = {
        "trabajador_diurno": {
            "best_hours": [8, 12, 18, 19, 20],
            "best_days": [5, 6],  # Viernes-Sábado
            "avoid_hours": [0, 1, 2, 3, 4, 5],
            "avg_response_time_minutes": 45,
            "engagement_rate": 0.7
        },
        "trabajador_nocturno": {
            "best_hours": [14, 15, 16, 23, 0, 1],
            "best_days": [0, 1, 2, 3],  # Lunes-Jueves
            "avoid_hours": [6, 7, 8, 9, 10],
            "avg_response_time_minutes": 60,
            "engagement_rate": 0.6
        },
        "estudiante": {
            "best_hours": [18, 19, 20, 21, 22],
            "best_days": [5, 6, 0],  # Viernes-Domingo
            "avoid_hours": [8, 9, 10, 11, 12],
            "avg_response_time_minutes": 30,
            "engagement_rate": 0.75
        },
        "jubilado": {
            "best_hours": [10, 11, 15, 16, 17],
            "best_days": [2, 3, 4, 5, 6],  # Miércoles-Sábado
            "avoid_hours": [22, 23, 0, 1],
            "avg_response_time_minutes": 120,
            "engagement_rate": 0.8
        },
        "empresario": {
            "best_hours": [8, 9, 17, 18, 19],
            "best_days": [0, 1, 2, 3, 4],  # Semana
            "avoid_hours": [12, 13, 22, 23],
            "avg_response_time_minutes": 20,
            "engagement_rate": 0.65
        }
    }
    
    def __init__(self):
        """Inicializa predictor de timing"""
        self.user_interaction_history = defaultdict(list)  # user_id -> [interaction_data]
        self.user_patterns = {}  # user_id -> {pattern_data}
    
    def record_interaction(
        self,
        user_id: str,
        message_sent_time: datetime,
        response_time_minutes: float,
        engagement_level: str = "neutral"
    ) -> None:
        """
        Registra interacción para análisis de patrón
        
        Args:
            user_id: ID del usuario
            message_sent_time: Cuándo se envió el mensaje
            response_time_minutes: Minutos para respuesta
            engagement_level: "alto", "neutral", "bajo"
        """
        interaction = {
            "timestamp": message_sent_time.isoformat(),
            "hour": message_sent_time.hour,
            "day_of_week": message_sent_time.weekday(),  # 0=Lunes, 6=Domingo
            "response_time_minutes": response_time_minutes,
            "engagement": engagement_level,
            "responded": response_time_minutes < 1440  # Respondió dentro de 24h
        }
        
        self.user_interaction_history[user_id].append(interaction)
    
    def analyze_user_pattern(self, user_id: str) -> Dict:
        """
        Analiza patrón de comportamiento del usuario
        
        Returns:
            {
                "user_id": str,
                "best_hours": [int],
                "best_days": [int],
                "avg_response_time": float,
                "engagement_rate": float,
                "pattern_confidence": float,
                "recommended_user_type": str
            }
        """
        history = self.user_interaction_history.get(user_id, [])
        
        if len(history) < 3:
            # Asignar patrón por defecto
            default_type = "estudiante"
            pattern = self.DEFAULT_PATTERNS[default_type].copy()
            return {
                "user_id": user_id,
                **pattern,
                "confidence": 0.3,
                "recommended_user_type": default_type,
                "note": "Patrón con datos limitados - mejorará con más interacciones"
            }
        
        # Analizar horas de respuesta rápida
        hour_responses = defaultdict(list)
        day_responses = defaultdict(list)
        engagement_count = {"alto": 0, "neutral": 0, "bajo": 0}
        total_response_time = 0
        responded_count = 0
        
        for interaction in history:
            hour = interaction["hour"]
            day = interaction["day_of_week"]
            response_time = interaction["response_time_minutes"]
            engagement = interaction["engagement"]
            
            hour_responses[hour].append(response_time)
            day_responses[day].append(response_time)
            engagement_count[engagement] += 1
            
            if interaction["responded"]:
                total_response_time += response_time
                responded_count += 1
        
        # Calcular mejores horas (menores tiempos de respuesta)
        best_hours = sorted(
            hour_responses.keys(),
            key=lambda h: sum(hour_responses[h]) / len(hour_responses[h])
        )[:5]  # Top 5 horas
        
        # Calcular mejores días
        best_days = sorted(
            day_responses.keys(),
            key=lambda d: sum(day_responses[d]) / len(day_responses[d])
        )[:4]  # Top 4 días
        
        avg_response_time = total_response_time / responded_count if responded_count > 0 else 60
        engagement_rate = engagement_count["alto"] / len(history)
        pattern_confidence = min(1.0, len(history) / 10)  # Confianza a los 10+ datos
        
        # Clasificar tipo de usuario basado en patrones
        user_type = self._classify_user_type(best_hours, best_days)
        
        return {
            "user_id": user_id,
            "best_hours": sorted(best_hours),
            "best_days": sorted(best_days),
            "avg_response_time_minutes": round(avg_response_time, 1),
            "engagement_rate": round(engagement_rate, 3),
            "pattern_confidence": round(pattern_confidence, 3),
            "recommended_user_type": user_type,
            "interactions_analyzed": len(history),
            "engagement_breakdown": engagement_count
        }
    
    def _classify_user_type(self, best_hours: List[int], best_days: List[int]) -> str:
        """
        Clasifica tipo de usuario basado en su patrón horario
        
        Returns: Uno de los tipos en DEFAULT_PATTERNS
        """
        morning_hours = sum(1 for h in best_hours if 6 <= h < 12)
        afternoon_hours = sum(1 for h in best_hours if 12 <= h < 18)
        evening_hours = sum(1 for h in best_hours if 18 <= h < 23)
        night_hours = sum(1 for h in best_hours if h >= 23 or h < 6)
        
        weekday_days = sum(1 for d in best_days if 0 <= d < 5)
        weekend_days = sum(1 for d in best_days if d >= 5)
        
        # Lógica de clasificación simple
        if evening_hours >= 3 and weekend_days >= 2:
            return "estudiante"
        elif morning_hours >= 3 and weekday_days >= 3:
            return "empresario"
        elif (evening_hours >= 2 or night_hours >= 2) and weekday_days >= 3:
            return "trabajador_nocturno"
        elif afternoon_hours >= 3:
            return "jubilado"
        else:
            return "trabajador_diurno"
    
    def get_next_contact_window(
        self,
        user_id: str,
        hours_ahead: int = 168  # 1 semana
    ) -> Dict:
        """
        Predice próxima ventana óptima para contactar al usuario
        
        Args:
            user_id: ID del usuario
            hours_ahead: Cuántas horas adelante buscar (default 7 días)
        
        Returns:
            {
                "best_time": datetime,
                "confidence": float,
                "best_hours": [int],
                "best_days": [int],
                "avoid_times": [datetime],
                "window_hours": {start: int, end: int},
                "estimated_response_time_minutes": float
            }
        """
        pattern = self.analyze_user_pattern(user_id)
        
        if "note" in pattern:
            # Usuario nuevo, usar patrón default
            pattern = self.DEFAULT_PATTERNS["estudiante"].copy()
            confidence = 0.3
        else:
            confidence = pattern.get("pattern_confidence", 0.5)
        
        best_hours = pattern.get("best_hours", [18, 19, 20, 21, 22])
        best_days = pattern.get("best_days", [5, 6, 0])
        
        # Encontrar próxima ventana óptima
        now = datetime.now()
        check_time = now + timedelta(hours=1)  # Empezar a buscar en 1 hora
        end_time = now + timedelta(hours=hours_ahead)
        
        while check_time < end_time:
            if check_time.hour in best_hours and check_time.weekday() in best_days:
                best_time = check_time
                break
            check_time += timedelta(hours=1)
        else:
            # Si no encontró en óptimos, usar siguiente mejor hora
            best_time = now + timedelta(hours=2)
        
        return {
            "user_id": user_id,
            "best_time": best_time.isoformat(),
            "best_time_readable": best_time.strftime("%A %d/%m a las %H:%M"),
            "confidence": round(confidence, 3),
            "best_hours": best_hours,
            "best_days": best_days,
            "day_names": [self._day_name(d) for d in best_days],
            "estimated_response_time_minutes": pattern.get("avg_response_time_minutes", 60),
            "search_window_hours": hours_ahead,
            "recommendation": f"Contacta a {best_time.strftime('%A %H:%M')} para máxima probabilidad de respuesta"
        }
    
    def _day_name(self, day_num: int) -> str:
        """Convierte número de día (0=Lunes) a nombre"""
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return days[day_num % 7]
    
    def get_bulk_contact_schedule(self, user_ids: List[str]) -> Dict:
        """
        Optimiza orden de contacto para múltiples usuarios
        
        Útil para:
        - Campañas de re-engagement
        - Recordatorios de bookings próximos
        - Promociones especiales
        
        Returns:
            {
                "total_users": int,
                "schedule": [
                    {
                        "user_id": str,
                        "contact_time": datetime,
                        "estimated_response_time": float,
                        "priority": str
                    }
                ],
                "optimal_campaign_start": datetime,
                "expected_response_rate": float
            }
        """
        schedule = []
        total_response_time = 0
        response_count = 0
        
        for user_id in user_ids:
            pattern = self.analyze_user_pattern(user_id)
            window = self.get_next_contact_window(user_id)
            
            best_time = datetime.fromisoformat(window["best_time"])
            response_time = pattern.get("avg_response_time_minutes", 60)
            
            # Priorizar usuarios con mayor probabilidad de respuesta
            priority_score = pattern.get("engagement_rate", 0.5) * pattern.get("pattern_confidence", 0.5)
            priority = "alta" if priority_score > 0.5 else "media" if priority_score > 0.3 else "baja"
            
            schedule.append({
                "user_id": user_id,
                "contact_time": best_time.isoformat(),
                "estimated_response_time_minutes": response_time,
                "priority": priority,
                "priority_score": round(priority_score, 3)
            })
            
            total_response_time += response_time
            response_count += 1
        
        # Ordenar por prioridad y tiempo
        schedule.sort(key=lambda x: (-{"alta": 3, "media": 2, "baja": 1}[x["priority"]], x["contact_time"]))
        
        avg_response_time = total_response_time / response_count if response_count > 0 else 60
        expected_response_rate = sum(
            self.analyze_user_pattern(uid).get("engagement_rate", 0.5)
            for uid in user_ids
        ) / len(user_ids)
        
        return {
            "total_users": len(user_ids),
            "schedule": schedule,
            "optimal_campaign_start": schedule[0]["contact_time"] if schedule else datetime.now().isoformat(),
            "expected_response_rate": round(expected_response_rate, 3),
            "estimated_total_response_time_minutes": round(avg_response_time * len(user_ids), 0),
            "users_by_priority": {
                "alta": len([s for s in schedule if s["priority"] == "alta"]),
                "media": len([s for s in schedule if s["priority"] == "media"]),
                "baja": len([s for s in schedule if s["priority"] == "baja"])
            }
        }
    
    def get_do_not_contact_windows(self, user_id: str) -> List[Dict]:
        """
        Retorna ventanas donde NO contactar al usuario
        
        Basado en:
        - Horas de descanso (noche)
        - Días donde típicamente no responde
        - Información de ocupación si está disponible
        """
        pattern = self.analyze_user_pattern(user_id)
        
        if "note" in pattern:
            # Usuario nuevo
            avoid_hours = [0, 1, 2, 3, 4, 5, 23]
        else:
            # Calcular evitar horas (opuestas a mejores horas)
            all_hours = set(range(24))
            best_hours = set(pattern.get("best_hours", []))
            avoid_hours = sorted(list(all_hours - best_hours))
        
        return {
            "user_id": user_id,
            "avoid_hours": avoid_hours,
            "avoid_hour_names": [f"{h:02d}:00-{h:02d}:59" for h in avoid_hours],
            "reason": "Usuario típicamente no responde en estos horarios"
        }


def get_contact_timing_predictor() -> ContactTimingPredictor:
    """Factory function"""
    global _predictor
    if '_predictor' not in globals():
        _predictor = ContactTimingPredictor()
    return _predictor
