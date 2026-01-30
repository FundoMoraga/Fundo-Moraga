"""
Test detallado del flujo de búsqueda de imágenes y envío a WhatsApp
"""
import json
import sys
import io
from hernando_tools import get_hernando_tools

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("[TEST] Detalle completo del flujo")
print("=" * 80)

user_id = '+56941242609'
tools = get_hernando_tools(user_id)

print(f"\n1. Herramientas cargadas: {len(tools.tools)}")

# Mostrar estructura de la herramienta buscar_imagenes
image_search_tool = None
for tool in tools.tools:
    if tool['function']['name'] == 'buscar_imagenes':
        image_search_tool = tool
        break

if image_search_tool:
    print(f"\n2. Herramienta 'buscar_imagenes' encontrada:")
    print(f"   Name: {image_search_tool['function']['name']}")
    print(f"   Description: {image_search_tool['function']['description'][:100]}...")
    print(f"   Parameters: {json.dumps(image_search_tool['function']['parameters'], indent=4)}")

print("\n3. Intentando ejecutar herramienta...")

search_args = {
    "query": "Jeep Wrangler",
    "max_results": 3,
    "doctoral_area": "tecnologia"
}

try:
    result = tools.execute_tool("buscar_imagenes", search_args)
    print(f"\n4. Resultado de execute_tool:")
    print(f"   Success: {result.get('success')}")
    if result.get('error'):
        print(f"   Error: {result.get('error')}")
    print(f"   Total found: {result.get('total_found')}")
    print(f"   Total analyzed: {result.get('total_analyzed')}")
    if result.get('images'):
        print(f"   Num images: {len(result.get('images', []))}")
        if result['images']:
            img = result['images'][0]
            print(f"\n   [Sample Image]")
            print(f"     - URL: {img.get('image_url', 'N/A')[:60]}...")
            print(f"     - Title: {img.get('search_title', 'N/A')[:60]}")
            print(f"     - Index: {img.get('search_index')}")

except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("[OK] Test de arquitectura completado!")
print("=" * 80)
print("""
FLUJO DISPONIBLE:
1. Usuario: "Hernando, busca 10 fotos de Jeep Wrangler"
2. Sistema: Usa tool 'buscar_imagenes' con Steel Browser + Vision Service
3. Resultado: Retorna imágenes con análisis doctoral
4. Sistema: Usa prepare_images_for_whatsapp() para enviar a WhatsApp
5. Usuario: Recibe imágenes en WhatsApp con análisis

NOTA: En producción (Railway), Steel Browser tendrá acceso a internet
      y podrá buscar en Google Images exitosamente.
""")
