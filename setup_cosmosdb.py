"""
Script para crear automáticamente la base de datos y contenedor en Cosmos DB
"""
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import config


def setup_cosmos_db():
    """Crea la base de datos y contenedor si no existen"""
    print("\n🔧 Configurando Azure Cosmos DB...")
    
    try:
        # Validar configuración
        config.validate_config()
        
        # Crear cliente
        client = CosmosClient(config.COSMOS_ENDPOINT, config.COSMOS_KEY)
        print(f"✅ Conectado a: {config.COSMOS_ENDPOINT}")
        
        # Crear base de datos si no existe
        print(f"\n📊 Verificando base de datos '{config.COSMOS_DATABASE}'...")
        try:
            database = client.create_database(config.COSMOS_DATABASE)
            print(f"✅ Base de datos '{config.COSMOS_DATABASE}' creada")
        except exceptions.CosmosResourceExistsError:
            database = client.get_database_client(config.COSMOS_DATABASE)
            print(f"✅ Base de datos '{config.COSMOS_DATABASE}' ya existe")
        
        # Crear contenedor si no existe
        print(f"\n📦 Verificando contenedor '{config.COSMOS_CONTAINER}'...")
        try:
            container = database.create_container(
                id=config.COSMOS_CONTAINER,
                partition_key=PartitionKey(path="/userId"),
                offer_throughput=None  # None = serverless
            )
            print(f"✅ Contenedor '{config.COSMOS_CONTAINER}' creado")
            print(f"   Partition Key: /userId")
        except exceptions.CosmosResourceExistsError:
            container = database.get_container_client(config.COSMOS_CONTAINER)
            print(f"✅ Contenedor '{config.COSMOS_CONTAINER}' ya existe")
        
        # Verificar que todo funciona guardando un documento de prueba
        print(f"\n🧪 Probando escritura en Cosmos DB...")
        test_doc = {
            "id": "setup_test_001",
            "userId": "setup_test",
            "message": "Test de configuración",
            "timestamp": "2025-12-15T00:00:00Z"
        }
        
        container.upsert_item(test_doc)
        print("✅ Escritura exitosa")
        
        # Leer el documento
        read_doc = container.read_item(
            item="setup_test_001",
            partition_key="setup_test"
        )
        print("✅ Lectura exitosa")
        
        # Eliminar documento de prueba
        container.delete_item(
            item="setup_test_001",
            partition_key="setup_test"
        )
        print("✅ Eliminación exitosa")
        
        print("\n" + "="*60)
        print("🎉 ¡Cosmos DB configurado correctamente!")
        print("="*60)
        print(f"\n📍 Base de datos: {config.COSMOS_DATABASE}")
        print(f"📦 Contenedor: {config.COSMOS_CONTAINER}")
        print(f"🔑 Partition Key: /userId")
        print("\n✅ Ya puedes ejecutar el bot con: python instagram_bot.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error configurando Cosmos DB:")
        print(f"   {e}")
        return False


if __name__ == "__main__":
    import sys
    success = setup_cosmos_db()
    sys.exit(0 if success else 1)
