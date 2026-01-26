"""
Pequeño demo para usar el contenedor 'Memoria' (precios, hechos, resúmenes).

Uso:
  python scripts/cosmos_memoria_demo.py
"""
from cosmos_client import get_memory_store


def main():
    store = get_memory_store()

    # Upsert precio
    store.upsert_price(product="degustacion", price=15000, currency="CLP", source="manual")
    precio = store.get_price("degustacion")
    print("Precio degustacion:", precio)

    # Upsert hecho
    store.upsert_fact(key="horario_domingo", value="10:00-18:00", scope="global", tags=["horarios"])
    fact = store.get_fact(key="horario_domingo", scope="global")
    print("Hecho horario_domingo:", fact)

    # Guardar resumen de conversación
    store.save_conversation_summary(
        user_id="user_123",
        conversation_id="conv_demo_1",
        summary="Usuario preguntó por precios y horarios, se coordinó visita.",
        topics=["precios", "horarios", "visitas"],
        score=0.92,
    )
    summaries = store.get_conversation_summaries(user_id="user_123", limit=5)
    print("Ultimos resúmenes:", summaries)


if __name__ == "__main__":
    main()
