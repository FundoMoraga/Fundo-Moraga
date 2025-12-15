"""
Gestor de conversaciones que maneja el ciclo de vida completo
Incluye detección de fin de conversación y envío de resúmenes
"""

from typing import Dict, Optional, List
import json
from datetime import datetime
from resend_client import get_resend_client

class ConversationManager:
    """Gestiona el ciclo de vida de las conversaciones y envío de resúmenes"""
    
    def __init__(self):
        self.resend_client = get_resend_client()
        self.user_info_cache = {}  # Cache temporal de información capturada
    
    def extract_user_info_from_tool_call(self, tool_call_result: str) -> Optional[Dict]:
        """
        Extrae información del usuario desde el resultado de capturar_informacion_usuario
        
        Args:
            tool_call_result: Resultado de la función capturar_informacion_usuario
        
        Returns:
            Dict con la información extraída o None si no se pudo extraer
        """
        try:
            # Buscar los datos en el resultado
            lines = tool_call_result.split('\n')
            info = {}
            
            for line in lines:
                if 'Nombre:' in line:
                    info['nombre'] = line.split('Nombre:')[1].strip()
                elif 'Interés:' in line or 'Interes:' in line:
                    info['interes'] = line.split(':')[1].strip()
                elif 'Contacto:' in line:
                    info['contacto'] = line.split('Contacto:')[1].strip()
            
            # Validar que tengamos al menos nombre e interés
            if info.get('nombre', 'No proporcionado') != 'No proporcionado' and \
               info.get('interes', 'No especificado') != 'No especificado':
                return info
            
            return None
            
        except Exception as e:
            print(f"Error extrayendo información del usuario: {str(e)}")
            return None
    
    def should_send_summary(self, conversation_history: List[Dict]) -> bool:
        """
        Determina si se debe enviar un resumen de la conversación
        
        Criterios:
        - La conversación tiene al menos 3 intercambios
        - Se ha capturado información del usuario
        - El último mensaje sugiere cierre o despedida
        
        Args:
            conversation_history: Historial de mensajes
        
        Returns:
            True si se debe enviar el resumen
        """
        if len(conversation_history) < 3:
            return False
        
        # Buscar si hay información capturada en algún mensaje
        info_captured = False
        for msg in conversation_history:
            content = msg.get('content', '').lower()
            if 'información registrada' in content or 'información será enviada' in content:
                info_captured = True
                break
        
        if not info_captured:
            return False
        
        # Verificar si el último mensaje parece ser una despedida
        last_msg = conversation_history[-1].get('content', '').lower()
        farewell_keywords = [
            'gracias', 'perfecto', 'excelente', 'muchas gracias',
            'hasta luego', 'adiós', 'chao', 'nos vemos',
            'eso es todo', 'nada más', 'es todo'
        ]
        
        for keyword in farewell_keywords:
            if keyword in last_msg:
                return True
        
        return False
    
    def send_conversation_summary(
        self,
        user_id: str,
        conversation_id: str,
        user_info: Dict,
        platform: str = "Instagram"
    ) -> Dict:
        """
        Envía el resumen de conversación por email
        
        Args:
            user_id: ID del usuario (Instagram ID o session ID web)
            conversation_id: ID de la conversación en Cosmos DB
            user_info: Dict con nombre, interes, contacto
            platform: Plataforma de origen
        
        Returns:
            Resultado del envío
        """
        try:
            result = self.resend_client.send_conversation_summary(
                user_name=user_info.get('nombre', 'No proporcionado'),
                user_interest=user_info.get('interes', 'No especificado'),
                user_contact=user_info.get('contacto', 'No proporcionado'),
                conversation_id=conversation_id,
                platform=platform
            )
            
            if result['success']:
                print(f"✅ Resumen enviado exitosamente para conversación {conversation_id}")
            else:
                print(f"❌ Error enviando resumen: {result.get('error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error en send_conversation_summary: {str(e)}"
            print(error_msg)
            return {"success": False, "error": error_msg}
    
    def cache_user_info(self, user_id: str, info: Dict):
        """
        Almacena información del usuario en cache temporal
        
        Args:
            user_id: ID del usuario
            info: Información a cachear
        """
        self.user_info_cache[user_id] = {
            **info,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cached_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Recupera información cacheada del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Info cacheada o None
        """
        return self.user_info_cache.get(user_id)
    
    def clear_cache(self, user_id: str):
        """
        Limpia el cache de un usuario específico
        
        Args:
            user_id: ID del usuario
        """
        if user_id in self.user_info_cache:
            del self.user_info_cache[user_id]


# Singleton instance
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """Obtiene la instancia singleton del gestor de conversaciones"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
