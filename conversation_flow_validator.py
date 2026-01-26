"""
Validador de flujo conversacional para Hernando.
Previene el "modo interrogatorio" detectando patrones de preguntas consecutivas.
"""

import re
from typing import List, Dict, Optional


class ConversationFlowValidator:
    """
    Valida que las conversaciones no caigan en patrones de interrogatorio.
    
    Reglas:
    - Máximo 2 preguntas consecutivas sin comentarios/validaciones entre medio
    - Detecta cuando bot hace 3+ preguntas seguidas
    - Sugiere mensajes de validación/comentario para recuperar naturalidad
    """
    
    def __init__(self, max_consecutive_questions: int = 2):
        """
        Args:
            max_consecutive_questions: Máximo de preguntas consecutivas permitidas (default: 2)
        """
        self.max_consecutive_questions = max_consecutive_questions
    
    def count_questions_in_text(self, text: str) -> int:
        """
        Cuenta cuántas preguntas hay en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Número de preguntas encontradas
        """
        if not text:
            return 0
        
        # Contar signos de interrogación
        question_marks = text.count('¿')
        
        # También detectar palabras interrogativas al inicio de oraciones
        interrogatives = ['cuál', 'cuáles', 'cuándo', 'cuánto', 'cuántos', 'cuánta', 'cuántas', 
                         'cómo', 'dónde', 'qué', 'quién', 'quiénes', 'por qué']
        
        text_lower = text.lower()
        for word in interrogatives:
            # Buscar palabra interrogativa al inicio de oración (después de . o al inicio)
            pattern = rf'(^|\. ){word}\b'
            if re.search(pattern, text_lower):
                question_marks += 1
        
        return question_marks
    
    def validate_no_interrogation(self, recent_bot_messages: List[str]) -> Dict[str, any]:
        """
        Valida que no haya patrón de interrogatorio en mensajes recientes del bot.
        
        Args:
            recent_bot_messages: Lista de últimos mensajes del bot (más reciente primero)
            
        Returns:
            Dict con:
            - is_valid: bool - True si no hay interrogatorio
            - consecutive_questions: int - Número de preguntas consecutivas detectadas
            - needs_validation: bool - True si necesita mensaje de validación
            - suggestion: str - Sugerencia de mensaje de validación (si aplica)
        """
        if not recent_bot_messages:
            return {
                'is_valid': True,
                'consecutive_questions': 0,
                'needs_validation': False,
                'suggestion': None
            }
        
        consecutive_count = 0
        
        # Contar preguntas consecutivas desde el mensaje más reciente
        for message in recent_bot_messages:
            question_count = self.count_questions_in_text(message)
            
            if question_count > 0:
                consecutive_count += question_count
            else:
                # Si encuentra mensaje sin preguntas, rompe la racha
                break
        
        is_valid = consecutive_count <= self.max_consecutive_questions
        needs_validation = consecutive_count >= self.max_consecutive_questions
        
        suggestion = None
        if needs_validation:
            suggestion = self._generate_validation_message()
        
        return {
            'is_valid': is_valid,
            'consecutive_questions': consecutive_count,
            'needs_validation': needs_validation,
            'suggestion': suggestion
        }
    
    def _generate_validation_message(self) -> str:
        """
        Genera mensaje de validación/comentario para recuperar naturalidad.
        
        Returns:
            Mensaje sugerido para validar/comentar antes de siguiente pregunta
        """
        validation_phrases = [
            "Ya cachái más o menos cómo funciona, ¿cierto?",
            "Perfecto, déjame ver qué te puedo armar con eso.",
            "Bacán, con eso ya te puedo ayudar mejor.",
            "Ok, eso me sirve caleta para orientarte.",
            "Dale, voy entendiendo lo que necesitái.",
            "Perfecto, ya me voy haciendo la idea.",
            "Excelente, con eso ya cachamos bien qué necesitái.",
        ]
        
        import random
        return random.choice(validation_phrases)
    
    def should_add_validation(self, recent_bot_messages: List[str]) -> bool:
        """
        Determina si se debe agregar mensaje de validación antes de continuar.
        
        Args:
            recent_bot_messages: Lista de últimos mensajes del bot
            
        Returns:
            True si debe agregar validación, False si puede continuar normal
        """
        result = self.validate_no_interrogation(recent_bot_messages)
        return result['needs_validation']
    
    def get_validation_prefix(self, recent_bot_messages: List[str]) -> Optional[str]:
        """
        Obtiene prefijo de validación si es necesario.
        
        Args:
            recent_bot_messages: Lista de últimos mensajes del bot
            
        Returns:
            String con prefijo de validación o None si no es necesario
        """
        result = self.validate_no_interrogation(recent_bot_messages)
        
        if result['needs_validation']:
            return result['suggestion']
        
        return None


