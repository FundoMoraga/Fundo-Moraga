"""
Cliente de Azure Cosmos DB para gestionar conversaciones del chatbot
Siguiendo las mejores prácticas de Azure Cosmos DB
"""
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
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

    def create_booking_reminder(
        self,
        *,
        user_id: str,
        conversation_id: str,
        reminder_at: str,
        email: str,
        booking: Dict[str, Any],
        platform: str = "web",
    ) -> Dict:
        """
        Guarda un recordatorio de reserva para envío diferido.
        Se almacena en una partición dedicada para no interferir con conversaciones.
        """
        try:
            reminder_id = str(uuid.uuid4())
            document = {
                "id": reminder_id,
                "userId": "__reminders__",
                "conversationId": f"reminder_{reminder_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": "system",
                "message": "",
                "metadata": {
                    "type": "booking_reminder",
                    "status": "pending",
                    "reminder_at": reminder_at,
                    "email": email,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "platform": platform,
                    "booking": booking,
                },
                "ttl": -1,
            }
            return self.container.create_item(body=document)
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error guardando recordatorio: {e.message}")
            raise

    def fetch_due_reminders(self, now_iso: str, limit: int = 20) -> List[Dict]:
        """
        Obtiene recordatorios pendientes con fecha <= now_iso.
        """
        try:
            query = """
                SELECT * FROM c
                WHERE c.userId = @partition
                AND c.metadata.type = @type
                AND c.metadata.status = @status
                AND c.metadata.reminder_at <= @now
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@partition", "value": "__reminders__"},
                {"name": "@type", "value": "booking_reminder"},
                {"name": "@status", "value": "pending"},
                {"name": "@now", "value": now_iso},
                {"name": "@limit", "value": limit},
            ]
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key="__reminders__",
                    enable_cross_partition_query=False,
                )
            )
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error obteniendo recordatorios: {e.message}")
            return []

    def update_reminder_status(self, reminder: Dict, *, status: str, error: Optional[str] = None) -> None:
        """
        Actualiza el estado de un recordatorio (pending/sent/error).
        """
        try:
            metadata = reminder.get("metadata") or {}
            metadata["status"] = status
            metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            if status == "sent":
                metadata["sent_at"] = metadata["updated_at"]
            if error:
                metadata["error"] = error
            reminder["metadata"] = metadata
            self.container.upsert_item(body=reminder)
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error actualizando recordatorio: {e.message}")

    def upsert_pending_email(
        self,
        *,
        user_id: str,
        conversation_id: str,
        email_type: str,
        payload: Dict[str, Any],
        platform: str = "web",
        booking_date: Optional[str] = None,
        next_attempt_at: Optional[str] = None,
    ) -> Dict:
        """
        Guarda o actualiza un correo pendiente para reintento.
        """
        try:
            suffix = f"_{booking_date}" if booking_date else ""
            pending_id = f"pending_{conversation_id}_{email_type}{suffix}"
            now_iso = datetime.now(timezone.utc).isoformat()
            document = {
                "id": pending_id,
                "userId": "__pending_emails__",
                "conversationId": f"pending_{pending_id}",
                "timestamp": now_iso,
                "role": "system",
                "message": "",
                "metadata": {
                    "type": "pending_email",
                    "email_type": email_type,
                    "status": "pending",
                    "next_attempt_at": next_attempt_at or now_iso,
                    "attempts": 0,
                    "payload": payload,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "platform": platform,
                    "booking_date": booking_date,
                },
                "ttl": -1,
            }
            return self.container.upsert_item(body=document)
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error guardando correo pendiente: {e.message}")
            raise

    def fetch_due_pending_emails(self, now_iso: str, limit: int = 20) -> List[Dict]:
        """
        Obtiene correos pendientes con fecha <= now_iso.
        """
        try:
            query = """
                SELECT * FROM c
                WHERE c.userId = @partition
                AND c.metadata.type = @type
                AND c.metadata.status = @status
                AND c.metadata.next_attempt_at <= @now
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@partition", "value": "__pending_emails__"},
                {"name": "@type", "value": "pending_email"},
                {"name": "@status", "value": "pending"},
                {"name": "@now", "value": now_iso},
                {"name": "@limit", "value": limit},
            ]
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key="__pending_emails__",
                    enable_cross_partition_query=False,
                )
            )
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error obteniendo correos pendientes: {e.message}")
            return []

    def update_pending_email_status(
        self,
        pending: Dict,
        *,
        status: str,
        error: Optional[str] = None,
        next_attempt_at: Optional[str] = None,
        attempts: Optional[int] = None,
    ) -> None:
        """
        Actualiza el estado de un correo pendiente (pending/sent/error).
        """
        try:
            metadata = pending.get("metadata") or {}
            metadata["status"] = status
            metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            if status == "sent":
                metadata["sent_at"] = metadata["updated_at"]
            if error:
                metadata["error"] = error
            if next_attempt_at:
                metadata["next_attempt_at"] = next_attempt_at
            if attempts is not None:
                metadata["attempts"] = attempts
            pending["metadata"] = metadata
            self.container.upsert_item(body=pending)
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error actualizando correo pendiente: {e.message}")
    
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
