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

# Categorías de artículos del blog con tópicos específicos
BLOG_CATEGORIES = {
    "historia": {
        "topics": [
            "Historia y tradiciones de Chile y la cultura huasa",
            "Genealogía y legado familiar en Latinoamérica",
            "Evolución del turismo rural y experiencias de aventura",
            "Patrimonio cultural chileno y conservación",
            "La familia Moraga y su conexión con la región"
        ],
        "prompt_prefix": "Enfócate en la historia, tradición y legado cultural. Incluye datos históricos interesantes y referencias a la región."
    },
    "guias": {
        "topics": [
            "Técnicas y consejos prácticos para manejo 4x4",
            "Preparación de vehículos todoterreno profesional",
            "Rutas escénicas y como planificar aventuras off-road",
            "Equipamiento esencial para expediciones outdoor",
            "Seguridad y protocolos en terrenos desafiantes"
        ],
        "prompt_prefix": "Crea una guía práctica y detallada con pasos concretos, listas de verificación y consejos profesionales."
    },
    "rutas": {
        "topics": [
            "Mejores circuitos off-road de la zona central de Chile",
            "Rutas scenic de Batuco y alrededores",
            "Senderos 4x4 con diferentes niveles de dificultad",
            "Destinos todoterreno cercanos a Santiago",
            "Exploración de terrenos naturales de Batuco"
        ],
        "prompt_prefix": "Describe rutas específicas con detalles de terreno, dificultad, duración, y puntos de interés. Incluye tips de navegación."
    },
    "eventos": {
        "topics": [
            "Experiencias corporativas en naturaleza",
            "Team building y actividades para equipos",
            "Eventos off-road y competiciones 4x4",
            "Reuniones empresariales en entornos outdoors",
            "Celebraciones y actividades grupales en Batuco"
        ],
        "prompt_prefix": "Enfócate en beneficios corporativos, dinámicas de grupo, impacto en equipos de trabajo."
    },
    "noticias": {
        "topics": [
            "Novedades en industria automotriz y 4x4",
            "Tendencias en turismo de aventura",
            "Desarrollos en tecnología off-road",
            "Eventos deportivos y competiciones de 4x4",
            "Anuncios y actualizaciones de Fundo Moraga"
        ],
        "prompt_prefix": "Escribe un artículo de noticias actual y relevante con perspectiva profesional."
    }
}

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
    
    def generate_article_by_category(
        self,
        headlines: List[Dict[str, str]],
        category: str,
        topic_index: int = 0
    ) -> Dict[str, Any]:
        """
        Genera un artículo específico para una categoría del blog
        """
        if category not in BLOG_CATEGORIES:
            raise ValueError(f"Categoría desconocida: {category}")
        
        cat_config = BLOG_CATEGORIES[category]
        topics = cat_config["topics"]
        topic = topics[topic_index % len(topics)]  # Rotar tópicos
        prompt_prefix = cat_config["prompt_prefix"]
        
        # Preparar contexto de titulares
        headlines_context = "\n".join([
            f"- {h['title']} (Fuente: {h['source']})"
            for h in headlines[:10]
        ])
        
        article_prompt = f"""Eres un redactor experto en contenido automotriz para el blog de Fundo Moraga, un centro off-road premium en Chile.

CONTEXTO DE TENDENCIAS ACTUALES (solo referencias):
{headlines_context}

INSTRUCCIÓN ESPECÍFICA:
{prompt_prefix}

TAREA:
Basándote en las tendencias actuales del mundo automotriz y el contexto sobre "{topic}", crea un artículo COMPLETAMENTE ORIGINAL de 1200-1500 palabras (mínimo 1500 caracteres):

1. **Tema Principal**: {topic}
2. **Categoría**: {category}
3. **Perspectiva**: Enfoca hacia entusiastas del 4x4 y off-road en Chile, con especial énfasis en Fundo Moraga
4. **Estilo**: Profesional pero accesible, con personalidad aventurera
5. **Estructura** (MÍNIMO 1500 CARACTERES):
   - Título atractivo y SEO-friendly específico para la categoría
   - Introducción enganchadora (3-4 párrafos)
   - 4-6 secciones bien desarrolladas con subtítulos
   - Cada sección: 2-3 párrafos con ejemplos concretos
   - Conclusión con call-to-action a Fundo Moraga
6. **SEO**: Incluye keywords: 4x4, off-road, Chile, Batuco, Fundo Moraga
7. **Originalidad**: 100% nuevo - NO copies de fuentes
8. **Longitud**: Mínimo 1500 caracteres de contenido

FORMATO DE SALIDA (JSON VÁLIDO):
{{
    "title": "Título del artículo",
    "subtitle": "Subtítulo breve",
    "slug": "titulo-articulo-en-url",
    "content_html": "<p>Contenido HTML completo</p>",
    "excerpt": "Resumen 120-150 caracteres",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "category": "{category}",
    "reading_time_minutes": 6,
    "sources_referenced": ["source1", "source2"]
}}

IMPORTANTE: Genera contenido original que agregue valor único. ¡No plagies!"""
        
        try:
            print(f"🤖 Generando artículo de {category}: {topic}")
            
            response = self.chatbot_ai.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Eres un redactor experto en contenido automotriz. Generas contenido 100% original, transformativo y detallado. Tus artículos siempre superan los 1500 caracteres."},
                    {"role": "user", "content": article_prompt}
                ],
                temperature=0.8,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            article_data = json.loads(response.choices[0].message.content)
            article_data["generated_at"] = datetime.now(timezone.utc).isoformat()
            article_data["status"] = "draft"
            article_data["author"] = "Hernando IA"
            article_data["source_headlines_count"] = len(headlines)
            
            print(f"   ✅ {article_data.get('title', 'Sin título')}")
            return article_data
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise
    
    def create_daily_digest(self) -> Dict[str, Any]:
        """
        Crea un digest diario completo:
        1. Agrega titulares de todas las fuentes
        2. Genera múltiples artículos (uno por categoría mínimo)
        3. Asegura contenido variado y relevante
        """
        print("\n" + "="*60)
        print("🚀 INICIANDO GENERACIÓN DE CONTENIDO DIARIO")
        print("="*60 + "\n")
        
        # Paso 1: Agregar titulares
        headlines = self.fetch_all_headlines(max_per_source=5)
        
        if not headlines:
            raise ValueError("No se pudieron obtener titulares de ninguna fuente")
        
        print(f"📰 Titulares agregados: {len(headlines)}")
        print("📝 Generando artículos por categoría...\n")
        
        # Paso 2: Generar múltiples artículos (uno por categoría)
        articles = []
        for idx, (category, config) in enumerate(BLOG_CATEGORIES.items()):
            try:
                article = self.generate_article_by_category(
                    headlines=headlines,
                    category=category,
                    topic_index=idx  # Variar tópico según orden
                )
                articles.append(article)
                print(f"✅ {category.upper()}: {article.get('title', 'Sin título')}")
            except Exception as e:
                print(f"⚠️  Error generando artículo de {category}: {e}")
                continue
        
        if not articles:
            raise ValueError("No se pudieron generar artículos de ninguna categoría")
        
        # Paso 3: Crear digest completo
        digest = {
            "digest_id": f"digest_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "headlines_collected": len(headlines),
            "sources_consulted": list(set([h["source"] for h in headlines])),
            "articles": articles,  # Múltiples artículos
            "articles_count": len(articles),
            "raw_headlines": headlines  # Para referencia interna
        }
        
        print("\n✅ DIGEST DIARIO COMPLETADO")
        print(f"   📰 Titulares agregados: {len(headlines)}")
        print(f"   📝 Artículos generados: {len(articles)}")
        total_reading_time = sum(a.get('reading_time_minutes', 0) for a in articles)
        print(f"   ⏱️  Tiempo total de lectura: {total_reading_time} min")
        
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
