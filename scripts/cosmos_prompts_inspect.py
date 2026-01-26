"""
Utility to inspect prompts stored in Azure Cosmos DB.

Reads endpoint/key from config (loads .env). Allows filtering by persona/type/status
for the Entrenamiento/Biblioteca container, or generic filters for any DB/container.

Safety: read-only queries; does not mutate data.
"""
from __future__ import annotations

import argparse
from typing import Any, Dict, List

import config


def _connect(database: str, container: str):
    try:
        from azure.cosmos import CosmosClient
    except Exception as e:
        raise SystemExit(
            "Missing dependency 'azure-cosmos'. Install with: pip install azure-cosmos"
        ) from e

    if not (config.COSMOS_ENDPOINT and config.COSMOS_KEY):
        raise SystemExit(
            "COSMOS_ENDPOINT/COSMOS_KEY are not set. Ensure .env is configured."
        )

    client = CosmosClient(config.COSMOS_ENDPOINT, config.COSMOS_KEY)
    db = client.get_database_client(database)
    cont = db.get_container_client(container)
    return cont


def _build_query(args: argparse.Namespace) -> tuple[str, List[Dict[str, Any]]]:
    select = (
        "SELECT c.id, c.persona, c.userId, c.type, c.version, c.status, c.updatedAt, "
        "(IS_DEFINED(c.content) ? LENGTH(c.content) : 0) AS contentLen"
    )
    from_c = " FROM c"

    where = []
    params: List[Dict[str, Any]] = []

    def add_param(name: str, value: Any):
        params.append({"name": name, "value": value})

    if args.persona:
        where.append("c.persona = @persona")
        add_param("@persona", args.persona)
    if args.user_id:
        where.append("c.userId = @userId")
        add_param("@userId", args.user_id)
    if args.type:
        where.append("c.type = @type")
        add_param("@type", args.type)
    if args.status:
        where.append("c.status = @status")
        add_param("@status", args.status)
    if args.id_contains:
        where.append("CONTAINS(LOWER(c.id), @idContains)")
        add_param("@idContains", args.id_contains.lower())

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    order = " ORDER BY IS_DEFINED(c.updatedAt) DESC, c.updatedAt DESC, c.version DESC"
    limit = f" OFFSET 0 LIMIT {int(args.limit)}" if args.limit else ""

    query = select + from_c + where_sql + order + limit
    return query, params


def run(args: argparse.Namespace) -> int:
    cont = _connect(args.db, args.container)

    query, params = _build_query(args)
    items = list(
        cont.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True,
        )
    )

    if not items:
        print("No items matched the filters.")
        return 0

    print(f"Found {len(items)} item(s):\n")
    for it in items:
        pid = it.get("id")
        persona = it.get("persona") or it.get("userId")
        typ = it.get("type")
        ver = it.get("version")
        st = it.get("status")
        ua = it.get("updatedAt")
        clen = it.get("contentLen")
        print(
            f"- id={pid} | persona={persona} | type={typ} | version={ver} | status={st} | updatedAt={ua} | contentLen={clen}"
        )

    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Inspect prompts stored in Cosmos DB.")
    p.add_argument("--db", required=True, help="Cosmos database name (e.g., Entrenamiento)")
    p.add_argument("--container", required=True, help="Cosmos container name (e.g., Biblioteca)")
    p.add_argument("--persona", help="Filter by persona (e.g., Hernando)")
    p.add_argument("--user-id", dest="user_id", help="Filter by userId (e.g., __prompts__)")
    p.add_argument("--type", choices=["system", "operational", "faq", "tools", "pointer", "persona"], help="Filter by type")
    p.add_argument("--status", choices=["active", "draft", "archived"], help="Filter by status")
    p.add_argument("--id-contains", help="Filter where id contains this substring (case-insensitive)")
    p.add_argument("--limit", type=int, default=50, help="Max items to return (default 50)")

    args = p.parse_args()
    try:
        return run(args)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
