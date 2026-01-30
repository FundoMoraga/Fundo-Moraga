#!/usr/bin/env python3
"""
Test para verificar que el cache de OpenAI funciona correctamente
"""
import time
import sys
from openai_client import get_chatbot_ai

def test_cache_functionality():
    """Prueba que el cache de respuestas OpenAI funciona"""
    print("\n" + "="*80)
    print("TEST: Cache de Respuestas OpenAI")
    print("="*80)
    
    try:
        ai = get_chatbot_ai()
        
        # Test 1: Verificar generación de cache key
        print("\n[TEST 1] Generación de Cache Keys")
        print("-" * 80)
        
        test_cases = [
            ("user1", "Hola", None, True, "Saludo -> debe cachear"),
            ("user1", "¿Qué es Batuco?", None, True, "FAQ -> debe cachear"),
            ("user1", "Mi reserva es mañana", None, False, "Datos personales -> NO cachear"),
            ("user1", "Busca información sobre turismo", None, False, "Búsqueda -> NO cachear"),
            ("user1", "¿Me ayudas?", None, True, "Ayuda -> debe cachear"),
        ]
        
        for user_id, message, persona, should_cache, description in test_cases:
            key = ai._get_cache_key_for_response(user_id, message, persona)
            result = key is not None
            status = "✅" if result == should_cache else "❌"
            print(f"{status} {description}")
            print(f"   Mensaje: '{message}'")
            print(f"   Key: {key if key else 'None (correcto)'}")
        
        # Test 2: Verificar que el cache funciona end-to-end
        print("\n[TEST 2] Cache End-to-End (si Redis está disponible)")
        print("-" * 80)
        
        from redis_cache import get_redis_cache
        cache = get_redis_cache()
        
        if not cache.enabled:
            print("⚠️  Redis no está disponible - Test omitido")
            return
        
        print("Redis está disponible, ejecutando test...")
        
        # Primera llamada: debe generar respuesta (MISS)
        print("\n1️⃣ Primera llamada: 'Hola' (esperado MISS)")
        start = time.time()
        resp1 = ai.generate_response("Hola", user_id="test_user_cache_1")
        duration1 = time.time() - start
        print(f"   Tiempo: {duration1*1000:.0f}ms")
        print(f"   Respuesta (primeras 100 chars): {resp1[:100] if isinstance(resp1, str) else '(dict)'}...")
        
        # Segunda llamada: debe venir del cache (HIT)
        print("\n2️⃣ Segunda llamada: 'Hola' (esperado HIT desde cache)")
        start = time.time()
        resp2 = ai.generate_response("Hola", user_id="test_user_cache_2")
        duration2 = time.time() - start
        print(f"   Tiempo: {duration2*1000:.0f}ms")
        print(f"   Respuesta: {resp2[:100] if isinstance(resp2, str) else '(dict)'}...")
        
        # Verificar mejora
        if duration2 < duration1 / 10:  # Si es 10x más rápido
            print(f"\n✅ Cache funciona! Mejora: {duration1/duration2:.1f}x más rápido")
        else:
            print(f"\n⚠️  Cache puede no estar funcionando correctamente")
            print(f"   Primera llamada: {duration1*1000:.0f}ms")
            print(f"   Segunda llamada: {duration2*1000:.0f}ms")
            print(f"   Ratio: {duration1/duration2:.1f}x")
        
        # Test 3: Verificar que NO cachea búsquedas
        print("\n[TEST 3] Búsquedas NO se cachean")
        print("-" * 80)
        
        key_search = ai._get_cache_key_for_response("user", "Busca información sobre turismo", None)
        if key_search is None:
            print("✅ Búsquedas correctamente excluidas del cache")
        else:
            print("❌ ERROR: Búsquedas no debería cachearse")
        
        # Test 4: Verificar que NO cachea datos personales
        print("\n[TEST 4] Datos personales NO se cachean")
        print("-" * 80)
        
        key_personal = ai._get_cache_key_for_response("user", "Mi reserva es para mañana", None)
        if key_personal is None:
            print("✅ Datos personales correctamente excluidos del cache")
        else:
            print("❌ ERROR: Datos personales no debería cachearse")
        
        print("\n" + "="*80)
        print("TEST COMPLETADO")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_cache_functionality()
