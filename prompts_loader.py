"""
Cargador dinámico de prompts desde Azure Cosmos DB.

Soporta leer prompts personalizados desde la DB "Entrenamiento", contenedor "Hernando"
con caché en memoria y fallback automático a prompts embebidos.

Uso:
    loader = get_prompts_loader()
    prompts = loader.get_prompts(persona="Hernando", fallback_system_prompt=..., fallback_operational_prompt=...)
    system_prompt = prompts["system"]
    operational_prompt = prompts["operational"]
"""

from __future__ import annotations

from typing import Dict, Optional, Any
from datetime import datetime, timedelta, timezone
import config


class PromptsLoader:
    """Carga prompts desde Cosmos DB con caché y fallback."""

    def __init__(self):
        """Inicializa el loader. No hace conexión hasta la primera llamada."""
        self._cache: Dict[str, Any] = {}
        self._cache_ttl_minutes = 60
        self._last_cache_time: Optional[datetime] = None
        self._cosmos_unavailable_until: Optional[datetime] = None

    def _is_cosmos_temporarily_unavailable(self) -> bool:
        """Verifica si Cosmos fue marcado como no disponible recientemente."""
        if not self._cosmos_unavailable_until:
            return False
        if datetime.now() < self._cosmos_unavailable_until:
            return True
        # Limpiar flag; reintentar conexión
        self._cosmos_unavailable_until = None
        return False

    def _mark_cosmos_unavailable(self, backoff_minutes: int = 5):
        """Marca Cosmos como no disponible por N minutos para evitar golpeteo."""
        self._cosmos_unavailable_until = datetime.now() + timedelta(minutes=backoff_minutes)
        print(f"⚠️ Cosmos DB marcado como no disponible por {backoff_minutes} min; usando caché/fallback.")

    def _connect(self):
        """Conecta a Cosmos DB si está configurado."""
        if not (config.COSMOS_ENDPOINT and config.COSMOS_KEY):
            raise RuntimeError("COSMOS_ENDPOINT/COSMOS_KEY no configurados")
        try:
            from azure.cosmos import CosmosClient
        except Exception as e:
            raise RuntimeError("Falta dependencia 'azure-cosmos'") from e

        return CosmosClient(config.COSMOS_ENDPOINT, config.COSMOS_KEY)

    def _fetch_from_cosmos(
        self,
        persona: str,
        db_name: str = "Entrenamiento",
        container_name: str = "Hernando",
    ) -> Dict[str, Any]:
        """
        Obtiene personalidad, operativo y tools desde Cosmos DB.

        Args:
            persona: nombre de la persona (ej. "Hernando")
            db_name: nombre de la base de datos
            container_name: nombre del contenedor

        Returns:
            Dict con "system", "operational" (strings) y "tools" (list)

        Raises:
            Si hay error en conexión o query.
        """
        try:
            client = self._connect()
            db = client.get_database_client(db_name)
            cont = db.get_container_client(container_name)

            # Query: obtener personalidad, operativo y tools
            query = """
                SELECT c.type, c.content, c.tools
                FROM c
                WHERE c.Categoria = @persona AND c.status = @status
                ORDER BY c.version DESC
            """
            parameters = [
                {"name": "@persona", "value": persona},
                {"name": "@status", "value": "active"},
            ]

            items = list(
                cont.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key=persona,
                    enable_cross_partition_query=False,
                )
            )

            if not items:
                raise RuntimeError(f"No active items found for {persona}")

            result: Dict[str, Any] = {}
            for item in items:
                item_type = item.get("type", "").lower()
                if item_type == "personalidad":
                    result["system"] = (item.get("content") or "").strip()
                elif item_type == "operativo":
                    result["operational"] = (item.get("content") or "").strip()
                elif item_type == "tools":
                    result["tools"] = item.get("tools") or []

            if "system" not in result or "operational" not in result:
                raise RuntimeError(f"Incomplete prompts for {persona}")

            if "tools" not in result:
                result["tools"] = []

            return result

        except Exception as e:
            raise RuntimeError(f"Error fetching prompts from Cosmos: {e}") from e

    def update_prompt(
        self,
        *,
        persona: str,
        prompt_type: str,
        new_text: str,
        db_name: Optional[str] = None,
        container_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Actualiza el contenido del prompt (personalidad/operativo) en Cosmos.
        """
        normalized = (prompt_type or "").strip().lower()
        if normalized in ("system", "personalidad", "persona"):
            normalized = "personalidad"
        elif normalized in ("operational", "operativo", "ops"):
            normalized = "operativo"

        if normalized not in ("personalidad", "operativo"):
            raise ValueError("prompt_type debe ser 'personalidad' o 'operativo'")

        client = self._connect()
        _db_name = db_name or config.COSMOS_PROMPTS_DB
        _container_name = container_name or config.COSMOS_PROMPTS_CONTAINER
        db = client.get_database_client(_db_name)
        cont = db.get_container_client(_container_name)

        query = """
            SELECT TOP 1 * FROM c
            WHERE c.Categoria = @persona AND c.type = @type
            ORDER BY c.version DESC
        """
        params = [
            {"name": "@persona", "value": persona},
            {"name": "@type", "value": normalized},
        ]
        items = list(
            cont.query_items(
                query=query,
                parameters=params,
                partition_key=persona,
                enable_cross_partition_query=False,
            )
        )
        if not items:
            raise RuntimeError(f"No se encontró prompt tipo '{normalized}' para {persona}")

        item = items[0]
        item["content"] = new_text
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        item["status"] = "active"
        try:
            item["version"] = int(item.get("version") or 0) + 1
        except Exception:
            item["version"] = 1

        updated = cont.upsert_item(item)
        self.clear_cache()
        return updated

    def _is_cache_valid(self) -> bool:
        """Verifica si el caché sigue siendo válido."""
        if not self._cache or not self._last_cache_time:
            return False
        elapsed = (datetime.now() - self._last_cache_time).total_seconds() / 60
        return elapsed < self._cache_ttl_minutes

    def get_prompts(
        self,
        persona: str = "Hernando",
        fallback_system_prompt: Optional[str] = None,
        fallback_operational_prompt: Optional[str] = None,
        fallback_tools: Optional[list] = None,
        use_cache: bool = True,
        db_name: Optional[str] = None,
        container_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene prompts (system + operational) y tools para una persona.

        Intenta leer de Cosmos DB con caché; si falla, usa fallback embebido.

        Args:
            persona: nombre de la persona (default: "Hernando")
            fallback_system_prompt: prompt embebido para fallback (system)
            fallback_operational_prompt: prompt embebido para fallback (operational)
            fallback_tools: tools embebidas para fallback (opcional)
            use_cache: usar caché en memoria (default: True)
            db_name: DB de Cosmos (opcional)
            container_name: contenedor de Cosmos (opcional)

        Returns:
            Dict: {"system": "...", "operational": "...", "tools": [...]} 
        """
        # 1. Intentar caché
        if use_cache and self._is_cache_valid():
            print(f"📦 Prompts para '{persona}' obtenidos del caché")
            return self._cache

        # 2. Si Cosmos está marcado como no disponible, saltar directo a fallback
        if self._is_cosmos_temporarily_unavailable():
            print(f"⏭️ Cosmos marcado como no disponible; usando fallback para '{persona}'")
            return self._build_fallback(fallback_system_prompt, fallback_operational_prompt, fallback_tools)

        # 3. Intentar fetch desde Cosmos DB
        try:
            # Usar defaults de config si no se especifican
            _db_name = db_name or config.COSMOS_PROMPTS_DB
            _container_name = container_name or config.COSMOS_PROMPTS_CONTAINER
            prompts = self._fetch_from_cosmos(persona, _db_name, _container_name)
            self._cache = prompts
            self._last_cache_time = datetime.now()
            print(f"✅ Prompts para '{persona}' cargados desde Cosmos DB")
            return prompts

        except Exception as e:
            print(f"❌ Error leyendo desde Cosmos: {e}")
            self._mark_cosmos_unavailable(backoff_minutes=5)
            return self._build_fallback(fallback_system_prompt, fallback_operational_prompt, fallback_tools)

    def _build_fallback(
        self,
        fallback_system_prompt: Optional[str] = None,
        fallback_operational_prompt: Optional[str] = None,
        fallback_tools: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Construye dict de fallback con prompts y tools embebidos."""
        return {
            "system": fallback_system_prompt or "Eres un asistente útil.",
            "operational": fallback_operational_prompt or "Responde de forma clara y concisa.",
            "tools": fallback_tools or [],
        }

    def clear_cache(self):
        """Limpia el caché en memoria (útil para forzar recarga de Cosmos)."""
        self._cache.clear()
        self._last_cache_time = None
        print("🗑️ Caché de prompts limpiado")


# Singleton instance
_prompts_loader: Optional[PromptsLoader] = None


def get_prompts_loader() -> PromptsLoader:
    """Obtiene la instancia singleton del cargador de prompts."""
    global _prompts_loader
    if _prompts_loader is None:
        _prompts_loader = PromptsLoader()
    return _prompts_loader
