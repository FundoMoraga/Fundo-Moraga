"""
Validador de Fechas Libres para Batuco Off Road
Solo permite offering Fecha Libre si ha sido anunciada en Instagram
"""
from datetime import datetime
import config

class FechaLibreValidator:
    """Valida si una fecha es una Fecha Libre activa anunciada"""
    
    @staticmethod
    def is_fecha_libre_active(date_str: str) -> bool:
        """
        Verifica si una fecha específica está activa como Fecha Libre
        
        Args:
            date_str: fecha en formato YYYY-MM-DD o similar
            
        Returns:
            True si está en la lista de Fechas Libres activas
        """
        try:
            # Normalizar formato (extraer YYYY-MM-DD si viene con hora)
            date_part = date_str.split("T")[0] if "T" in date_str else date_str.split(" ")[0]
            
            active_dates = config.ACTIVE_FECHA_LIBRE_DATES
            return date_part in active_dates
        except:
            return False
    
    @staticmethod
    def get_active_fecha_libre_dates() -> list:
        """Retorna lista de fechas libres activas"""
        return config.ACTIVE_FECHA_LIBRE_DATES or []
    
    @staticmethod
    def format_pricing_info() -> str:
        """
        Genera información de precios formateada según horarios
        IMPORTANTE: No menciona Fecha Libre a menos que esté activa
        """
        return """
**HORARIOS Y TARIFAS - Batuco Off Road:**

🔷 **LUNES A VIERNES** (9:00 - 17:00)
   • Auto: $15.000
   • Moto: $10.000
   
🔶 **FIN DE SEMANA** (Sábado/Domingo sin Fecha Libre)
   • Arriendo completo por grupo: $200.000
   (Puede ser grupo pequeño o numeroso - mismo precio)

📱 **Anuncia Fecha Libre en Instagram:**
   • Se abre sábado o domingo con tarifa de semana
   • $15.000 auto / $10.000 moto
   • SOLO cuando se anuncia en @Batuco_OffRoad
   
💬 **Otras actividades/eventos**
   • Contacto: contacto@fundomoraga.com
   • Teléfono: (Consultar)
"""

    @staticmethod
    def should_mention_fecha_libre(message: str) -> bool:
        """
        Determina si debe mencionarse Fecha Libre en la respuesta
        Solo si el usuario pregunta explícitamente O hay fechas activas
        """
        fecha_libre_keywords = ["fecha libre", "domingo", "abierto", "fecha-libre"]
        
        # Solo si hay fechas activas o usuario pregunta específicamente
        has_active = len(config.ACTIVE_FECHA_LIBRE_DATES) > 0
        user_asking = any(kw in message.lower() for kw in fecha_libre_keywords)
        
        return has_active or user_asking


def validate_response_for_fecha_libre(response: str) -> str:
    """
    Limpia respuestas que mencionan Fecha Libre si no está anunciada
    PREVIENE que el bot ofrezca domingos sin anuncio previo
    """
    if not FechaLibreValidator.get_active_fecha_libre_dates():
        # Si NO hay Fechas Libres activas, remover menciones
        problematic_phrases = [
            "próximo domingo abierto tipo \"Fecha Libre\"",
            "el próximo domingo abierto",
            "domingo abierto al público",
            "Fecha Libre",
            "fecha libre",
            "este domingo"
        ]
        
        for phrase in problematic_phrases:
            if phrase.lower() in response.lower():
                # Reemplazar con mensaje genérico
                response = response.replace(phrase, "cuando anunciemos Fecha Libre por Instagram")
    
    return response
