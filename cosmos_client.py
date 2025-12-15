"""
Cliente de Azure Cosmos DB para gestionar conversaciones del chatbot
Siguiendo las mejores prácticas de Azure Cosmos DB
"""
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid
import config


class ConversationStore:
    """Gestiona el almacenamiento de conversaciones en Cosmos DB"""
    
    def __init__(self):
        """Inicializa la conexión a Cosmos DB (singleton pattern)"""
        try:
            # Crear cliente reutilizable (best practice)
            self.client = CosmosClient(
                config.COSMOS_ENDPOINT, 
                config.COSMOS_KEY
            )
            
            # Obtener database y container
            self.database = self.client.get_database_client(config.COSMOS_DATABASE)
            self.container = self.database.get_container_client(config.COSMOS_CONTAINER)
            
            print(f"✅ Conectado a Cosmos DB: {config.COSMOS_DATABASE}/{config.COSMOS_CONTAINER}")
            
        except Exception as e:
            print(f"❌ Error conectando a Cosmos DB: {e}")
            raise
    
    def save_message(
        self, 
        user_id: str, 
        role: str, 
        message: str, 
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Guarda un mensaje en Cosmos DB
        
        Args:
            user_id: ID del usuario de Instagram
            role: 'user' o 'assistant'
            message: Contenido del mensaje
            conversation_id: ID de la conversación (opcional, se genera si no existe)
            metadata: Información adicional (opcional)
        
        Returns:
            El documento creado
        """
        try:
            # Generar IDs si no existen
            if not conversation_id:
                conversation_id = f"conv_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            
            message_id = str(uuid.uuid4())
            
            # Estructura del documento siguiendo best practices
            document = {
                "id": message_id,
                "userId": user_id,  # Partition key para queries rápidas
                "conversationId": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": role,
                "message": message,
                "metadata": metadata or {"platform": "instagram"},
                "ttl": -1  # -1 = no expira, ajustar según necesidades
            }
            
            # Crear item en Cosmos DB
            created_item = self.container.create_item(body=document)
            
            return created_item
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error guardando mensaje: {e.message}")
            raise
    
    def get_conversation_history(
        self, 
        user_id: str, 
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Recupera el historial de conversación de un usuario
        
        Args:
            user_id: ID del usuario de Instagram
            conversation_id: ID de conversación específica (opcional)
            limit: Número máximo de mensajes a recuperar
        
        Returns:
            Lista de mensajes ordenados por timestamp
        """
        try:
            # Query optimizada usando partition key (best practice)
            if conversation_id:
                query = """
                    SELECT * FROM c 
                    WHERE c.userId = @userId 
                    AND c.conversationId = @conversationId
                    ORDER BY c.timestamp DESC
                    OFFSET 0 LIMIT @limit
                """
                parameters = [
                    {"name": "@userId", "value": user_id},
                    {"name": "@conversationId", "value": conversation_id},
                    {"name": "@limit", "value": limit}
                ]
            else:
                # Obtener últimas conversaciones del usuario
                query = """
                    SELECT * FROM c 
                    WHERE c.userId = @userId
                    ORDER BY c.timestamp DESC
                    OFFSET 0 LIMIT @limit
                """
                parameters = [
                    {"name": "@userId", "value": user_id},
                    {"name": "@limit", "value": limit}
                ]
            
            # Ejecutar query con partition key para eficiencia
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id,  # Usa partition key para queries rápidas
                enable_cross_partition_query=False  # False = más eficiente
            ))
            
            # Ordenar cronológicamente (más antiguo primero)
            items.reverse()
            
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error recuperando historial: {e.message}")
            return []
    
    def get_latest_conversation_id(self, user_id: str) -> Optional[str]:
        """
        Obtiene el ID de la conversación más reciente del usuario
        
        Args:
            user_id: ID del usuario de Instagram
        
        Returns:
            ID de la conversación más reciente o None
        """
        try:
            query = """
                SELECT TOP 1 c.conversationId 
                FROM c 
                WHERE c.userId = @userId
                ORDER BY c.timestamp DESC
            """
            parameters = [{"name": "@userId", "value": user_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id,
                enable_cross_partition_query=False
            ))
            
            return items[0]["conversationId"] if items else None
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error obteniendo última conversación: {e.message}")
            return None
    
    def delete_old_conversations(self, user_id: str, days: int = 30):
        """
        Elimina conversaciones antiguas de un usuario
        
        Args:
            user_id: ID del usuario de Instagram
            days: Eliminar conversaciones más antiguas que X días
        """
        try:
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date, timezone.utc).isoformat()
            
            query = """
                SELECT c.id, c.userId FROM c 
                WHERE c.userId = @userId 
                AND c.timestamp < @cutoffDate
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@cutoffDate", "value": cutoff_iso}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id,
                enable_cross_partition_query=False
            ))
            
            # Eliminar items
            for item in items:
                self.container.delete_item(item["id"], partition_key=item["userId"])
            
            print(f"🗑️ Eliminadas {len(items)} conversaciones antiguas de {user_id}")
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error eliminando conversaciones antiguas: {e.message}")
    
    def close(self):
        """Cierra la conexión (opcional, el cliente maneja esto automáticamente)"""
        # En producción, mantén el cliente abierto para reutilización
        pass


# Singleton instance (best practice: reutilizar cliente)
_conversation_store = None

def get_conversation_store() -> ConversationStore:
    """Obtiene la instancia singleton del ConversationStore"""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store
