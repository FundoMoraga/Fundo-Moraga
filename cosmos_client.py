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
            print("[ConversationStore] Intentando conectar a Cosmos DB...")
            self.client = _create_cosmos_client()
            
            # Obtener database y container
            print(f"[ConversationStore] Accediendo a database: {config.COSMOS_DATABASE}")
            self.database = self.client.get_database_client(config.COSMOS_DATABASE)
            print(f"[ConversationStore] Accediendo a container: {config.COSMOS_CONTAINER}")
            self.container = self.database.get_container_client(config.COSMOS_CONTAINER)
            
            print(f"[ConversationStore] ✅ Conectado exitosamente a Cosmos DB: {config.COSMOS_DATABASE}/{config.COSMOS_CONTAINER}")
            
        except Exception as e:
            print(f"[ConversationStore] ❌ Error conectando a Cosmos DB: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
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


def _create_cosmos_client() -> CosmosClient:
    """Crea un CosmosClient soportando connection string o endpoint+key."""
    cs = getattr(config, "COSMOS_CONNECTION_STRING", None)
    if cs:
        print("[_create_cosmos_client] Usando COSMOS_CONNECTION_STRING para conectar")
        try:
            return CosmosClient.from_connection_string(cs)
        except Exception as e:
            print(f"[_create_cosmos_client] ❌ Error con connection string: {type(e).__name__}: {str(e)}")
            raise
    
    endpoint = getattr(config, "COSMOS_ENDPOINT", None)
    key = getattr(config, "COSMOS_KEY", None)
    
    if not endpoint:
        raise RuntimeError("[_create_cosmos_client] ❌ COSMOS_ENDPOINT no configurado")
    if not key:
        raise RuntimeError("[_create_cosmos_client] ❌ COSMOS_KEY no configurado")
    
    print(f"[_create_cosmos_client] Usando COSMOS_ENDPOINT={endpoint} + COSMOS_KEY para conectar")
    try:
        return CosmosClient(endpoint, credential=key)
    except Exception as e:
        print(f"[_create_cosmos_client] ❌ Error con endpoint+key: {type(e).__name__}: {str(e)}")
        raise


class MemoryStore:
    """Almacenamiento de 'Memoria' (precios, hechos, resúmenes) en Cosmos DB"""

    def __init__(self):
        try:
            print("[MemoryStore] Intentando conectar a Cosmos DB...")
            self.client = _create_cosmos_client()
            print(f"[MemoryStore] Accediendo a database: {config.COSMOS_DATABASE}")
            self.database = self.client.get_database_client(config.COSMOS_DATABASE)
            print(f"[MemoryStore] Accediendo a container: {config.COSMOS_MEMORY_CONTAINER}")
            self.container = self.database.get_container_client(config.COSMOS_MEMORY_CONTAINER)
            self._pk_field = (config.COSMOS_MEMORY_PK_PATH or "/Categoria").lstrip("/")
            print(f"[MemoryStore] ✅ Conectado exitosamente a Cosmos DB Memoria: {config.COSMOS_DATABASE}/{config.COSMOS_MEMORY_CONTAINER}")
        except Exception as e:
            print(f"[MemoryStore] ❌ Error conectando a Cosmos DB (Memoria): {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def upsert_item(self, item: Dict) -> Dict:
        """Guarda o actualiza un documento genérico"""
        try:
            return self.container.upsert_item(item)
        except Exception as e:
            print(f"⚠️ Error en upsert_item: {e}")
            raise

    def query_items(self, query: str, limit: int = 100) -> List[Dict]:
        """Ejecuta una consulta genérica contra el contenedor"""
        try:
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True,
            ))
            return items[:limit] if limit else items
        except Exception as e:
            print(f"⚠️ Error en query_items: {e}")
            return []

    def _with_pk(self, doc: Dict, pk_value: str) -> Dict:
        doc[self._pk_field] = pk_value
        return doc

    # --------- Precios ---------
    def upsert_price(self, *, product: str, price: float, currency: str = "CLP", source: str | None = None,
                     effective_from: Optional[str] = None, tags: Optional[list[str]] = None) -> Dict:
        """Guarda/actualiza el precio de un producto."""
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": f"price:{product}",
            "type": "price",
            "product": product,
            "price": price,
            "currency": currency,
            "source": source,
            "effective_from": effective_from or now_iso,
            "updated_at": now_iso,
            "tags": tags or [],
        }
        doc = self._with_pk(doc, "price")
        return self.container.upsert_item(doc)

    def get_price(self, product: str) -> Optional[Dict]:
        try:
            query = """
                SELECT TOP 1 * FROM c
                WHERE c.{pk} = @categoria AND c.type = @type AND c.id = @id
                ORDER BY c.updated_at DESC
            """.replace("{pk}", self._pk_field)
            params = [
                {"name": "@categoria", "value": "price"},
                {"name": "@type", "value": "price"},
                {"name": "@id", "value": f"price:{product}"},
            ]
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True,
            ))
            return items[0] if items else None
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error consultando precio: {e.message}")
            return None

    # --------- Hechos (facts) ---------
    def upsert_fact(self, *, key: str, value: Any, scope: str = "global", tags: Optional[list[str]] = None,
                    expires_at: Optional[str] = None) -> Dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": f"fact:{scope}:{key}",
            "type": "fact",
            "scope": scope,
            "key": key,
            "value": value,
            "updated_at": now_iso,
            "expires_at": expires_at,
            "tags": tags or [],
        }
        doc = self._with_pk(doc, "fact")
        return self.container.upsert_item(doc)

    def get_fact(self, *, key: str, scope: str = "global") -> Optional[Dict]:
        try:
            query = """
                SELECT TOP 1 * FROM c
                WHERE c.{pk} = @categoria AND c.type = @type AND c.id = @id
            """.replace("{pk}", self._pk_field)
            params = [
                {"name": "@categoria", "value": "fact"},
                {"name": "@type", "value": "fact"},
                {"name": "@id", "value": f"fact:{scope}:{key}"},
            ]
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True,
            ))
            return items[0] if items else None
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error consultando hecho: {e.message}")
            return None

    def list_facts(self, *, scope: Optional[str] = None, limit: int = 20) -> List[Dict]:
        try:
            if scope:
                query = """
                    SELECT * FROM c
                    WHERE c.{pk} = @categoria AND c.type = @type AND c.scope = @scope
                    ORDER BY c.updated_at DESC OFFSET 0 LIMIT @limit
                """.replace("{pk}", self._pk_field)
                params = [
                    {"name": "@categoria", "value": "fact"},
                    {"name": "@type", "value": "fact"},
                    {"name": "@scope", "value": scope},
                    {"name": "@limit", "value": limit},
                ]
            else:
                query = """
                    SELECT * FROM c
                    WHERE c.{pk} = @categoria AND c.type = @type
                    ORDER BY c.updated_at DESC OFFSET 0 LIMIT @limit
                """.replace("{pk}", self._pk_field)
                params = [
                    {"name": "@categoria", "value": "fact"},
                    {"name": "@type", "value": "fact"},
                    {"name": "@limit", "value": limit},
                ]
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True,
                )
            )
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error listando hechos: {e.message}")
            return []

    def list_prices(self, *, limit: int = 20) -> List[Dict]:
        try:
            query = """
                SELECT * FROM c
                WHERE c.{pk} = @categoria AND c.type = @type
                ORDER BY c.updated_at DESC OFFSET 0 LIMIT @limit
            """.replace("{pk}", self._pk_field)
            params = [
                {"name": "@categoria", "value": "price"},
                {"name": "@type", "value": "price"},
                {"name": "@limit", "value": limit},
            ]
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True,
                )
            )
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error listando precios: {e.message}")
            return []

    # --------- Resúmenes de conversación ---------
    def save_conversation_summary(self, *, user_id: str, conversation_id: str, summary: str,
                                  topics: Optional[list[str]] = None, score: Optional[float] = None) -> Dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": f"summary:{conversation_id}",
            "type": "conversation_summary",
            "userId": user_id,
            "conversationId": conversation_id,
            "summary": summary,
            "topics": topics or [],
            "score": score,
            "created_at": now_iso,
        }
        doc = self._with_pk(doc, "summary")
        return self.container.upsert_item(doc)

    def get_conversation_summaries(self, *, user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        try:
            if user_id:
                query = """
                    SELECT * FROM c
                    WHERE c.{pk} = @categoria AND c.type = @type AND c.userId = @userId
                    ORDER BY c.created_at DESC OFFSET 0 LIMIT @limit
                """.replace("{pk}", self._pk_field)
                params = [
                    {"name": "@categoria", "value": "summary"},
                    {"name": "@type", "value": "conversation_summary"},
                    {"name": "@userId", "value": user_id},
                    {"name": "@limit", "value": limit},
                ]
            else:
                query = """
                    SELECT * FROM c
                    WHERE c.{pk} = @categoria AND c.type = @type
                    ORDER BY c.created_at DESC OFFSET 0 LIMIT @limit
                """.replace("{pk}", self._pk_field)
                params = [
                    {"name": "@categoria", "value": "summary"},
                    {"name": "@type", "value": "conversation_summary"},
                    {"name": "@limit", "value": limit},
                ]
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True,
            ))
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"❌ Error consultando resúmenes: {e.message}")
            return []


_memory_store = None

def get_memory_store() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
