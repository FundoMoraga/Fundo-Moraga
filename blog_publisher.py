"""
Sistema de publicación automática de artículos del blog
Gestiona la creación de archivos HTML y actualización del índice del blog
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import os
import json
import re
from pathlib import Path
from cosmos_client import get_conversation_store
import config

class BlogPublisher:
    """Publica artículos generados al blog HTML estático"""
    
    def __init__(self):
        self.blog_dir = Path("Web/blog")
        self.articles_dir = self.blog_dir / "articulos"
        self._conversation_store = None  # Lazy initialization
        
        # Crear directorio de artículos si no existe
        self.articles_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def conversation_store(self):
        """Lazy initialization of Cosmos DB connection"""
        if self._conversation_store is None:
            self._conversation_store = get_conversation_store()
        return self._conversation_store
    
    def _sanitize_slug(self, slug: str) -> str:
        """Sanitiza el slug para nombre de archivo"""
        slug = slug.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _format_date(self, iso_date: str, format: str = "long") -> str:
        """Formatea fecha ISO a formato legible"""
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        
        months_es = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        if format == "long":
            return f"{dt.day} de {months_es[dt.month]} de {dt.year}"
        elif format == "short":
            return f"{dt.day}/{dt.month}/{dt.year}"
        else:
            return dt.strftime("%Y-%m-%d")
    
    def generate_article_html(self, article: Dict[str, Any]) -> str:
        """Genera HTML completo para un artículo"""
        
        slug = self._sanitize_slug(article.get("slug", "articulo"))
        title = article.get("title", "Sin título")
        subtitle = article.get("subtitle", "")
        content_html = article.get("content_html", "<p>Contenido no disponible</p>")
        excerpt = article.get("excerpt", "")
        keywords = ", ".join(article.get("keywords", []))
        category = article.get("category", "noticias")
        reading_time = article.get("reading_time_minutes", 5)
        author = article.get("author", "Hernando IA")
        published_date = article.get("published_at", article.get("generated_at", datetime.now(timezone.utc).isoformat()))
        
        # Obtener imagen destacada (puede ser dict de Pexels o string directo de DALL-E)
        featured_image_raw = article.get("featured_image", "https://fundomoragastorage.blob.core.windows.net/assets/images/blog-default.jpg")
        if isinstance(featured_image_raw, dict):
            # Formato Pexels: {"url": "...", "attribution": "..."}
            featured_image_url = featured_image_raw.get("url", "https://fundomoragastorage.blob.core.windows.net/assets/images/blog-default.jpg")
            featured_image_attr = featured_image_raw.get("attribution", "")
        else:
            # Formato string directo (DALL-E o URL simple)
            featured_image_url = featured_image_raw
            featured_image_attr = ""
        
        date_formatted = self._format_date(published_date, "long")
        
        # Template HTML completo
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{excerpt}">
    <meta name="keywords" content="{keywords}">
    <meta name="author" content="{author}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://fundomoraga.com/blog/articulos/{slug}.html">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt}">
    <meta property="og:image" content="{featured_image_url}">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://fundomoraga.com/blog/articulos/{slug}.html">
    <meta property="twitter:title" content="{title}">
    <meta property="twitter:description" content="{excerpt}">
    <meta property="twitter:image" content="{featured_image_url}">
    
    <!-- Article metadata -->
    <meta property="article:published_time" content="{published_date}">
    <meta property="article:author" content="{author}">
    <meta property="article:section" content="{category}">
    
    <title>{title} - Fundo Moraga Blog</title>
    <link rel="canonical" href="https://fundomoraga.com/blog/articulos/{slug}.html">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/png" href="https://fundomoragastorage.blob.core.windows.net/assets/images/Logo%20Fundo%20Moraga.png">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/css/tokens.css">
    <link rel="stylesheet" href="/css/buttons.css">
    <link rel="stylesheet" href="../../styles.20260126-1.css">
    <link rel="stylesheet" href="../blog-styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    
    <!-- Google Analytics 4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-43GCJKN7KX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-43GCJKN7KX');
    </script>
    
    <style>
        .article-header {{
            padding: 120px 0 60px;
            background: linear-gradient(135deg, rgba(10, 10, 10, 0.95), rgba(30, 30, 30, 0.9));
            border-bottom: 1px solid rgba(212, 175, 55, 0.3);
        }}
        
        .article-meta {{
            display: flex;
            gap: 20px;
            align-items: center;
            justify-content: center;
            margin-top: 20px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }}
        
        .article-meta span {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .featured-image {{
            width: 100%;
            max-width: 800px;
            height: auto;
            margin: 40px auto;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(212, 175, 55, 0.2);
            display: block;
        }}
        
        .image-attribution {{
            text-align: center;
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 10px;
            margin-bottom: 40px;
        }}
        
        .image-attribution a {{
            color: rgba(212, 175, 55, 0.8);
            text-decoration: none;
        }}
        
        .image-attribution a:hover {{
            color: rgb(212, 175, 55);
            text-decoration: underline;
        }}
        
        .article-content {{
            max-width: 800px;
            margin: 60px auto;
            padding: 0 20px;

            line-height: 1.8;
            color: #e0e0e0;
        }}
        
        .article-content h2 {{
            color: #d4af37;
            font-size: 1.8rem;
            margin-top: 40px;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        
        .article-content h3 {{
            color: #e0c04a;
            font-size: 1.4rem;
            margin-top: 30px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .article-content p {{
            margin-bottom: 20px;
            font-size: 1.05rem;
        }}
        
        .article-content ul, .article-content ol {{
            margin: 20px 0;
            padding-left: 30px;
        }}
        
        .article-content li {{
            margin-bottom: 10px;
        }}
        
        .article-cta {{
            margin: 60px auto;
            padding: 40px;
            max-width: 700px;
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(212, 175, 55, 0.05));
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 12px;
            text-align: center;
        }}
        
        .article-cta h3 {{
            color: #d4af37;
            margin-bottom: 15px;
        }}
        
        .badge-category {{
            display: inline-block;
            padding: 6px 16px;
            background: rgba(212, 175, 55, 0.2);
            color: #d4af37;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body data-theme="dark">
    <a class="skip-link" href="#article-content">Saltar al contenido</a>

    <!-- Navigation -->
    <nav class="navbar dark-nav">
        <div class="container">
            <div class="nav-wrapper">
                <a href="../../index.html">
                    <img src="https://fundomoragastorage.blob.core.windows.net/assets/images/Logo%20Fundo%20Moraga.png" alt="Fundo Moraga" class="logo">
                </a>
                <button class="mobile-menu-toggle" aria-label="Abrir menú de navegación" aria-expanded="false">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
                <ul class="nav-links">
                    <li><a href="../../index.html#inicio" class="btn btn--tertiary btn--sm">Inicio</a></li>
                    <li><a href="../../index.html#nosotros" class="btn btn--tertiary btn--sm">Nosotros</a></li>
                    <li><a href="../../historia.html" class="btn btn--tertiary btn--sm">Historia</a></li>
                    <li><a href="../../leyenda.html" class="btn btn--tertiary btn--sm">La Leyenda</a></li>
                    <li><a href="../../mapa.html" class="btn btn--tertiary btn--sm">Mapa Virtual</a></li>
                    <li><a href="../../index.html#servicios" class="btn btn--tertiary btn--sm">Servicios</a></li>
                    <li><a href="../index.html" class="btn btn--tertiary btn--sm active">Blog</a></li>
                    <li><a href="../../index.html#contacto" class="btn btn--tertiary btn--sm">Contacto</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Article Header -->
    <header class="article-header">
        <div class="container" style="text-align: center;">
            <span class="badge-category">{category}</span>
            <h1 style="font-size: 2.5rem; color: #fff; margin-bottom: 15px;">{title}</h1>
            {f'<p style="font-size: 1.2rem; color: rgba(255,255,255,0.8); margin-bottom: 10px;">{subtitle}</p>' if subtitle else ''}
            <div class="article-meta">
                <span>📅 {date_formatted}</span>
                <span>✍️ {author}</span>
                <span>⏱️ {reading_time} min lectura</span>
            </div>
        </div>
    </header>

    <!-- Featured Image -->
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 20px;">
        <img src="{featured_image}" alt="{title}" style="width: 100%; height: auto; border-radius: 12px; margin: 40px 0; box-shadow: 0 10px 40px rgba(0,0,0,0.3);">
    </div>

    <!-- Article Content -->
    <main id="article-content">
        <!-- Featured Image -->
        {f'<div style="text-align: center; max-width: 800px; margin: 40px auto;"><img src="{featured_image_url}" alt="{title}" class="featured-image" loading="lazy"><div class="image-attribution">{featured_image_attr}</div></div>' if featured_image_url else ''}
        
        <article class="article-content">
            {content_html}
        </article>

        <!-- Call to Action -->
        <div class="article-cta">
            <h3>¿Listo para la Aventura Off-Road?</h3>
            <p style="margin-bottom: 25px; color: rgba(255,255,255,0.8);">
                Vive la experiencia 4x4 más completa en Fundo Moraga, Batuco. 
                Circuitos profesionales, capacitación y eventos corporativos.
            </p>
            <a href="../../index.html#contacto" class="btn btn--primary btn--lg">
                Reserva tu Visita
            </a>
        </div>
    </main>

    <!-- Footer -->
    <footer style="background: rgba(10,10,10,0.95); padding: 40px 20px; text-align: center; border-top: 1px solid rgba(212,175,55,0.2);">
        <div class="container">
            <p style="color: rgba(255,255,255,0.6); margin-bottom: 10px;">
                &copy; {datetime.now().year} Fundo Moraga. Todos los derechos reservados.
            </p>
            <p style="color: rgba(255,255,255,0.4); font-size: 0.85rem;">
                Artículo generado por Hernando IA basándose en múltiples fuentes públicas
            </p>
            <div style="margin-top: 20px;">
                <a href="../index.html" class="btn btn--tertiary btn--sm">← Volver al Blog</a>
            </div>
        </div>
    </footer>

    <script src="../blog-scripts.js"></script>
</body>
</html>"""
        
        return html
    
    def publish_article(self, article: Dict[str, Any], save_to_cosmos: bool = True) -> Dict[str, str]:
        """
        Publica un artículo:
        1. Guarda en Cosmos DB
        2. Genera archivo HTML
        3. Actualiza índice del blog
        """
        try:
            slug = self._sanitize_slug(article.get("slug", "articulo"))
            filename = f"{slug}.html"
            filepath = self.articles_dir / filename
            
            # Marcar como publicado
            article["status"] = "published"
            article["published_at"] = datetime.now(timezone.utc).isoformat()
            article["url"] = f"https://fundomoraga.com/blog/articulos/{filename}"
            
            # 1. Guardar en Cosmos DB
            if save_to_cosmos:
                print(f"💾 Guardando artículo en Cosmos DB...")
                cosmos_doc = {
                    "id": f"article_{slug}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                    "type": "blog_article",
                    "userId": "system",
                    **article
                }
                self.conversation_store.container.upsert_item(cosmos_doc)
                print(f"✅ Guardado en Cosmos: {cosmos_doc['id']}")
            
            # 2. Generar archivo HTML
            print(f"📄 Generando HTML: {filepath}")
            html_content = self.generate_article_html(article)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Artículo publicado: {filepath}")
            
            # 3. Actualizar índice del blog y sitemap
            self._update_blog_index(article, filename)
            self._update_sitemap()
            
            return {
                "success": True,
                "filepath": str(filepath),
                "url": article["url"],
                "slug": slug
            }
            
        except Exception as e:
            print(f"❌ Error publicando artículo: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_blog_index(self, article: Dict[str, Any], filename: str):
        """Actualiza el índice del blog con el nuevo artículo"""
        print(f"📋 Artículo '{article.get('title')}' listo para añadir al índice")
        print(f"   URL: /blog/articulos/{filename}")
        # TODO: Implementar actualización dinámica del index.html
    
    def _update_sitemap(self):
        """Actualiza sitemap.xml con artículos nuevos"""
        try:
            from sitemap_generator import update_sitemap_file
            update_sitemap_file()
            print("✅ Sitemap actualizado")
        except Exception as e:
            print(f"⚠️  No se pudo actualizar sitemap: {e}")
    
    def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene artículos recientes de Cosmos DB"""
        try:
            query = """
            SELECT * FROM c 
            WHERE c.type = 'blog_article' 
            AND c.status = 'published'
            ORDER BY c.published_at DESC
            OFFSET 0 LIMIT @limit
            """
            
            items = list(self.conversation_store.container.query_items(
                query=query,
                parameters=[{"name": "@limit", "value": limit}],
                enable_cross_partition_query=True
            ))
            
            return items
            
        except Exception as e:
            print(f"❌ Error obteniendo artículos: {e}")
            return []


def get_blog_publisher() -> BlogPublisher:
    """Singleton instance"""
    if not hasattr(get_blog_publisher, '_instance'):
        get_blog_publisher._instance = BlogPublisher()
    return get_blog_publisher._instance


# CLI para testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Blog Publisher para Fundo Moraga")
    parser.add_argument("--test", action="store_true", help="Publicar artículo de prueba")
    parser.add_argument("--list", action="store_true", help="Listar artículos recientes")
    
    args = parser.parse_args()
    
    publisher = BlogPublisher()
    
    if args.test:
        # Artículo de prueba
        test_article = {
            "title": "Artículo de Prueba",
            "subtitle": "Sistema de publicación automática funcionando",
            "slug": "articulo-de-prueba",
            "content_html": "<h2>Sección 1</h2><p>Este es un artículo de prueba generado automáticamente.</p>",
            "excerpt": "Artículo de prueba del sistema de publicación automática",
            "keywords": ["test", "4x4", "off-road"],
            "category": "noticias",
            "reading_time_minutes": 3,
            "author": "Hernando IA",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = publisher.publish_article(test_article)
        print(json.dumps(result, indent=2))
    
    elif args.list:
        articles = publisher.get_recent_articles()
        print(json.dumps([{
            "title": a.get("title"),
            "published_at": a.get("published_at"),
            "url": a.get("url")
        } for a in articles], indent=2, ensure_ascii=False))
    
    else:
        print("Usa --test o --list")
