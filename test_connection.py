"""
Script para probar la conexión a Cosmos DB
Útil para verificar que todo esté configurado correctamente
"""
import sys
from config import validate_config
from cosmos_client import get_conversation_store


def test_cosmos_connection():
    """Prueba la conexión a Cosmos DB"""
    print("\n🔍 Verificando configuración...")
    
    try:
        # Validar variables de entorno
        validate_config()
        print("✅ Variables de entorno configuradas correctamente")
    except ValueError as e:
        print(f"❌ {e}")
        return False
    
    print("\n🔗 Conectando a Azure Cosmos DB...")
    
    try:
        # Obtener cliente
        store = get_conversation_store()
        
        # Probar guardando un mensaje de prueba
        test_user_id = "test_user_connection"
        test_message = store.save_message(
            user_id=test_user_id,
            role="user",
            message="Mensaje de prueba de conexión",
            conversation_id="test_conv_001",
            metadata={"test": True}
        )
        
        print(f"✅ Mensaje de prueba guardado con ID: {test_message['id']}")
        
        # Probar recuperando el historial
        history = store.get_conversation_history(test_user_id, limit=1)
        
        if history:
            print(f"✅ Historial recuperado: {len(history)} mensaje(s)")
            print(f"   Último mensaje: {history[-1]['message']}")
        
        print("\n✅ ¡Conexión a Cosmos DB exitosa!")
        print("   Ya puedes ejecutar el bot con: python instagram_bot.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error conectando a Cosmos DB:")
        print(f"   {e}")
        print("\n💡 Verifica:")
        print("   1. Que COSMOS_ENDPOINT sea correcto")
        print("   2. Que COSMOS_KEY sea válido")
        print("   3. Que la base de datos 'chatbot' y contenedor 'conversations' existan")
        return False


if __name__ == "__main__":
    success = test_cosmos_connection()
    sys.exit(0 if success else 1)
