from hernando_tools import get_hernando_tools

tools = get_hernando_tools('+56941242609')

# Filtrar herramientas de búsqueda y análisis de imágenes
image_tools = [t['function']['name'] for t in tools.tools if 'imagen' in t['function']['name'].lower() or 'imagenes' in t['function']['name'].lower()]

print("🖼️ Herramientas de búsqueda y análisis de imágenes disponibles:")
for tool in sorted(image_tools):
    print(f"  ✅ {tool}")

print(f"\nTotal de herramientas disponibles: {len(tools.tools)}")

# Mostrar todas las herramientas con web/imagen
all_special = [t['function']['name'] for t in tools.tools if 'web' in t['function']['name'].lower() or 'imagen' in t['function']['name'].lower() or 'buscar' in t['function']['name'].lower()]
print(f"\n🔍 Herramientas de investigación web + imágenes:")
for tool in sorted(all_special):
    print(f"  ✅ {tool}")
