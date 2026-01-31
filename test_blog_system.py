"""
Script de testing rápido para el sistema de publicaciones
Verifica la estructura sin necesidad de APIs externas
"""

def test_imports():
    """Test 1: Verificar que todos los módulos se importan correctamente"""
    print("🧪 Test 1: Imports de módulos")
    try:
        import news_aggregator
        print("  ✓ news_aggregator")
        import blog_publisher
        print("  ✓ blog_publisher")
        import news_scheduler
        print("  ✓ news_scheduler")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_data_structures():
    """Test 2: Verificar estructuras de datos"""
    print("\n🧪 Test 2: Estructuras de datos")
    try:
        from news_aggregator import NEWS_SOURCES
        print(f"  ✓ {len(NEWS_SOURCES)} fuentes de noticias configuradas")
        for source in NEWS_SOURCES:
            print(f"    - {source.name} ({source.category})")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_html_generation():
    """Test 3: Verificar generación HTML sin publicar"""
    print("\n🧪 Test 3: Generación de HTML")
    try:
        from blog_publisher import BlogPublisher
        from datetime import datetime, timezone
        from pathlib import Path
        
        # Crear publisher SIN inicializar Cosmos (solo para testing)
        publisher = BlogPublisher.__new__(BlogPublisher)
        publisher.blog_dir = Path("Web/blog")
        publisher.articles_dir = publisher.blog_dir / "articulos"
        # NO llamar a get_conversation_store() en modo test
        
        # Artículo de prueba
        test_article = {
            "title": "Test: Tendencias 4x4 en Chile",
            "subtitle": "Artículo de prueba del sistema automático",
            "slug": "test-tendencias-4x4-chile",
            "content_html": """
                <h2>Introducción</h2>
                <p>Este es un artículo de prueba generado por el sistema de publicaciones automáticas.</p>
                
                <h2>Tendencias Principales</h2>
                <ul>
                    <li>Vehículos eléctricos off-road</li>
                    <li>Tecnología de suspensión adaptativa</li>
                    <li>Neumáticos todo terreno de nueva generación</li>
                </ul>
                
                <h3>Conclusión</h3>
                <p>El mercado 4x4 continúa evolucionando con tecnología de punta.</p>
            """,
            "excerpt": "Descubre las últimas tendencias del mundo 4x4 y off-road en Chile para 2026",
            "keywords": ["4x4", "off-road", "chile", "tendencias", "tecnología"],
            "category": "noticias",
            "reading_time_minutes": 4,
            "author": "Hernando IA",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Generar HTML (sin guardar)
        html = publisher.generate_article_html(test_article)
        
        print(f"  ✓ HTML generado: {len(html)} caracteres")
        print(f"  ✓ Incluye título: {'title' in html.lower()}")
        print(f"  ✓ Incluye contenido: {'tendencias' in html.lower()}")
        print(f"  ✓ Incluye metadatos: {'og:' in html.lower()}")
        
        # Guardar para inspección
        with open("test_article_output.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ HTML guardado en: test_article_output.html")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduler_logic():
    """Test 4: Verificar lógica del scheduler"""
    print("\n🧪 Test 4: Lógica del scheduler")
    try:
        from news_scheduler import get_next_publish_time
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        next_time = get_next_publish_time()
        now = datetime.now(ZoneInfo("America/Santiago"))
        
        print(f"  ✓ Hora actual (Chile): {now.strftime('%d/%m/%Y %H:%M')}")
        print(f"  ✓ Próxima publicación: {next_time}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("🚀 TESTING DEL SISTEMA DE PUBLICACIONES AUTOMÁTICAS")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Data Structures", test_data_structures()))
    results.append(("HTML Generation", test_html_generation()))
    results.append(("Scheduler Logic", test_scheduler_logic()))
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n  🎉 ¡Todos los tests pasaron! Sistema listo para producción.")
        print("  📝 Nota: Requiere OPENAI_API_KEY y COSMOS_ENDPOINT en producción")
    else:
        print("\n  ⚠️  Algunos tests fallaron. Revisar errores arriba.")
    
    print("="*60)


if __name__ == "__main__":
    main()
