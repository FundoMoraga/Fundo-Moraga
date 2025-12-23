"""
Modo Desarrollador para Hernando
Permite editar Cosmos DB y prompts directamente desde el chat
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import json
import re
from cosmos_client import get_memory_store, get_conversation_store
from prompts_loader import load_prompts_from_cosmos

# Clave secreta para activar/desactivar
ADMIN_KEY = "Ve88967788@"

class AdminMode:
    """Gestiona el modo desarrollador de Hernando"""
    
    def __init__(self):
        self.memory_store = get_memory_store()
        self.conversation_store = get_conversation_store()
        self.active_sessions: Dict[str, Dict] = {}
    
    def is_admin_key(self, message: str) -> bool:
        """Verifica si el mensaje contiene la clave de admin"""
        return message.strip() == ADMIN_KEY
    
    def is_active(self, user_id: str) -> bool:
        """Verifica si el modo admin está activo para un usuario"""
        return user_id in self.active_sessions
    
    def toggle_mode(self, user_id: str, platform: str = "web") -> tuple[bool, str]:
        """
        Activa o desactiva el modo admin para un usuario
        
        Returns:
            tuple: (is_active, message)
        """
        if user_id in self.active_sessions:
            # Desactivar
            session = self.active_sessions[user_id]
            duration = datetime.now(timezone.utc) - session["started_at"]
            changes = session.get("changes_made", 0)
            
            del self.active_sessions[user_id]
            
            return False, (
                f"🔓 **Modo Desarrollador DESACTIVADO**\n\n"
                f"✅ Sesión finalizada\n"
                f"⏱️ Duración: {duration.seconds // 60} minutos\n"
                f"📝 Cambios realizados: {changes}\n\n"
                f"Hernando ha vuelto al modo normal."
            )
        else:
            # Activar
            self.active_sessions[user_id] = {
                "started_at": datetime.now(timezone.utc),
                "platform": platform,
                "changes_made": 0,
                "context": []
            }
            
            return True, (
                f"🔐 **MODO DESARROLLADOR ACTIVADO**\n\n"
                f"Comandos disponibles:\n"
                f"• `/view [categoria]` - Ver datos de Cosmos DB\n"
                f"• `/edit [id] [campo] [valor]` - Editar registro\n"
                f"• `/delete [id]` - Eliminar registro\n"
                f"• `/prompts` - Ver/editar prompts de Hernando\n"
                f"• `/search [texto]` - Buscar en Memoria\n"
                f"• `/conversations [user_id]` - Ver conversaciones\n"
                f"• `/error [conversation_id]` - Analizar error en conversación\n"
                f"• `/fix [descripción]` - Aplicar corrección\n"
                f"• `{ADMIN_KEY}` - Salir del modo desarrollador\n\n"
                f"💡 **Tip:** Puedes describir el problema en lenguaje natural\n"
                f"y te ayudaré a identificar qué corregir."
            )
    
    def increment_changes(self, user_id: str):
        """Incrementa el contador de cambios realizados"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]["changes_made"] += 1
    
    def add_context(self, user_id: str, action: str, details: Dict):
        """Registra una acción en el contexto de la sesión"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]["context"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "details": details
            })
    
    def process_admin_command(self, user_id: str, message: str) -> Optional[str]:
        """
        Procesa comandos del modo desarrollador
        
        Returns:
            str: Respuesta al comando, o None si no es un comando admin
        """
        if not self.is_active(user_id):
            return None
        
        message = message.strip()
        
        # Comandos específicos
        if message.startswith("/view"):
            return self._cmd_view(user_id, message)
        elif message.startswith("/edit"):
            return self._cmd_edit(user_id, message)
        elif message.startswith("/delete"):
            return self._cmd_delete(user_id, message)
        elif message.startswith("/prompts"):
            return self._cmd_prompts(user_id, message)
        elif message.startswith("/search"):
            return self._cmd_search(user_id, message)
        elif message.startswith("/conversations"):
            return self._cmd_conversations(user_id, message)
        elif message.startswith("/error"):
            return self._cmd_error(user_id, message)
        elif message.startswith("/fix"):
            return self._cmd_fix(user_id, message)
        else:
            # Análisis en lenguaje natural
            return self._analyze_natural_request(user_id, message)
    
    def _cmd_view(self, user_id: str, message: str) -> str:
        """Ver datos de Cosmos DB por categoría"""
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return (
                "**Uso:** `/view [categoria]`\n\n"
                "Categorías disponibles:\n"
                "• `prompts` - Prompts de sistema\n"
                "• `memoria` - Base de datos de memoria\n"
                "• `conversaciones` - Historial de chats\n"
                "• `precios` - Información de precios\n"
                "• `fechas-libres` - Fechas libres activas\n"
                "• `training` - Datos de entrenamiento"
            )
        
        categoria = parts[1].lower()
        
        try:
            if categoria == "fechas-libres":
                import config
                dates = getattr(config, "ACTIVE_FECHA_LIBRE_DATES", [])
                if not dates:
                    return "📅 **Fechas Libres:** No hay fechas activas configuradas."
                return f"📅 **Fechas Libres Activas:**\n" + "\n".join(f"• {d}" for d in dates)
            
            elif categoria == "prompts":
                prompts = load_prompts_from_cosmos()
                if not prompts:
                    return "❌ No se encontraron prompts en Cosmos DB."
                
                result = "📝 **Prompts de Sistema:**\n\n"
                for key, value in prompts.items():
                    preview = value[:100] + "..." if len(value) > 100 else value
                    result += f"**{key}:**\n{preview}\n\n"
                return result
            
            elif categoria == "memoria":
                # Listar últimos 10 items de memoria
                query = "SELECT TOP 10 * FROM c ORDER BY c._ts DESC"
                items = self.memory_store.query_items(query)
                
                if not items:
                    return "❌ No hay datos en la memoria."
                
                result = f"🧠 **Últimos {len(items)} registros de Memoria:**\n\n"
                for item in items:
                    id_val = item.get("id", "N/A")
                    categoria_val = item.get("Categoria", "N/A")
                    result += f"• ID: `{id_val}` | Categoría: `{categoria_val}`\n"
                
                return result
            
            elif categoria == "conversaciones":
                return (
                    "Para ver conversaciones, usa:\n"
                    "`/conversations [user_id]`\n\n"
                    "Ejemplo: `/conversations 12345678`"
                )
            
            else:
                return f"❌ Categoría desconocida: `{categoria}`"
        
        except Exception as e:
            return f"❌ **Error al consultar datos:**\n{str(e)}"
    
    def _cmd_edit(self, user_id: str, message: str) -> str:
        """Editar un registro en Cosmos DB"""
        parts = message.split(maxsplit=3)
        if len(parts) < 4:
            return (
                "**Uso:** `/edit [id] [campo] [valor]`\n\n"
                "Ejemplo:\n"
                "`/edit precios-batuco tarifa-auto 15000`"
            )
        
        _, item_id, field, new_value = parts
        
        try:
            # Buscar el item
            query = f"SELECT * FROM c WHERE c.id = '{item_id}'"
            items = self.memory_store.query_items(query)
            
            if not items:
                return f"❌ No se encontró registro con ID: `{item_id}`"
            
            item = items[0]
            old_value = item.get(field, "(no existía)")
            
            # Actualizar campo
            item[field] = new_value
            self.memory_store.upsert_item(item)
            
            self.increment_changes(user_id)
            self.add_context(user_id, "edit", {
                "item_id": item_id,
                "field": field,
                "old_value": old_value,
                "new_value": new_value
            })
            
            return (
                f"✅ **Registro actualizado**\n\n"
                f"ID: `{item_id}`\n"
                f"Campo: `{field}`\n"
                f"Valor anterior: `{old_value}`\n"
                f"Valor nuevo: `{new_value}`"
            )
        
        except Exception as e:
            return f"❌ **Error al editar:**\n{str(e)}"
    
    def _cmd_delete(self, user_id: str, message: str) -> str:
        """Eliminar un registro de Cosmos DB"""
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return "**Uso:** `/delete [id]`\n\nEjemplo: `/delete registro-antiguo`"
        
        item_id = parts[1]
        
        try:
            # Buscar el item para confirmación
            query = f"SELECT * FROM c WHERE c.id = '{item_id}'"
            items = self.memory_store.query_items(query)
            
            if not items:
                return f"❌ No se encontró registro con ID: `{item_id}`"
            
            item = items[0]
            categoria = item.get("Categoria", "N/A")
            
            # Eliminar (necesitas implementar delete_item en cosmos_client.py)
            # self.memory_store.delete_item(item_id, partition_key_value)
            
            self.increment_changes(user_id)
            self.add_context(user_id, "delete", {"item_id": item_id, "categoria": categoria})
            
            return (
                f"⚠️ **Eliminación programada**\n\n"
                f"ID: `{item_id}`\n"
                f"Categoría: `{categoria}`\n\n"
                f"Nota: Implementa `delete_item()` en cosmos_client.py para completar esta función."
            )
        
        except Exception as e:
            return f"❌ **Error al eliminar:**\n{str(e)}"
    
    def _cmd_prompts(self, user_id: str, message: str) -> str:
        """Ver y editar prompts de sistema"""
        parts = message.split(maxsplit=2)
        
        if len(parts) == 1:
            # Solo listar
            prompts = load_prompts_from_cosmos()
            result = "📝 **Prompts disponibles:**\n\n"
            for key in prompts.keys():
                result += f"• `{key}`\n"
            result += "\n**Uso:** `/prompts [nombre] [nuevo_texto]`"
            return result
        
        elif len(parts) == 2:
            # Ver contenido completo
            prompt_name = parts[1]
            prompts = load_prompts_from_cosmos()
            if prompt_name not in prompts:
                return f"❌ Prompt no encontrado: `{prompt_name}`"
            return f"**{prompt_name}:**\n\n{prompts[prompt_name]}"
        
        else:
            # Editar prompt
            prompt_name = parts[1]
            new_text = parts[2]
            
            # Aquí deberías actualizar en Cosmos DB (container Hernando)
            return (
                f"✅ **Prompt actualizado:** `{prompt_name}`\n\n"
                f"Nota: Implementa actualización de prompts en Cosmos DB."
            )
    
    def _cmd_search(self, user_id: str, message: str) -> str:
        """Buscar en memoria por texto"""
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return "**Uso:** `/search [texto]`\n\nEjemplo: `/search precios batuco`"
        
        search_text = parts[1].lower()
        
        try:
            # Búsqueda simple en todos los items
            query = "SELECT * FROM c"
            all_items = self.memory_store.query_items(query, limit=100)
            
            matches = []
            for item in all_items:
                item_str = json.dumps(item, ensure_ascii=False).lower()
                if search_text in item_str:
                    matches.append(item)
            
            if not matches:
                return f"❌ No se encontraron resultados para: `{search_text}`"
            
            result = f"🔍 **Encontrados {len(matches)} resultados:**\n\n"
            for item in matches[:10]:  # Máximo 10
                id_val = item.get("id", "N/A")
                categoria = item.get("Categoria", "N/A")
                result += f"• `{id_val}` | Categoría: {categoria}\n"
            
            if len(matches) > 10:
                result += f"\n... y {len(matches) - 10} más"
            
            return result
        
        except Exception as e:
            return f"❌ **Error en búsqueda:**\n{str(e)}"
    
    def _cmd_conversations(self, user_id: str, message: str) -> str:
        """Ver conversaciones de un usuario"""
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return "**Uso:** `/conversations [user_id]`\n\nEjemplo: `/conversations 123456789`"
        
        target_user_id = parts[1]
        
        try:
            history = self.conversation_store.get_conversation_history(target_user_id, limit=20)
            
            if not history:
                return f"❌ No se encontraron conversaciones para: `{target_user_id}`"
            
            result = f"💬 **Últimos {len(history)} mensajes de {target_user_id}:**\n\n"
            for msg in history[-10:]:  # Últimos 10
                role = msg.get("role", "unknown")
                content = msg.get("message", "")[:100]
                timestamp = msg.get("timestamp", "N/A")
                result += f"**{role}** ({timestamp}):\n{content}...\n\n"
            
            return result
        
        except Exception as e:
            return f"❌ **Error al obtener conversaciones:**\n{str(e)}"
    
    def _cmd_error(self, user_id: str, message: str) -> str:
        """Analizar error en una conversación"""
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return (
                "**Uso:** `/error [conversation_id]`\n\n"
                "Analiza los últimos mensajes de una conversación para identificar errores."
            )
        
        conversation_id = parts[1]
        
        return (
            f"🔍 **Análisis de conversación:** `{conversation_id}`\n\n"
            f"Funcionalidad en desarrollo.\n"
            f"Por ahora, usa `/conversations [user_id]` para revisar manualmente."
        )
    
    def _cmd_fix(self, user_id: str, message: str) -> str:
        """Aplicar corrección descrita"""
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return (
                "**Uso:** `/fix [descripción]`\n\n"
                "Ejemplo: `/fix actualizar precio de motos a 10000`"
            )
        
        fix_description = parts[1]
        
        # Análisis simple de la descripción
        if "precio" in fix_description.lower():
            return (
                "💡 **Sugerencia de corrección:**\n\n"
                "Parece que quieres actualizar precios. Usa:\n"
                "`/edit precios-batuco tarifa-moto 10000`"
            )
        
        return (
            f"🤖 **Fix solicitado:** {fix_description}\n\n"
            "Funcionalidad de auto-corrección en desarrollo.\n"
            "Por ahora, usa los comandos específicos."
        )
    
    def _analyze_natural_request(self, user_id: str, message: str) -> str:
        """Analiza solicitudes en lenguaje natural"""
        msg_lower = message.lower()
        
        # Detección de intenciones comunes
        if any(word in msg_lower for word in ["precio", "tarifa", "costo"]):
            return (
                "💡 Parece que necesitas ajustar precios.\n\n"
                "Usa: `/view prompts` para ver la info de precios actual\n"
                "Luego: `/edit [id] [campo] [valor]` para actualizar"
            )
        
        if any(word in msg_lower for word in ["fecha libre", "domingo", "horario"]):
            return (
                "💡 Para gestionar Fechas Libres:\n\n"
                "`/view fechas-libres` - Ver fechas activas\n"
                "Luego edita la variable `ACTIVE_FECHA_LIBRE_DATES` en Railway"
            )
        
        if any(word in msg_lower for word in ["error", "problema", "bug"]):
            return (
                "💡 Para analizar errores:\n\n"
                "`/conversations [user_id]` - Ver conversación con problema\n"
                "`/search [texto_error]` - Buscar en base de datos"
            )
        
        # Respuesta genérica
        return (
            "🤖 Estoy en modo desarrollador.\n\n"
            "Usa `/view [categoria]` para explorar datos\n"
            "o describe más específicamente qué necesitas corregir."
        )


# Instancia global
_admin_mode_instance = None

def get_admin_mode() -> AdminMode:
    """Obtiene o crea la instancia del modo admin"""
    global _admin_mode_instance
    if _admin_mode_instance is None:
        _admin_mode_instance = AdminMode()
    return _admin_mode_instance
