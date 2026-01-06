"""
Sistema avanzado de extracción de entidades
Identifica fechas, precios, preferencias y otras entidades en texto
"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
import config
import os

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class EntityExtractor:
    """Extrae entidades relevantes de mensajes del usuario"""
    
    def __init__(self):
        self.client = None
        if _OPENAI_AVAILABLE and config.OPENAI_API_KEY and getattr(config, "ADVANCED_AI_USE_OPENAI", False):
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extrae todas las entidades relevantes del texto.
        
        Returns:
            {
                'dates': [{'date': datetime, 'original': str, 'type': 'específica|relativa'}],
                'prices': [{'amount': float, 'currency': str, 'original': str}],
                'quantities': [{'value': int, 'unit': str, 'original': str}],
                'activities': [str],
                'locations': [str],
                'preferences': [str],
                'emails': [str],
                'phones': [str],
                'people': [str]
            }
        """
        
        result = {
            'dates': self.extract_dates(text),
            'prices': self.extract_prices(text),
            'quantities': self.extract_quantities(text),
            'activities': self.extract_activities(text),
            'locations': self.extract_locations(text),
            'preferences': self.extract_preferences(text),
            'emails': self.extract_emails(text),
            'phones': self.extract_phones(text),
            'people': self.extract_people_names(text)
        }
        
        return result
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae fechas en varios formatos.
        Ej: "25 de diciembre", "Navidad 2025", "el próximo viernes", "12/12/2025"
        """
        dates = []
        text_lower = text.lower()
        
        # Patrones de fechas específicas
        patterns = {
            # DD/MM/YYYY o DD-MM-YYYY
            r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b': 'específica',
            # YYYY-MM-DD
            r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b': 'específica',
        }
        
        for pattern, date_type in patterns.items():
            for match in re.finditer(pattern, text):
                dates.append({
                    'date': match.group(),
                    'original': match.group(),
                    'type': date_type
                })
        
        # Fechas relativas
        relative_patterns = {
            r'\b(hoy|mañana|pasado mañana)\b': 0,
            r'\b(este|el) (lunes|martes|miércoles|jueves|viernes|sábado|domingo)\b': 'this_week',
            r'\b(próximo|el próximo) (lunes|martes|miércoles|jueves|viernes|sábado|domingo)\b': 'next_week',
            r'\b(este|próximo) (fin de semana|finde)\b': 'weekend',
            r'\b(navidad|año nuevo|año nuevo|pascua)\b': 'holiday'
        }
        
        for pattern in relative_patterns.keys():
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower)
                dates.append({
                    'date': 'relativa',
                    'original': match.group(),
                    'type': 'relativa'
                })
        
        return dates
    
    def extract_prices(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae precios mencionados.
        Ej: "$50000", "50 mil", "$50K", "CLP 50000"
        """
        prices = []
        
        # Patrones de precio
        patterns = [
            # $50000 o $ 50000 o $50.000
            (r'\$\s*(\d{1,3}(?:\.?\d{3})*(?:,\d{2})?)', '$'),
            # 50000 CLP o 50 mil
            (r'(\d{1,3}(?:\.?\d{3})*)\s*(mil|CLP|peso|pesos|chilenos?)', 'CLP'),
        ]
        
        for pattern, currency in patterns:
            for match in re.finditer(pattern, text):
                # Limpiar número
                amount_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    amount = float(amount_str)
                    prices.append({
                        'amount': amount,
                        'currency': currency,
                        'original': match.group()
                    })
                except ValueError:
                    pass
        
        return prices
    
    def extract_quantities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae cantidades.
        Ej: "2 personas", "10 autos", "50 invitados"
        """
        quantities = []
        
        pattern = r'(\d+)\s+(persona|personas|auto|autos|carro|carros|moto|motos|persona|grupo|gente|invitad[oa]s?|participante|participantes)'
        
        for match in re.finditer(pattern, text.lower()):
            quantities.append({
                'value': int(match.group(1)),
                'unit': match.group(2),
                'original': match.group()
            })
        
        return quantities
    
    def extract_activities(self, text: str) -> List[str]:
        """
        Extrae actividades mencionadas.
        """
        activities = []
        activity_keywords = {
            'off-road': ['off road', 'offroad', 'ruteo', 'ruta', 'batuco', 'quads', 'motos', 'autos'],
            'evento': ['evento', 'fiesta', 'reunión', 'conferencia', 'retiro', 'congreso', 'junta'],
            'producción': ['producción', 'cine', 'fotografía', 'película', 'publicidad', 'rodaje'],
            'visita': ['visita', 'turismo', 'recorrido', 'tour', 'conocer'],
            'historia': ['historia', 'histórico', 'patrimonio', 'colonial']
        }
        
        text_lower = text.lower()
        for activity, keywords in activity_keywords.items():
            if any(kw in text_lower for kw in keywords):
                activities.append(activity)
        
        return list(set(activities))
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extrae ubicaciones mencionadas.
        """
        locations = []
        location_keywords = {
            'Fundo Moraga': ['fundo moraga', 'fundo', 'moraga'],
            'Santiago': ['santiago', 'capital'],
            'Batuco': ['batuco'],
            'Andes': ['andes', 'cordillera']
        }
        
        text_lower = text.lower()
        for location, keywords in location_keywords.items():
            if any(kw in text_lower for kw in keywords):
                locations.append(location)
        
        return list(set(locations))
    
    def extract_preferences(self, text: str) -> List[str]:
        """
        Extrae preferencias expresadas.
        Ej: "prefiero en la tarde", "me encanta la naturaleza", "mejor fin de semana"
        """
        preferences = []
        
        # Palabras indicadoras de preferencia
        preference_markers = [
            r'\b(me encanta|me gusta|prefiero|preferencia|mejor|ideal)\s+(.+?)(?:[,.!?]|$)',
            r'\b(quiero|deseo|busco)\s+(.+?)(?:[,.!?]|$)',
            r'\b(sin|con|solo)\s+(.+?)(?:[,.!?]|$)',
        ]
        
        for pattern in preference_markers:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                pref = match.group(2).strip()
                if len(pref) < 50:  # Evitar frases muy largas
                    preferences.append(pref)
        
        return list(set(preferences))
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Extrae direcciones de email.
        """
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    def extract_phones(self, text: str) -> List[str]:
        """
        Extrae números de teléfono.
        Formato: +56 9 1234 5678, 91234567, etc.
        """
        phones = []
        patterns = [
            r'\+56\s*9\s*\d{4}\s*\d{4}',  # +56 9 1234 5678
            r'\+56\d{9}',                   # +569123456789
            r'9\s*\d{4}\s*\d{4}',           # 9 1234 5678
            r'\d{8,9}',                     # 91234567
        ]
        
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    def extract_people_names(self, text: str) -> List[str]:
        """
        Intenta extraer nombres de personas.
        Nota: Es heurístico, no es 100% preciso.
        """
        names = []
        
        # Buscar patrones como "Soy X" o "Me llamo X"
        patterns = [
            r'\b(?:soy|me llamo|nombre es|llamado|nombre:?)\s+([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)?)',
            r'\b(Juan|María|Carlos|Ana|Pedro|Rosa|Diego|Patricia)\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1) if match.lastindex else match.group()
                if len(name) > 2:
                    names.append(name)
        
        return list(set(names))
    
    def get_entity_summary(self, entities: Dict[str, Any]) -> str:
        """
        Convierte entidades extraídas en resumen de texto.
        """
        parts = []
        
        if entities.get('dates'):
            dates_str = ", ".join([d['original'] for d in entities['dates']])
            parts.append(f"Fecha: {dates_str}")
        
        if entities.get('prices'):
            prices_str = ", ".join([f"{p['amount']}{p['currency']}" for p in entities['prices']])
            parts.append(f"Presupuesto: {prices_str}")
        
        if entities.get('quantities'):
            qty_str = ", ".join([f"{q['value']} {q['unit']}" for q in entities['quantities']])
            parts.append(f"Cantidad: {qty_str}")
        
        if entities.get('activities'):
            act_str = ", ".join(entities['activities'])
            parts.append(f"Actividades: {act_str}")
        
        if entities.get('preferences'):
            pref_str = ", ".join(entities['preferences'][:3])
            parts.append(f"Preferencias: {pref_str}")
        
        if entities.get('people'):
            person_str = ", ".join(entities['people'][:2])
            parts.append(f"Persona: {person_str}")
        
        return " | ".join(parts) if parts else "Sin entidades específicas"


def get_entity_extractor() -> EntityExtractor:
    """Obtiene instancia singleton del extractor"""
    global _extractor
    if '_extractor' not in globals():
        _extractor = EntityExtractor()
    return _extractor