# Instancia global para uso en el bot
validator = ConversationFlowValidator(max_consecutive_questions=2)


def validate_conversation_flow(recent_bot_messages: List[str]) -> Dict[str, any]:
    """
    Función helper para validar flujo conversacional.
    
    Args:
        recent_bot_messages: Lista de últimos mensajes del bot (más reciente primero)
        
    Returns:
        Dict con validación y sugerencias
    """
    return validator.validate_no_interrogation(recent_bot_messages)


def get_validation_message_if_needed(recent_bot_messages: List[str]) -> Optional[str]:
    """
    Función helper para obtener mensaje de validación si es necesario.
    
    Args:
        recent_bot_messages: Lista de últimos mensajes del bot
        
    Returns:
        Mensaje de validación o None
    """
    return validator.get_validation_prefix(recent_bot_messages)


if __name__ == "__main__":
    # Tests básicos
    print("=== Tests de Conversation Flow Validator ===\n")
    
    # Test 1: Sin interrogatorio
    messages_ok = [
        "Bacán que te interese el off-road. Acá hemos tenido grupos desde 2 hasta 10 autos.",
        "¿Te tinca para cuándo más o menos?",
    ]
    result = validate_conversation_flow(messages_ok)
    print(f"Test 1 - Conversación OK:")
    print(f"  Válido: {result['is_valid']}")
    print(f"  Preguntas consecutivas: {result['consecutive_questions']}")
    print(f"  Necesita validación: {result['needs_validation']}\n")
    
    # Test 2: Interrogatorio detectado
    messages_interrogation = [
        "¿Y cuántos autos serían?",
        "¿Para qué fecha estabas pensando?",
        "¿Cuál es tu nombre?",
        "Te cuento que tenemos rutas piolas."
    ]
    result = validate_conversation_flow(messages_interrogation)
    print(f"Test 2 - Interrogatorio detectado:")
    print(f"  Válido: {result['is_valid']}")
    print(f"  Preguntas consecutivas: {result['consecutive_questions']}")
    print(f"  Necesita validación: {result['needs_validation']}")
    print(f"  Sugerencia: {result['suggestion']}\n")
    
    # Test 3: Mensaje sin preguntas
    messages_no_questions = [
        "Bacán que te interese. Te cuento que las rutas off-road son la raja acá.",
    ]
    result = validate_conversation_flow(messages_no_questions)
    print(f"Test 3 - Sin preguntas:")
    print(f"  Válido: {result['is_valid']}")
    print(f"  Preguntas consecutivas: {result['consecutive_questions']}\n")
    
    # Test 4: Exactamente en el límite
    messages_limit = [
        "¿Y para cuándo lo necesitái?",
        "¿Te tinca más este finde o el próximo?",
    ]
    result = validate_conversation_flow(messages_limit)
    print(f"Test 4 - En el límite (2 preguntas):")
    print(f"  Válido: {result['is_valid']}")
    print(f"  Preguntas consecutivas: {result['consecutive_questions']}")
    print(f"  Necesita validación: {result['needs_validation']}")

