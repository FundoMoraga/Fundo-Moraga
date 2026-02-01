"""
Sistema de agregación ética de noticias automotrices
Genera artículos ORIGINALES basándose en múltiples fuentes públicas
NO copia contenido con copyright - cumple con fair use y estándares éticos
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
import json
import time
from openai_client import get_chatbot_ai
import config
import re

class NewsSource:
    """Define una fuente de noticias automotrices"""
    def __init__(self, name: str, url: str, selectors: Dict[str, str], category: str = "general"):
        self.name = name
        self.url = url
        self.selectors = selectors  # CSS selectors para extraer titulares
        self.category = category

# Fuentes de noticias públicas (solo titulares y enlaces)
NEWS_SOURCES = [
    NewsSource(
        name="RutaMotor",
        url="https://rutamotor.com",
        selectors={
            "articles": "article.post",
            "title": "h2.entry-title",
            "link": "h2.entry-title a",
            "excerpt": "div.entry-summary"
        },
        category="nacional"
    ),
    NewsSource(
        name="La Tercera Motores",
        url="https://www.latercera.com/category/tendencias/autos/",
        selectors={
            "articles": "article",
            "title": "h2.headline",
            "link": "a.story-link",
            "excerpt": "div.excerpt"
        },
        category="nacional"
    ),
    NewsSource(
        name="Al Torque",
        url="https://www.altorque.cl",
        selectors={
            "articles": "article",
            "title": "h2",
            "link": "a",
            "excerpt": "p.excerpt"
        },
        category="nacional"
    )
]

class NewsAggregator:
    """Agrega noticias de múltiples fuentes y genera contenido original"""
    
    def __init__(self):
        self.chatbot_ai = get_chatbot_ai()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FundoMoragaBot/1.0; +https://fundomoraga.com)'
        })
    
    def fetch_headlines(self, source: NewsSource, max_items: int = 5) -> List[Dict[str, str]]:
        """
        Extrae solo titulares y enlaces de una fuente (ethical scraping)
        NO extrae contenido completo - solo información pública básica
        """
        headlines = []
        try:
            print(f"📰 Consultando {source.name}...")
            response = self.session.get(source.url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select(source.selectors.get("articles", "article"))[:max_items]
            
            for article in articles:
                try:
                    title_elem = article.select_one(source.selectors.get("title", "h2"))
                    link_elem = article.select_one(source.selectors.get("link", "a"))
                    excerpt_elem = article.select_one(source.selectors.get("excerpt", "p"))
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href', '')
                        excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ""
                        
                        # Normalizar URL relativa
                        if link and not link.startswith('http'):
                            link = source.url.rstrip('/') + '/' + link.lstrip('/')
                        
                        headlines.append({
                            "source": source.name,
                            "category": source.category,
                            "title": title,
                            "link": link,
                            "excerpt": excerpt[:200] if excerpt else "",  # Solo primeras 200 chars
                            "fetched_at": datetime.now(timezone.utc).isoformat()
                        })
                except Exception as e:
                    print(f"⚠️  Error procesando artículo en {source.name}: {e}")
                    continue
            
            print(f"✓ {len(headlines)} titulares obtenidos de {source.name}")
            time.sleep(1)  # Rate limiting ético
            
        except Exception as e:
            print(f"❌ Error fetching {source.name}: {e}")
        
        return headlines
    
    def fetch_all_headlines(self, max_per_source: int = 5) -> List[Dict[str, str]]:
        """Obtiene titulares de todas las fuentes configuradas"""
        all_headlines = []
        for source in NEWS_SOURCES:
            headlines = self.fetch_headlines(source, max_items=max_per_source)
            all_headlines.extend(headlines)
            time.sleep(2)  # Rate limiting ético entre fuentes
        
        print(f"\n📊 Total: {len(all_headlines)} titulares agregados")
        return all_headlines
    
    def generate_original_article(
        self, 
        headlines: List[Dict[str, str]], 
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera un artículo COMPLETAMENTE ORIGINAL usando IA
        Basado en múltiples fuentes pero con contenido 100% nuevo
        """
        if not headlines:
            raise ValueError("No hay titulares disponibles para generar artículo")
        
        # Preparar contexto de titulares (solo referencias públicas)
        headlines_context = "\n".join([
            f"- {h['title']} (Fuente: {h['source']})"
            for h in headlines[:10]  # Máximo 10 referencias
        ])
        
        # Prompt para generar contenido original
        article_prompt = f"""Eres un redactor experto en contenido automotriz para el blog de Fundo Moraga, un centro off-road premium en Chile.

CONTEXTO DE TENDENCIAS ACTUALES (solo referencias):
{headlines_context}

TAREA:
Basándote en las tendencias actuales del mundo automotriz mostradas arriba, crea un artículo COMPLETAMENTE ORIGINAL de 1200-1500 palabras (mínimo 1500 caracteres) que:

1. **Tema Principal**: {focus_topic if focus_topic else 'Resume las tendencias más relevantes del mundo automotriz 4x4/off-road'}
2. **Perspectiva**: Enfoca el contenido hacia entusiastas del 4x4 y off-road en Chile
3. **Estilo**: Profesional pero accesible, con personalidad aventurera
4. **Estructura** (MÍNIMO 1500 CARACTERES):
   - Título atractivo y SEO-friendly
   - Introducción enganchadora (3-4 párrafos explicando el tema)
   - 4-6 secciones de desarrollo con subtítulos descriptivos
   - Cada sección debe tener 2-3 párrafos bien desarrollados
   - Incluir ejemplos concretos, datos técnicos y consejos prácticos
   - Conclusión con call-to-action hacia Fundo Moraga
5. **SEO**: Incluye keywords naturalmente: 4x4, off-road, Chile, Batuco, manejo todoterreno
6. **Originalidad**: NO copies texto de las fuentes - genera contenido 100% nuevo
7. **Longitud**: El artículo debe tener MÍNIMO 1500 caracteres de contenido (sin contar HTML tags)

FORMATO DE SALIDA (JSON):
{{
    "title": "Título del artículo",
    "subtitle": "Subtítulo o bajada",
    "slug": "titulo-del-articulo-en-formato-url",
    "content_html": "<p>Contenido completo en HTML con <h2>, <h3>, <p>, <ul>, etc.</p>",
    "excerpt": "Resumen de 120-150 caracteres",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "category": "noticias" o "tips" o "tecnologia",
    "reading_time_minutes": 4,
    "sources_referenced": ["RutaMotor", "La Tercera"]
}}

IMPORTANTE: El contenido debe ser 100% original, transformativo y añadir valor único. No plagies."""

        try:
            print("🤖 Generando artículo original con IA...")
            
            # Usar el cliente OpenAI existente
            response = self.chatbot_ai.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Eres un redactor experto en contenido automotriz. Generas contenido 100% original, transformativo y detallado. Tus artículos siempre superan los 1500 caracteres."},
                    {"role": "user", "content": article_prompt}
                ],
                temperature=0.8,  # Mayor creatividad
                max_tokens=4000,  # Aumentado para artículos más largos
                response_format={"type": "json_object"}
            )
            
            article_data = json.loads(response.choices[0].message.content)
            
            # Añadir metadata
            article_data["generated_at"] = datetime.now(timezone.utc).isoformat()
            article_data["status"] = "draft"
            article_data["author"] = "Hernando IA"
            article_data["source_headlines_count"] = len(headlines)
            
            print(f"✅ Artículo generado: '{article_data.get('title', 'Sin título')}'")
            return article_data
            
        except Exception as e:
            print(f"❌ Error generando artículo: {e}")
            raise
    
    def create_daily_digest(self) -> Dict[str, Any]:
        """
        Crea un digest diario completo:
        1. Agrega titulares de todas las fuentes
        2. Genera artículo original basado en tendencias
        """
        print("\n" + "="*60)
        print("🚀 INICIANDO GENERACIÓN DE CONTENIDO DIARIO")
        print("="*60 + "\n")
        
        # Paso 1: Agregar titulares
        headlines = self.fetch_all_headlines(max_per_source=5)
        
        if not headlines:
            raise ValueError("No se pudieron obtener titulares de ninguna fuente")
        
        # Paso 2: Generar artículo original
        article = self.generate_original_article(
            headlines=headlines,
            focus_topic="Las tendencias más importantes del mundo automotriz y off-road"
        )
        
        # Paso 3: Crear digest completo
        digest = {
            "digest_id": f"digest_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "headlines_collected": len(headlines),
            "sources_consulted": list(set([h["source"] for h in headlines])),
            "article": article,
            "raw_headlines": headlines  # Para referencia interna
        }
        
        print("\n✅ DIGEST DIARIO COMPLETADO")
        print(f"   📰 Titulares agregados: {len(headlines)}")
        print(f"   📝 Artículo: {article.get('title', 'N/A')}")
        print(f"   ⏱️  Tiempo de lectura: {article.get('reading_time_minutes', 0)} min")
        
        return digest


def get_news_aggregator() -> NewsAggregator:
    """Singleton instance"""
    if not hasattr(get_news_aggregator, '_instance'):
        get_news_aggregator._instance = NewsAggregator()
    return get_news_aggregator._instance


# CLI para testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="News Aggregator para Fundo Moraga")
    parser.add_argument("--headlines", action="store_true", help="Solo obtener titulares")
    parser.add_argument("--generate", action="store_true", help="Generar artículo completo")
    parser.add_argument("--digest", action="store_true", help="Crear digest diario completo")
    
    args = parser.parse_args()
    
    aggregator = NewsAggregator()
    
    if args.headlines:
        headlines = aggregator.fetch_all_headlines()
        print(json.dumps(headlines, indent=2, ensure_ascii=False))
    
    elif args.generate:
        headlines = aggregator.fetch_all_headlines()
        article = aggregator.generate_original_article(headlines)
        print(json.dumps(article, indent=2, ensure_ascii=False))
    
    elif args.digest:
        digest = aggregator.create_daily_digest()
        print(json.dumps(digest, indent=2, ensure_ascii=False))
    
    else:
        print("Usa --headlines, --generate o --digest")
