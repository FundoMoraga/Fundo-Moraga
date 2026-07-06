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
import unicodedata
from pexels_client import get_pexels_client

FALLBACK_BLOG_IMAGE_URL = "https://fundomoragastorage.blob.core.windows.net/assets/images/blog-default.jpg"

# Marcas para validacion semantica basica de coherencia titulo/imagen
KNOWN_AUTO_BRANDS = {
    "toyota", "maxus", "changan", "mercedes", "lamborghini", "ford", "nissan", "chevrolet",
    "mitsubishi", "jeep", "subaru", "suzuki", "kia", "hyundai", "renault", "peugeot",
    "volkswagen", "audi", "bmw", "honda", "mazda", "fiat", "land", "rover", "gwm", "jac"
}

GENERIC_MODEL_STOPWORDS = {
    "nuevos", "nuevo", "nueva", "nuevas", "disenados", "disenada", "aventura", "off", "road",
    "chile", "analisis", "mercado", "llega", "futuro", "tendencias", "camionetas", "suv", "suvs",
    "segmento", "modelo", "modelos", "turismo", "experiencia", "mejores", "lanzamientos"
}

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

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparaciones robustas (minusculas y sin acentos)."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.lower()

    def _extract_vehicle_entities(self, title: str) -> Dict[str, Any]:
        """Extrae marca esperada y tokens de modelo desde el titulo."""
        t = self._normalize_text(title)
        words = re.findall(r"[a-z0-9]+", t)

        expected_brand = None
        for brand in KNOWN_AUTO_BRANDS:
            if re.search(rf"\b{re.escape(brand)}\b", t):
                expected_brand = brand
                break

        model_tokens: List[str] = []
        if expected_brand and expected_brand in words:
            bidx = words.index(expected_brand)
            for w in words[bidx + 1:bidx + 5]:
                if w in GENERIC_MODEL_STOPWORDS:
                    continue
                if w.isdigit() and len(w) == 4:
                    continue
                if len(w) < 2:
                    continue
                model_tokens.append(w)

        # Tokens con letras+numeros suelen ser buenos identificadores de modelo (ej: t90)
        for w in words:
            if re.search(r"[a-z]+\d+|\d+[a-z]+", w) and w not in model_tokens:
                model_tokens.append(w)

        # Limitar ruido
        model_tokens = model_tokens[:3]

        return {
            "brand": expected_brand,
            "model_tokens": model_tokens,
            "title_norm": t,
        }

    def _build_image_queries(self, article_title: str, category: str, vehicle_entities: Dict[str, Any]) -> List[str]:
        """Construye queries en orden de precision para evitar imagenes incongruentes."""
        expected_brand = vehicle_entities.get("brand")
        model_tokens: List[str] = vehicle_entities.get("model_tokens", [])

        queries: List[str] = []
        if expected_brand:
            model_part = " ".join(model_tokens).strip()
            if model_part:
                queries.append(f"{expected_brand} {model_part} 4x4")
                queries.append(f"{expected_brand} {model_part} suv")
                queries.append(f"{expected_brand} {model_part} pickup")
            queries.append(f"{expected_brand} 4x4")
            queries.append(f"{expected_brand} suv")
            queries.append(f"{expected_brand} pickup truck")

        if category == "historia":
            queries.extend(["off-road tradition", "truck history", "4x4 adventure chile"])
        elif category == "guías":
            queries.extend(["vehicle maintenance", "4x4 repair", "truck preparation"])
        elif category == "rutas":
            queries.extend(["off-road trail", "mountain road", "adventure landscape"])
        elif category == "eventos":
            queries.extend(["off-road competition", "4x4 rally", "adventure sports"])
        else:
            queries.extend(["4x4 truck", "off-road vehicle", "automotive news"])

        # dedupe preservando orden
        seen = set()
        deduped = []
        for q in queries:
            qq = q.strip().lower()
            if qq and qq not in seen:
                seen.add(qq)
                deduped.append(q)
        return deduped

    def _photo_relevance_score(self, photo: Dict[str, Any], vehicle_entities: Dict[str, Any]) -> int:
        """Calcula puntaje de relevancia y descarta marcas contradictorias."""
        text = self._normalize_text(
            f"{photo.get('alt', '')} {photo.get('photographer', '')} {photo.get('url', '')}"
        )

        expected_brand = vehicle_entities.get("brand")
        model_tokens: List[str] = vehicle_entities.get("model_tokens", [])
        score = 0

        if expected_brand:
            if re.search(rf"\b{re.escape(expected_brand)}\b", text):
                score += 60
            else:
                # Si el titulo exige marca y la foto no la evidencia, baja fuerte
                score -= 40

            # Penalizacion extrema por marca contradictoria
            for b in KNOWN_AUTO_BRANDS:
                if b == expected_brand:
                    continue
                if re.search(rf"\b{re.escape(b)}\b", text):
                    score -= 120

            for token in model_tokens:
                if re.search(rf"\b{re.escape(token)}\b", text):
                    score += 25
        else:
            # Sin marca objetivo, preferir descriptores off-road
            for token in ("off", "road", "4x4", "suv", "pickup", "trail", "adventure"):
                if re.search(rf"\b{re.escape(token)}\b", text):
                    score += 8

        return score
    
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
    
    def _generate_featured_image(self, article_title: str, article_excerpt: str) -> Optional[str]:
        """
        Genera una imagen featured usando DALL-E 3 y la sube a Azure Storage
        Retorna la URL pública de la imagen o None si falla
        """
        try:
            from azure_storage_client import upload_blog_image
            import requests
            from datetime import datetime
            
            print("🎨 Generando imagen featured con DALL-E 3...")
            
            # Prompt optimizado para imágenes de blog automotriz
            image_prompt = f"""Professional automotive photography for a blog article titled '{article_title[:100]}'. 
            High-quality image showing 4x4 vehicles, off-road terrain, or automotive technology in action. 
            Modern, dynamic composition with dramatic lighting. Photorealistic style, suitable for blog header."""
            
            # Generar imagen con DALL-E 3
            response = self.chatbot_ai.client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1792x1024",  # Formato 16:9 ideal para blog
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            print(f"✓ Imagen generada: {image_url[:80]}...")
            
            # Descargar imagen temporalmente
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            # Generar nombre de archivo único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blog_featured_{timestamp}.jpg"
            
            # Subir a Azure Storage
            print("☁️  Subiendo imagen a Azure Storage...")
            public_url = upload_blog_image(
                image_data=img_response.content,
                filename=filename,
                content_type="image/jpeg"
            )
            
            print(f"✅ Imagen publicada: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"⚠️  Error generando imagen (continuando sin imagen): {e}")
            return None
    
    def generate_original_article(
        self, 
        headlines: List[Dict[str, str]], 
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera un artículo COMPLETAMENTE ORIGINAL usando IA
        Basado en múltiples fuentes pero con contenido 100% nuevo
        Incluye generación de imagen featured con DALL-E 3
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
            
            # Generar imagen featured
            featured_image = self._generate_featured_image(
                article_title=article_data.get("title", "Artículo 4x4"),
                article_excerpt=article_data.get("excerpt", "")
            )
            
            # Añadir metadata
            article_data["generated_at"] = datetime.now(timezone.utc).isoformat()
            article_data["status"] = "draft"
            article_data["author"] = "Hernando IA"
            article_data["source_headlines_count"] = len(headlines)
            article_data["featured_image"] = featured_image
            
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
            
            # Obtener imagen principal para el artículo
            title = article_data.get('title', '')
            featured_image = self._get_featured_image(title, category)
            if featured_image:
                article_data["featured_image"] = featured_image
            
            print(f"   ✅ {article_data.get('title', 'Sin título')}")
            return article_data
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise
    
    def _get_featured_image(self, article_title: str, category: str) -> Optional[Dict[str, str]]:
        """
        Busca una imagen principal relevante en Pexels para el artículo
        
        Args:
            article_title: Título del artículo para generar términos de búsqueda
            category: Categoría del blog para mejor contextualización
        
        Returns:
            Dict con URL y metadata de la imagen, o None si falla
        """
        try:
            pexels = get_pexels_client(api_key=config.PEXELS_API_KEY)
            entities = self._extract_vehicle_entities(article_title)
            expected_brand = entities.get("brand")
            queries = self._build_image_queries(article_title, category, entities)

            best_photo: Optional[Dict[str, Any]] = None
            best_score = -999

            for query in queries:
                photos = pexels.search_images(query, per_page=12, orientation="landscape")
                if not photos:
                    continue

                for photo in photos:
                    score = self._photo_relevance_score(photo, entities)
                    if score > best_score:
                        best_score = score
                        best_photo = photo

                # Corte temprano solo si hay alta confianza real
                if expected_brand and best_score >= 80:
                    break
                if not expected_brand and best_score >= 45:
                    break

            # Regla anti-error: si el titulo menciona marca y no hay confianza alta, usar imagen neutra
            required_score = 70 if expected_brand else 35
            if best_photo and best_score >= required_score:
                src = best_photo.get("src", {})
                image_url = src.get("large") or src.get("medium") or src.get("small")
                if image_url:
                    return {
                        "url": image_url,
                        "photographer": best_photo.get("photographer", "Photographer"),
                        "source": "pexels",
                        "attribution": pexels.format_attribution(best_photo),
                    }

            # Fallback seguro: imagen referencial neutra para evitar asociaciones de marca incorrectas.
            return {
                "url": FALLBACK_BLOG_IMAGE_URL,
                "photographer": "Fundo Moraga",
                "source": "fallback_local",
                "attribution": "Imagen referencial de Fundo Moraga",
            }

        except Exception as e:
            print(f"   ⚠️  No se pudo obtener imagen: {e}")
            return {
                "url": FALLBACK_BLOG_IMAGE_URL,
                "photographer": "Fundo Moraga",
                "source": "fallback_local",
                "attribution": "Imagen referencial de Fundo Moraga",
            }
    
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
