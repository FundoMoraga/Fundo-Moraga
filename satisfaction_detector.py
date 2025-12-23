"""
Detección temprana de insatisfacción del usuario
Sistema de alerta para prevenir pérdida de clientes
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class SatisfactionDetector:
    """
    Detecta señales de insatisfacción temprana
    Dispara alertas antes de que el cliente se vaya
    """
    
    # Palabras clave de frustración/insatisfacción
    FRUSTRATION_KEYWORDS = {
        "crítico": [
            "cancel", "devolver", "dinero", "reembolso", "estafa",
            "fraude", "engaño", "no vale", "basura", "porquería",
            "perdí", "arruinó", "nunca más", "horrib", "terrib",
            "pedir ayuda", "quejo", "reclamo", "abogado", "demanda"
        ],
        "alto": [
            "odio", "malo", "problema", "difícil", "caro", "decepción",
            "frustración", "enojado", "disgustado", "arrepentido",
            "no quiero", "no puedo", "no funciona", "falla",
            "pésimo", "medíocre", "desastroso"
        ],
        "medio": [
            "eh", "meh", "medio", "así", "bueno", "ok", "podría ser mejor",
            "esperaba más", "deslusionado", "no me gustó", "menos de lo esperado",
            "complicado", "confundido", "dudoso"
        ]
    }
    
    # Patrones de comportamiento que indican insatisfacción
    BEHAVIOR_PATTERNS = {
        "aumento_preguntas": {
            "threshold": 5,  # 5+ preguntas sin booking
            "meaning": "Usuario confundido o desconfiado"
        },
        "respuesta_lenta": {
            "threshold_hours": 48,
            "meaning": "Usuario perdiendo interés"
        },
        "cambios_frecuentes": {
            "threshold": 3,  # Cambiar booking 3+ veces
            "meaning": "Usuario inseguro o insatisfecho con opciones"
        },
        "consulta_competencia": {
            "keywords": ["otro", "alternativa", "donde más", "comparar"],
            "meaning": "Usuario evaluando opciones"
        },
        "solicitud_especial_rechazada": {
            "meaning": "Usuario no obtuvo lo que pedía"
        }
    }
    
    def __init__(self):
        """Inicializa detector de satisfacción"""
        self.user_satisfaction_scores = {}  # user_id -> score (0-1)
        self.user_alerts = defaultdict(list)  # user_id -> [alerts]
        self.user_interaction_patterns = defaultdict(list)  # user_id -> [interactions]
        self.critical_flags = defaultdict(list)  # user_id -> [flags]
    
    def analyze_message_satisfaction(self, message: str) -> Dict:
        """
        Analiza un mensaje para detectar insatisfacción
        
        Returns:
            {
                "satisfaction_level": "satisfecho" | "neutral" | "insatisfecho" | "crítico",
                "frustration_score": float (0-1),
                "keywords_found": [str],
                "severity": str,
                "recommendation": str
            }
        """
        message_lower = message.lower()
        
        # Contador de palabras por severidad
        critical_count = sum(
            1 for kw in self.FRUSTRATION_KEYWORDS.get("crítico", [])
            if kw in message_lower
        )
        high_count = sum(
            1 for kw in self.FRUSTRATION_KEYWORDS.get("alto", [])
            if kw in message_lower
        )
        medium_count = sum(
            1 for kw in self.FRUSTRATION_KEYWORDS.get("medio", [])
            if kw in message_lower
        )
        
        # Calcular score
        frustration_score = min(
            1.0,
            (critical_count * 0.5 + high_count * 0.3 + medium_count * 0.1) / 5
        )
        
        # Palabras encontradas
        keywords_found = []
        for severity in ["crítico", "alto", "medio"]:
            found = [
                kw for kw in self.FRUSTRATION_KEYWORDS.get(severity, [])
                if kw in message_lower
            ]
            keywords_found.extend(found)
        
        # Clasificar nivel de satisfacción
        if critical_count > 0:
            level = "crítico"
            severity = "CRÍTICO"
        elif frustration_score > 0.6:
            level = "insatisfecho"
            severity = "ALTO"
        elif frustration_score > 0.3:
            level = "neutral"
            severity = "MEDIO"
        else:
            level = "satisfecho"
            severity = "BAJO"
        
        # Recomendación
        recommendations = {
            "crítico": "⚠️ ESCALACIÓN INMEDIATA - Contactar gerente/especialista ahora",
            "insatisfecho": "🔴 Intervención rápida requerida - Ofrecer solución personalizada",
            "neutral": "🟡 Monitorear - Seguir patrón, estar atento a más señales",
            "satisfecho": "✅ Cliente satisfecho - Mantener calidad actual"
        }
        
        return {
            "satisfaction_level": level,
            "frustration_score": round(frustration_score, 3),
            "keywords_found": list(set(keywords_found)),
            "critical_keywords": critical_count,
            "high_keywords": high_count,
            "severity": severity,
            "recommendation": recommendations[level],
            "requires_escalation": level in ["crítico", "insatisfecho"]
        }
    
    def track_user_satisfaction(
        self,
        user_id: str,
        message: str,
        response: str,
        booking_completed: bool = False
    ) -> Dict:
        """
        Registra interacción y actualiza score de satisfacción del usuario
        
        Returns: Estado actualizado del usuario
        """
        analysis = self.analyze_message_satisfaction(message)
        
        # Obtener score actual (default 0.7 = neutral)
        current_score = self.user_satisfaction_scores.get(user_id, 0.7)
        
        # Ajustar score basado en análisis
        if analysis["satisfaction_level"] == "crítico":
            delta = -0.3
        elif analysis["satisfaction_level"] == "insatisfecho":
            delta = -0.15
        elif analysis["satisfaction_level"] == "satisfecho":
            delta = 0.1
        else:  # neutral
            delta = 0
        
        # Bonus si completa booking
        if booking_completed:
            delta += 0.2
        
        new_score = max(0, min(1, current_score + delta))
        self.user_satisfaction_scores[user_id] = new_score
        
        # Registrar interacción
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "message": message[:100],  # Primeros 100 caracteres
            "satisfaction_level": analysis["satisfaction_level"],
            "frustration_score": analysis["frustration_score"],
            "booking_completed": booking_completed,
            "score_before": current_score,
            "score_after": new_score,
            "delta": delta
        }
        
        self.user_interaction_patterns[user_id].append(interaction)
        
        # Generar alerta si es necesario
        if analysis["satisfaction_level"] in ["crítico", "insatisfecho"]:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "type": "SATISFACCIÓN",
                "level": analysis["severity"],
                "keywords": analysis["keywords_found"],
                "message_snippet": message[:50] + "..." if len(message) > 50 else message,
                "recommendation": analysis["recommendation"],
                "action_required": analysis["requires_escalation"]
            }
            self.user_alerts[user_id].append(alert)
        
        return {
            "user_id": user_id,
            "satisfaction_score": round(new_score, 3),
            "level": self._score_to_level(new_score),
            "trend": self._calculate_trend(user_id),
            "last_analysis": analysis,
            "active_alerts": len(self.user_alerts.get(user_id, [])),
            "critical_flags": len(self.critical_flags.get(user_id, []))
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convierte score a nivel legible"""
        if score >= 0.8:
            return "Muy Satisfecho"
        elif score >= 0.6:
            return "Satisfecho"
        elif score >= 0.4:
            return "Neutral"
        elif score >= 0.2:
            return "Insatisfecho"
        else:
            return "Muy Insatisfecho (RIESGO)"
    
    def _calculate_trend(self, user_id: str) -> str:
        """Calcula tendencia de satisfacción"""
        if user_id not in self.user_interaction_patterns:
            return "nuevo_usuario"
        
        interactions = self.user_interaction_patterns[user_id]
        if len(interactions) < 2:
            return "insuficientes_datos"
        
        recent = [i.get("score_after", 0.5) for i in interactions[-5:]]
        early = [i.get("score_after", 0.5) for i in interactions[:2]]
        
        avg_recent = sum(recent) / len(recent)
        avg_early = sum(early) / len(early)
        
        change = avg_recent - avg_early
        
        if change > 0.1:
            return "mejorando"
        elif change < -0.1:
            return "deteriorándose"
        else:
            return "estable"
    
    def detect_behavior_anomalies(self, user_id: str) -> List[Dict]:
        """
        Detecta patrones de comportamiento anómalos que indican insatisfacción
        
        Returns lista de anomalías detectadas
        """
        anomalies = []
        interactions = self.user_interaction_patterns.get(user_id, [])
        
        if not interactions:
            return anomalies
        
        # 1. Demasiadas preguntas sin booking
        question_count = sum(
            1 for i in interactions[-10:]
            if "?" in i.get("message", "")
        )
        if question_count >= self.BEHAVIOR_PATTERNS["aumento_preguntas"]["threshold"]:
            anomalies.append({
                "type": "aumento_preguntas",
                "severity": "MEDIO",
                "message": f"Usuario ha hecho {question_count} preguntas en últimas 10 interacciones sin booking",
                "meaning": self.BEHAVIOR_PATTERNS["aumento_preguntas"]["meaning"],
                "action": "Ofrecer consulta personalizada con especialista"
            })
        
        # 2. Tiempo entre respuestas aumentando
        if len(interactions) >= 2:
            last_times = [
                datetime.fromisoformat(i["timestamp"])
                for i in interactions[-3:]
            ]
            if len(last_times) >= 2:
                time_delta = (datetime.now() - last_times[-1]).total_seconds() / 3600
                if time_delta > self.BEHAVIOR_PATTERNS["respuesta_lenta"]["threshold_hours"]:
                    anomalies.append({
                        "type": "respuesta_lenta",
                        "severity": "MEDIO",
                        "message": f"Usuario sin respuesta hace {int(time_delta)} horas",
                        "meaning": self.BEHAVIOR_PATTERNS["respuesta_lenta"]["meaning"],
                        "action": "Enviar mensaje de seguimiento atractivo"
                    })
        
        # 3. Múltiples cambios en booking
        change_count = sum(
            1 for i in interactions[-20:]
            if "cambiar" in i.get("message", "").lower() or "otra" in i.get("message", "").lower()
        )
        if change_count >= self.BEHAVIOR_PATTERNS["cambios_frecuentes"]["threshold"]:
            anomalies.append({
                "type": "cambios_frecuentes",
                "severity": "ALTO",
                "message": f"Usuario ha solicitado cambios {change_count} veces",
                "meaning": self.BEHAVIOR_PATTERNS["cambios_frecuentes"]["meaning"],
                "action": "Ofrecer opciones limitadas pero atractivas para cerrar venta"
            })
        
        # 4. Buscando alternativas
        search_keywords = self.BEHAVIOR_PATTERNS["consulta_competencia"]["keywords"]
        search_count = sum(
            1 for i in interactions[-10:]
            if any(kw in i.get("message", "").lower() for kw in search_keywords)
        )
        if search_count > 0:
            anomalies.append({
                "type": "evalua_alternativas",
                "severity": "ALTO",
                "message": "Usuario evaluando opciones competidoras",
                "meaning": self.BEHAVIOR_PATTERNS["consulta_competencia"]["meaning"],
                "action": "Resaltar ventajas únicas de Fundo Moraga, ofrecer promoción especial"
            })
        
        return anomalies
    
    def get_user_risk_assessment(self, user_id: str) -> Dict:
        """
        Evaluación integral de riesgo de pérdida del cliente
        
        Returns:
            {
                "risk_level": "bajo" | "medio" | "alto" | "crítico",
                "churn_probability": float (0-1),
                "satisfaction_score": float,
                "trend": str,
                "anomalies": [Dict],
                "alerts": [Dict],
                "urgent_actions": [str]
            }
        """
        satisfaction = self.user_satisfaction_scores.get(user_id, 0.7)
        anomalies = self.detect_behavior_anomalies(user_id)
        alerts = self.user_alerts.get(user_id, [])
        critical_flags = self.critical_flags.get(user_id, [])
        trend = self._calculate_trend(user_id)
        
        # Calcular probabilidad de churn (0-1)
        churn_prob = 0.0
        
        # Factor 1: Score de satisfacción
        if satisfaction < 0.3:
            churn_prob += 0.6
        elif satisfaction < 0.5:
            churn_prob += 0.4
        elif satisfaction < 0.7:
            churn_prob += 0.2
        
        # Factor 2: Anomalías detectadas
        if len(anomalies) >= 3:
            churn_prob += 0.3
        elif len(anomalies) >= 1:
            churn_prob += 0.15
        
        # Factor 3: Trend negativo
        if trend == "deteriorándose":
            churn_prob += 0.2
        
        # Factor 4: Alertas críticas
        if any(a["level"] == "CRÍTICO" for a in alerts):
            churn_prob += 0.4
        
        churn_prob = min(1.0, churn_prob)
        
        # Determinar nivel de riesgo
        if churn_prob > 0.75 or satisfaction < 0.2:
            risk_level = "crítico"
        elif churn_prob > 0.5 or satisfaction < 0.4:
            risk_level = "alto"
        elif churn_prob > 0.3 or satisfaction < 0.6:
            risk_level = "medio"
        else:
            risk_level = "bajo"
        
        # Acciones urgentes
        urgent_actions = []
        
        if risk_level == "crítico":
            urgent_actions.append("🚨 CONTACTAR GERENTE INMEDIATAMENTE")
            urgent_actions.append("Ofrecer solución personalizada de emergencia")
            urgent_actions.append("Considerar oferta especial de retención")
        elif risk_level == "alto":
            urgent_actions.append("Asignar especialista para seguimiento")
            urgent_actions.append("Preparar propuesta personalizada")
            urgent_actions.append("Planificar llamada en próximas 24h")
        elif risk_level == "medio":
            urgent_actions.append("Monitorear interacciones próximas")
            urgent_actions.append("Preparar respuestas proactivas")
        
        # Agregar acciones específicas por anomalía
        for anomaly in anomalies:
            urgent_actions.append(f"⚠️ {anomaly['action']}")
        
        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "churn_probability": round(churn_prob, 3),
            "satisfaction_score": round(satisfaction, 3),
            "satisfaction_level": self._score_to_level(satisfaction),
            "trend": trend,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "active_alerts": len(alerts),
            "critical_flags": len(critical_flags),
            "urgent_actions": urgent_actions,
            "recommendation": self._get_recommendation(risk_level, churn_prob)
        }
    
    def _get_recommendation(self, risk_level: str, churn_prob: float) -> str:
        """Genera recomendación basada en riesgo"""
        if risk_level == "crítico":
            return "INTERVENCIÓN INMEDIATA REQUERIDA - Probabilidad de pérdida > 75%"
        elif risk_level == "alto":
            return "Acción de retención planificada para próximas 24 horas"
        elif risk_level == "medio":
            return "Monitoreo activo - Prepara propuesta de valor mejorada"
        else:
            return "Cliente en buen estado - Mantener calidad de servicio"
    
    def generate_retention_offer(self, user_id: str) -> Dict:
        """
        Genera oferta de retención personalizada
        Más agresiva cuanto mayor sea el riesgo
        """
        assessment = self.get_user_risk_assessment(user_id)
        risk_level = assessment["risk_level"]
        
        # Ofertas por nivel de riesgo
        offers = {
            "crítico": {
                "discount": 40,
                "bonus": "Experiencia VIP completa",
                "validity_hours": 24,
                "message": "Te tenemos una oferta especial que no puedes rechazar 💙"
            },
            "alto": {
                "discount": 30,
                "bonus": "Pack de servicios premium",
                "validity_hours": 48,
                "message": "Queremos que vuelvas - oferta exclusiva"
            },
            "medio": {
                "discount": 15,
                "bonus": "Acceso a nuevas actividades",
                "validity_hours": 72,
                "message": "Nueva actividad exclusiva para ti"
            },
            "bajo": {
                "discount": 10,
                "bonus": "Puntos de referido",
                "validity_hours": 168,
                "message": "Sigue disfrutando de Fundo Moraga"
            }
        }
        
        offer = offers.get(risk_level, offers["bajo"])
        
        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "discount_percentage": offer["discount"],
            "bonus_offer": offer["bonus"],
            "validity_hours": offer["validity_hours"],
            "message": offer["message"],
            "urgency": "ALTA" if risk_level in ["crítico", "alto"] else "MEDIA"
        }


def get_satisfaction_detector() -> SatisfactionDetector:
    """Factory function"""
    global _detector
    if '_detector' not in globals():
        _detector = SatisfactionDetector()
    return _detector
