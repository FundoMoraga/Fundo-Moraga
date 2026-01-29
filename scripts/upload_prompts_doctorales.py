"""
Script para subir prompts doctorales a Cosmos DB.

Este script lee todos los archivos JSON de la carpeta prompts_doctorales/
y los sube al container "Hernando" en la base de datos "Entrenamiento" de Cosmos DB.

Estructura esperada en Cosmos DB:
- Database: Entrenamiento
- Container: Hernando
- Partition Key: /persona

Ejecutar desde raíz del proyecto:
    python scripts/upload_prompts_doctorales.py
"""

import json
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cosmos_client as cosmos_module
from config import COSMOS_ENDPOINT, COSMOS_KEY


def cargar_prompts_desde_archivos(directorio="prompts_doctorales"):
    """
    Carga todos los archivos JSON del directorio de prompts doctorales.
    
    Returns:
        list: Lista de diccionarios con el contenido de cada archivo JSON
    """
    prompts = []
    directorio_path = Path(directorio)
    
    if not directorio_path.exists():
        print(f"❌ Error: El directorio {directorio} no existe")
        return prompts
    
    # Buscar todos los archivos .json
    archivos_json = list(directorio_path.glob("*.json"))
    
    if not archivos_json:
        print(f"⚠️  Advertencia: No se encontraron archivos JSON en {directorio}")
        return prompts
    
    print(f"📁 Encontrados {len(archivos_json)} archivos JSON en {directorio}/")
    
    for archivo in archivos_json:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = json.load(f)
                prompts.append(contenido)
                print(f"   ✓ Cargado: {archivo.name}")
        except json.JSONDecodeError as e:
            print(f"   ❌ Error JSON en {archivo.name}: {e}")
        except Exception as e:
            print(f"   ❌ Error leyendo {archivo.name}: {e}")
    
    return prompts


def validar_estructura_prompt(prompt_data):
    """
    Valida que el prompt tenga la estructura mínima requerida.
    
    Args:
        prompt_data (dict): Datos del prompt a validar
        
    Returns:
        tuple: (bool válido, str mensaje_error)
    """
    campos_requeridos = ["id", "persona"]
    
    for campo in campos_requeridos:
        if campo not in prompt_data:
            return False, f"Falta campo requerido: {campo}"
    
    # Validar que persona sea efrain_moraga o relacionado
    if not prompt_data["persona"].startswith("efrain_moraga"):
        return False, f"Persona debe comenzar con 'efrain_moraga', encontrado: {prompt_data['persona']}"
    
    return True, "OK"


def subir_prompts_a_cosmos(prompts):
    """
    Sube los prompts a Cosmos DB.
    
    Args:
        prompts (list): Lista de prompts a subir
        
    Returns:
        tuple: (int exitosos, int fallidos)
    """
    if not prompts:
        print("⚠️  No hay prompts para subir")
        return 0, 0
    
    print(f"\n🔄 Conectando a Cosmos DB...")
    print(f"   Endpoint: {COSMOS_ENDPOINT}")
    
    try:
        # Inicializar cliente Cosmos usando la misma configuración del proyecto
        client = cosmos_module._create_cosmos_client()
        database = client.get_database_client("Entrenamiento")
        container = database.get_container_client("Hernando")
        
        exitosos = 0
        fallidos = 0
        
        print(f"\n📤 Subiendo {len(prompts)} prompts a Cosmos DB...\n")
        
        for prompt in prompts:
            # Validar estructura
            valido, mensaje = validar_estructura_prompt(prompt)
            if not valido:
                print(f"   ❌ {prompt.get('id', 'SIN_ID')}: {mensaje}")
                fallidos += 1
                continue
            
            try:
                # Upsert: crea si no existe, actualiza si existe
                container.upsert_item(prompt)
                print(f"   ✓ {prompt['id']}")
                exitosos += 1
                
            except Exception as e:
                print(f"   ❌ {prompt['id']}: {str(e)}")
                fallidos += 1
        
        print(f"\n" + "="*60)
        print(f"✅ Exitosos: {exitosos}")
        if fallidos > 0:
            print(f"❌ Fallidos: {fallidos}")
        print("="*60 + "\n")
        
        return exitosos, fallidos
        
    except Exception as e:
        print(f"❌ Error crítico conectando a Cosmos DB: {e}")
        return 0, len(prompts)


def listar_prompts_en_cosmos():
    """
    Lista todos los prompts doctorales actualmente en Cosmos DB.
    """
    print("\n📋 Listando prompts doctorales en Cosmos DB...\n")
    
    try:
        client = cosmos_module._create_cosmos_client()
        database = client.get_database_client("Entrenamiento")
        container = database.get_container_client("Hernando")
        
        # Query para obtener prompts de Efraín
        query = "SELECT c.id, c.persona, c.area, c.nivel FROM c WHERE STARTSWITH(c.persona, 'efrain_moraga')"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            print("   (No se encontraron prompts doctorales en Cosmos DB)")
            return
        
        print(f"   Encontrados {len(items)} prompts:\n")
        for item in items:
            area = item.get('area', 'base')
            nivel = item.get('nivel', 'N/A')
            print(f"   • {item['id']}")
            print(f"     Persona: {item['persona']}")
            if area != 'base':
                print(f"     Área: {area}")
            print(f"     Nivel: {nivel}")
            print()
        
    except Exception as e:
        print(f"❌ Error listando prompts: {e}")


def main():
    """Función principal del script."""
    print("\n" + "="*60)
    print("  UPLOAD DE PROMPTS DOCTORALES A COSMOS DB")
    print("="*60 + "\n")
    
    # 1. Cargar prompts desde archivos
    prompts = cargar_prompts_desde_archivos()
    
    if not prompts:
        print("\n❌ No se cargaron prompts. Abortando.")
        sys.exit(1)
    
    # 2. Confirmar con usuario
    print(f"\n⚠️  Se subirán {len(prompts)} prompts a Cosmos DB (Base: Entrenamiento, Container: Hernando)")
    respuesta = input("¿Continuar? (s/n): ").lower().strip()
    
    if respuesta != 's':
        print("\n❌ Operación cancelada por el usuario.")
        sys.exit(0)
    
    # 3. Subir a Cosmos DB
    exitosos, fallidos = subir_prompts_a_cosmos(prompts)
    
    # 4. Listar prompts en Cosmos DB
    if exitosos > 0:
        listar_prompts_en_cosmos()
    
    # 5. Resultado final
    if fallidos == 0:
        print("✅ Todos los prompts se subieron exitosamente!")
        sys.exit(0)
    else:
        print(f"⚠️  Algunos prompts fallaron ({fallidos}/{len(prompts)})")
        sys.exit(1)


if __name__ == "__main__":
    main()
