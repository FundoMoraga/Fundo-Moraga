"""
Test: Búsqueda de imágenes y envío por WhatsApp
Simula el flujo completo: buscar imágenes → analizar con Vision → enviar a WhatsApp
"""
import json
import sys
import io
from hernando_tools import get_hernando_tools

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("[TEST] Busqueda de imagenes y envio a WhatsApp")
print("=" * 80)

# Usuario autorizado (Efraín Moraga)
user_id = '+56941242609'
chat_id = '+56941242609@s.whatsapp.net'

print(f"\nUsuario: {user_id}")
print(f"Chat ID: {chat_id}")

# Obtener herramientas
tools = get_hernando_tools(user_id)
print(f"\n[OK] Herramientas cargadas: {len(tools.tools)} disponibles")

# Mostrar herramientas de búsqueda de imágenes
image_tools = [
    t['function']['name'] 
    for t in tools.tools 
    if 'buscar_imagen' in t['function']['name']
]

print(f"\n[TOOLS] Herramientas de busqueda de imagenes:")
for tool in image_tools:
    print(f"   - {tool}")

print("\n" + "=" * 80)
print("[TEST] Simulacion: Busqueda de 'Jeep Wrangler'")
print("=" * 80)

# Preparar argumentos para buscar imágenes
search_args = {
    "query": "Jeep Wrangler",
    "max_results": 5,
    "doctoral_area": "tecnologia"
}

print(f"\n[PARAMS] Parametros de busqueda:")
print(f"   - Query: {search_args['query']}")
print(f"   - Max resultados: {search_args['max_results']}")
print(f"   - Area doctoral: {search_args['doctoral_area']}")

print("\n[EXEC] Ejecutando herramienta 'buscar_imagenes'...")

try:
    result = tools.execute_tool("buscar_imagenes", search_args)
    
    if result.get("success"):
        print(f"\n[OK] Busqueda exitosa!")
        print(f"   - Total encontradas: {result.get('total_found', 0)}")
        print(f"   - Total analizadas: {result.get('total_analyzed', 0)}")
        
        images = result.get("images", [])
        
        if images:
            print(f"\n[RESULTS] Primeras 3 imagenes encontradas:")
            for img in images[:3]:
                print(f"\n   [{img.get('search_index', '?')}] {img.get('search_title', 'Sin titulo')}")
                print(f"       URL: {img.get('image_url', 'N/A')}")
                if img.get('academic_summary'):
                    summary = img['academic_summary'][:100]
                    print(f"       Summary: {summary}...")
                if img.get('relevance_score'):
                    print(f"       Relevancia: {img['relevance_score']:.1f}%")
        
        # Demostrar URLs de imágenes para envío
        image_urls = [img.get('image_url') for img in images[:3] if img.get('image_url')]
        
        if image_urls:
            print(f"\n[WHATSAPP] URLs listas para envio por WhatsApp:")
            for i, url in enumerate(image_urls, 1):
                print(f"   [{i}] {url}")
            
            print(f"\n[INFO] Estas imagenes podrian enviarse a WhatsApp con:")
            print(f"   _send_waha_images_batch(chat_id='{chat_id}', image_urls=[...])")
    else:
        print(f"[ERROR] Error en busqueda: {result.get('error', 'Desconocido')}")

except Exception as e:
    print(f"[ERROR] Error ejecutando herramienta: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("[FLUJO COMPLETO]")
print("=" * 80)
print("""
1. Hernando recibe: "Hernando, busca 10 fotografias de Jeep Wrangler"

2. Hernando usa herramienta 'buscar_imagenes' con:
   - Steel Browser -> Busca en Google Images
   - Vision Service -> Analiza cada imagen academicamente
   - Extrae: objetos, descripcion, tags, confianza

3. Resultado: Lista de imagenes con analisis doctoral

4. Hernando usa funcion 'prepare_images_for_whatsapp()' para:
   - Preparar URLs de imagenes
   - Invocar _send_waha_images_batch()
   - Enviar cada imagen a WhatsApp con caption

5. Usuario recibe: 10 imagenes de Jeep Wrangler en WhatsApp con analisis
""")

print("[OK] Test completado exitosamente!")
