"""
Auditoría completa del sistema Hernando con IA avanzada
Verifica todos los componentes y hace pruebas de integración
"""
import sys
import os
import traceback
from datetime import datetime

# Forzar UTF-8 en Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_section(title):
    """Imprime sección de la auditoría"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_module(module_name, check_func=None):
    """Verifica que un módulo se pueda importar y ejecutar checks"""
    try:
        module = __import__(module_name)
        print(f"✅ {module_name} - Importado correctamente")
        if check_func:
            check_func(module)
        return True
    except Exception as e:
        print(f"❌ {module_name} - Error: {e}")
        traceback.print_exc()
        return False

def audit_core_modules():
    """Audita módulos core del sistema"""
    print_section("1. MÓDULOS CORE")
    
    results = {}
    results['config'] = check_module('config')
    results['cosmos_client'] = check_module('cosmos_client')
    results['openai_client'] = check_module('openai_client')
    results['language_client'] = check_module('language_client')
    results['conversation_manager'] = check_module('conversation_manager')
    
    return results

def audit_ai_modules():
    """Audita los 6 módulos de IA avanzada"""
    print_section("2. MÓDULOS DE IA AVANZADA")
    
    results = {}
    
    # 1. Intent Classifier
    try:
        from intent_classifier import get_intent_classifier
        classifier = get_intent_classifier()
        print("✅ intent_classifier - OK")
        
        # Test básico
        result = classifier.classify("Quiero reservar para el sábado", [])
        print(f"   Test: Intent={result['intent']}, Confidence={result['confidence']:.0%}")
        results['intent_classifier'] = True
    except Exception as e:
        print(f"❌ intent_classifier - Error: {e}")
        results['intent_classifier'] = False
    
    # 2. Entity Extractor
    try:
        from entity_extractor import get_entity_extractor
        extractor = get_entity_extractor()
        print("✅ entity_extractor - OK")
        
        # Test básico
        entities = extractor.extract_entities("Quiero ir el 28 de diciembre con 3 motos")
        print(f"   Test: Fechas={len(entities['dates'])}, Cantidades={len(entities['quantities'])}")
        results['entity_extractor'] = True
    except Exception as e:
        print(f"❌ entity_extractor - Error: {e}")
        results['entity_extractor'] = False
    
    # 3. Continuous Learning
    try:
        from continuous_learning import get_continuous_learning
        learning = get_continuous_learning()
        print("✅ continuous_learning - OK")
        results['continuous_learning'] = True
    except Exception as e:
        print(f"❌ continuous_learning - Error: {e}")
        results['continuous_learning'] = False
    
    # 4. Prediction Engine
    try:
        from prediction import get_prediction_engine
        predictor = get_prediction_engine()
        print("✅ prediction - OK")
        results['prediction'] = True
    except Exception as e:
        print(f"❌ prediction - Error: {e}")
        results['prediction'] = False
    
    # 5. Recommendation Engine
    try:
        from recommendation import get_recommendation_engine
        recommender = get_recommendation_engine()
        print("✅ recommendation - OK")
        
        # Test básico
        rec = recommender.recommend("test_user", {}, "consulta", "")
        print(f"   Test: {len(recommender.activity_catalog)} actividades en catálogo")
        results['recommendation'] = True
    except Exception as e:
        print(f"❌ recommendation - Error: {e}")
        results['recommendation'] = False
    
    # 6. Advanced AI Integration
    try:
        from advanced_ai_integration import get_advanced_ai_integration
        ai_integration = get_advanced_ai_integration()
        print("✅ advanced_ai_integration - OK")
        results['advanced_ai_integration'] = True
    except Exception as e:
        print(f"❌ advanced_ai_integration - Error: {e}")
        results['advanced_ai_integration'] = False
    
    return results

def audit_bot_integration():
    """Audita la integración del bot mejorado"""
    print_section("3. INTEGRACIÓN DEL BOT")
    
    results = {}
    
    # Bot original
    try:
        from instagram_bot import InstagramBot
        print("✅ InstagramBot (original) - OK")
        results['instagram_bot'] = True
    except Exception as e:
        print(f"❌ InstagramBot - Error: {e}")
        results['instagram_bot'] = False
    
    # Bot mejorado
    try:
        from instagram_bot_enhanced import InstagramBotEnhanced
        print("✅ InstagramBotEnhanced - OK")
        
        # Verificar que tiene ai_integration
        bot = InstagramBotEnhanced()
        if hasattr(bot, 'ai_integration'):
            print("   ✅ ai_integration inicializado")
        else:
            print("   ⚠️  ai_integration NO encontrado")
        
        results['instagram_bot_enhanced'] = True
    except Exception as e:
        print(f"❌ InstagramBotEnhanced - Error: {e}")
        traceback.print_exc()
        results['instagram_bot_enhanced'] = False
    
    # Server
    try:
        from server import InstagramBot as ServerBot
        print("✅ server.py usando bot correcto")
        print(f"   Clase: {ServerBot.__name__}")
        results['server'] = True
    except Exception as e:
        print(f"❌ server.py - Error: {e}")
        results['server'] = False
    
    return results

def test_full_flow():
    """Prueba el flujo completo con un mensaje"""
    print_section("4. PRUEBA DE FLUJO COMPLETO")
    
    try:
        from instagram_bot_enhanced import InstagramBotEnhanced
        from cosmos_client import get_conversation_store
        
        print("🧪 Iniciando prueba con mensaje de ejemplo...")
        
        # Crear bot
        bot = InstagramBotEnhanced()
        print("✅ Bot inicializado")
        
        # Mensaje de prueba
        test_message = "Hola, quisiera reservar para el próximo sábado con 2 motos"
        test_user_id = f"audit_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n📝 Usuario: {test_user_id}")
        print(f"📝 Mensaje: {test_message}")
        print("\n🔄 Procesando mensaje...\n")
        
        # Procesar mensaje (esto debería mostrar los logs de IA)
        response = bot.process_message(
            user_id=test_user_id,
            message_text=test_message,
            platform="web",
            source="audit_test"
        )
        
        print(f"\n📤 Respuesta generada:")
        print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
        
        # Verificar que se guardó en Cosmos
        store = get_conversation_store()
        conv_id = store.get_latest_conversation_id(test_user_id)
        
        if conv_id:
            history = store.get_conversation_history(test_user_id, conv_id, limit=10)
            print(f"\n✅ Conversación guardada en Cosmos DB")
            print(f"   Conversation ID: {conv_id}")
            print(f"   Mensajes: {len(history)}")
            
            # Verificar si hay metadata de IA
            ai_metadata_found = False
            for msg in history:
                if msg.get('metadata', {}).get('type') == 'ai_enrichment':
                    ai_metadata_found = True
                    print(f"   ✅ Metadata de IA encontrada")
                    break
            
            if not ai_metadata_found:
                print(f"   ⚠️  No se encontró metadata de IA en mensajes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en prueba de flujo: {e}")
        traceback.print_exc()
        return False

def check_cosmos_pricing():
    """Verifica que los precios en Cosmos estén actualizados"""
    print_section("5. VERIFICACIÓN DE PRECIOS EN COSMOS DB")
    
    try:
        from prompts_loader import load_prompts
        
        prompts = load_prompts()
        prompt_text = prompts.get('main', '')
        
        # Verificar precios actualizados
        checks = {
            'Sábado $200.000': '$200.000' in prompt_text and 'sábado' in prompt_text.lower(),
            'Domingo $200.000': '$200.000' in prompt_text and 'domingo' in prompt_text.lower(),
            'Fecha Libre mencionada': 'fecha libre' in prompt_text.lower() or 'fecha-libre' in prompt_text.lower(),
            'Baño disponible': 'baño' in prompt_text.lower(),
            'Lunes-Viernes $15.000': '$15.000' in prompt_text or '$15000' in prompt_text
        }
        
        print("Verificando información actualizada en prompts:")
        all_ok = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            if not result:
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Error verificando precios: {e}")
        return False

def generate_report(results):
    """Genera reporte final de auditoría"""
    print_section("RESUMEN DE AUDITORÍA")
    
    all_results = {}
    for category_results in results:
        all_results.update(category_results)
    
    total = len(all_results)
    passed = sum(1 for v in all_results.values() if v)
    failed = total - passed
    
    print(f"\n📊 Estadísticas:")
    print(f"   Total de checks: {total}")
    print(f"   ✅ Exitosos: {passed}")
    print(f"   ❌ Fallidos: {failed}")
    print(f"   📈 Tasa de éxito: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print(f"\n⚠️  Componentes con problemas:")
        for name, result in all_results.items():
            if not result:
                print(f"   ❌ {name}")
    
    print(f"\n{'='*70}")
    if failed == 0:
        print("✅ TODOS LOS SISTEMAS OPERATIVOS - SISTEMA LISTO PARA PRODUCCIÓN")
    else:
        print(f"⚠️  SE ENCONTRARON {failed} PROBLEMAS - REVISAR COMPONENTES")
    print(f"{'='*70}\n")
    
    return failed == 0

def main():
    """Ejecuta auditoría completa"""
    print("\n" + " AUDITORIA COMPLETA DEL SISTEMA HERNANDO CON IA AVANZADA ".center(70, "="))
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # 1. Módulos core
    results.append(audit_core_modules())
    
    # 2. Módulos de IA
    results.append(audit_ai_modules())
    
    # 3. Integración del bot
    results.append(audit_bot_integration())
    
    # 4. Prueba de flujo completo
    flow_result = test_full_flow()
    results.append({'full_flow_test': flow_result})
    
    # 5. Verificación de precios
    pricing_result = check_cosmos_pricing()
    results.append({'cosmos_pricing': pricing_result})
    
    # Generar reporte
    success = generate_report(results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
