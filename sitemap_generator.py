"""
Generador dinámico de sitemap.xml
Incluye páginas estáticas + artículos del blog desde Cosmos DB
"""
from datetime import datetime, timezone
from typing import List, Dict
from cosmos_client import get_conversation_store
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_sitemap() -> str:
    """Genera sitemap.xml completo con páginas estáticas y artículos dinámicos"""
    
    # Namespace declarations
    namespaces = {
        '': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        'image': 'http://www.google.com/schemas/sitemap-image/1.1',
        'video': 'http://www.google.com/schemas/sitemap-video/1.1'
    }
    
    # Register namespaces
    for prefix, uri in namespaces.items():
        if prefix:
            ET.register_namespace(prefix, uri)
        else:
            ET.register_namespace('', uri)
    
    # Root element
    urlset = ET.Element('urlset')
    for prefix, uri in namespaces.items():
        if prefix:
            urlset.set(f'xmlns:{prefix}', uri)
        else:
            urlset.set('xmlns', uri)
    
    # Páginas estáticas
    static_pages = [
        {
            'loc': 'https://fundomoraga.com/',
            'lastmod': '2026-01-31',
            'changefreq': 'weekly',
            'priority': '1.0',
            'image': 'https://fundomoragastorage.blob.core.windows.net/assets/images/Logo%20Fundo%20Moraga.png'
        },
        {
            'loc': 'https://fundomoraga.com/historia.html',
            'lastmod': '2026-01-31',
            'changefreq': 'monthly',
            'priority': '0.9',
            'image': 'https://fundomoragastorage.blob.core.windows.net/assets/images/Palacio%20de%20los%20Moraga.jpg'
        },
        {
            'loc': 'https://fundomoraga.com/leyenda.html',
            'lastmod': '2026-01-31',
            'changefreq': 'monthly',
            'priority': '0.9'
        },
        {
            'loc': 'https://fundomoraga.com/mapa.html',
            'lastmod': '2026-01-31',
            'changefreq': 'monthly',
            'priority': '0.8'
        },
        {
            'loc': 'https://fundomoraga.com/reservas.html',
            'lastmod': '2026-01-31',
            'changefreq': 'monthly',
            'priority': '0.8'
        },
        {
            'loc': 'https://fundomoraga.com/blog/',
            'lastmod': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '0.9'
        }
    ]
    
    for page in static_pages:
        url = ET.SubElement(urlset, 'url')
        ET.SubElement(url, 'loc').text = page['loc']
        ET.SubElement(url, 'lastmod').text = page['lastmod']
        ET.SubElement(url, 'changefreq').text = page['changefreq']
        ET.SubElement(url, 'priority').text = page['priority']
        
        if 'image' in page:
            image = ET.SubElement(url, '{http://www.google.com/schemas/sitemap-image/1.1}image')
            ET.SubElement(image, '{http://www.google.com/schemas/sitemap-image/1.1}loc').text = page['image']
    
    # Artículos del blog (dinámico desde Cosmos DB)
    try:
        store = get_conversation_store()
        query = """
        SELECT c.url, c.published_at, c.title
        FROM c 
        WHERE c.type = 'blog_article' 
        AND c.status = 'published'
        ORDER BY c.published_at DESC
        """
        
        articles = list(store.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        for article in articles:
            url = ET.SubElement(urlset, 'url')
            ET.SubElement(url, 'loc').text = article.get('url', '')
            
            # Formatear fecha
            pub_date = article.get('published_at', '')
            if pub_date:
                try:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    ET.SubElement(url, 'lastmod').text = dt.strftime('%Y-%m-%d')
                except:
                    pass
            
            ET.SubElement(url, 'changefreq').text = 'monthly'
            ET.SubElement(url, 'priority').text = '0.8'
        
        print(f"✓ Añadidos {len(articles)} artículos al sitemap")
        
    except Exception as e:
        print(f"⚠️  No se pudieron cargar artículos del blog: {e}")
    
    # Convertir a string con formato bonito
    rough_string = ET.tostring(urlset, encoding='unicode', method='xml')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')
    
    # Limpiar líneas vacías extra
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    return '\n'.join(lines)


def update_sitemap_file():
    """Actualiza el archivo Web/sitemap.xml"""
    try:
        sitemap_content = generate_sitemap()
        
        with open('Web/sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
        
        print("✅ Sitemap actualizado: Web/sitemap.xml")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando sitemap: {e}")
        return False


if __name__ == "__main__":
    print("🗺️  Generando sitemap dinámico...")
    update_sitemap_file()
