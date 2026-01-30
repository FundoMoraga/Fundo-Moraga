"""
Script de prueba para funcionalidades de Hernando en WhatsApp
Prueba el número: +569 4 1242609
"""
import sys
import os
from datetime import datetime
import json

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from instagram_bot_enhanced import InstagramBotEnhanced as HernandoBot

# Número de prueba
TEST_PHONE = "+56941242609"
TEST_USER_ID = f"wa_{TEST_PHONE}@s.whatsapp.net"

def print_separator(title=""):
    print("\n" + "="*70)
    if title:
        print(f"  {title}")
        print("="*70)
    print()

def test_configuration():
    """Prueba la configuración del sistema"""
    print_separator("VERIFICACIÓN DE CONFIGURACIÓN")
    
    configs = {
        "Cosmos DB": bool(config.COSMOS_CONNECTION_STRING or (config.COSMOS_ENDPOINT and config.COSMOS_KEY)),
        "OpenAI": bool(config.OPENAI_API_KEY),
        "WAHA (WhatsApp)": bool(config.WAHA_API_URL),
        "Azure Language": bool(config.AZURE_LANGUAGE_KEY),
        "Azure Translator": bool(config.AZURE_TRANSLATOR_KEY),
        "Google Calendar": bool(config.GOOGLE_CALENDAR_ID),
        "Payment Inbox": bool(config.PAYMENT_INBOX_USER),
    }
    
    print("Estado de servicios:")
    for service, status in configs.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {'Configurado' if status else 'No configurado'}")
    
    return all([configs["Cosmos DB"], configs["OpenAI"]])

def test_basic_conversation():
    """Prueba una conversación básica"""
    print_separator("PRUEBA 1: CONVERSACIÓN BÁSICA")
    
    try:
        bot = HernandoBot()
        print(f"🤖 Bot inicializado correctamente")
        print(f"📱 Probando con: {TEST_PHONE}")
        print(f"🆔 User ID: {TEST_USER_ID}")
        
        # Mensaje de prueba
        test_message = "Hola, quisiera información sobre el Fundo Moraga"
        print(f"\n💬 Usuario: {test_message}")
        
        response = bot.process_message(
            user_id=TEST_USER_ID,
            message_text=test_message,
            platform="whatsapp",
            source="waha"
        )
        
        print(f"🤖 Hernando: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intent_detection():
    """Prueba detección de intenciones"""
    print_separator("PRUEBA 2: DETECCIÓN DE INTENCIONES")
    
    test_cases = [
        "¿Cuánto cuesta el arriendo?",
        "Quiero hacer una reserva para el próximo sábado",
        "¿Qué horarios tienen disponibles?",
        "¿Aceptan mascotas?",
        "¿Cómo llego al fundo?",
    ]
    
    try:
        bot = HernandoBot()
        
        for i, message in enumerate(test_cases, 1):
            print(f"\n{i}. 💬 Usuario: {message}")
            
            response = bot.process_message(
                user_id=f"{TEST_USER_ID}_intent_{i}",
                message_text=message,
                platform="whatsapp",
                source="test"
            )
            
            # Mostrar solo las primeras líneas de la respuesta
            response_preview = response[:150] + "..." if len(response) > 150 else response
            print(f"   🤖 Respuesta: {response_preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_memory():
    """Prueba la memoria conversacional"""
    print_separator("PRUEBA 3: MEMORIA CONVERSACIONAL")
    
    conversation = [
        "Hola, me llamo Juan",
        "Quiero hacer una reserva",
        "Para 4 personas",
        "¿Cuál es mi nombre?",  # Debe recordar "Juan"
    ]
    
    try:
        bot = HernandoBot()
        memory_user_id = f"{TEST_USER_ID}_memory"
        
        print(f"🆔 Usuario de prueba: {memory_user_id}\n")
        
        for i, message in enumerate(conversation, 1):
            print(f"{i}. 💬 Usuario: {message}")
            
            response = bot.process_message(
                user_id=memory_user_id,
                message_text=message,
                platform="whatsapp",
                source="test"
            )
            
            response_preview = response[:200] + "..." if len(response) > 200 else response
            print(f"   🤖 Hernando: {response_preview}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sentiment_analysis():
    """Prueba análisis de sentimiento"""
    print_separator("PRUEBA 4: ANÁLISIS DE SENTIMIENTO")
    
    test_cases = [
        ("¡Excelente servicio, todo perfecto!", "positivo"),
        ("No me gustó para nada, muy caro", "negativo"),
        ("¿Cuál es el horario?", "neutral"),
        ("Estoy muy emocionado por mi reserva", "positivo"),
    ]
    
    try:
        from language_client import analyze_sentiment
        
        for message, expected in test_cases:
            print(f"\n💬 Mensaje: {message}")
            print(f"   📊 Sentimiento esperado: {expected}")
            
            sentiment = analyze_sentiment(message)
            if sentiment:
                detected = sentiment.get("sentiment", "desconocido")
                score = sentiment.get(detected, 0.0)
                print(f"   ✅ Detectado: {detected} (confianza: {score:.2f})")
            else:
                print(f"   ⚠️ No se pudo analizar el sentimiento")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tools_integration():
    """Prueba integración con herramientas (calendario, pagos, etc.)"""
    print_separator("PRUEBA 5: INTEGRACIÓN CON HERRAMIENTAS")
    
    test_cases = [
        "Quiero reservar para el 15 de febrero",
        "¿Ya recibieron mi transferencia?",
        "Necesito ayuda con mi reserva",
    ]
    
    try:
        bot = HernandoBot()
        tools_user_id = f"{TEST_USER_ID}_tools"
        
        for i, message in enumerate(test_cases, 1):
            print(f"\n{i}. 💬 Usuario: {message}")
            
            response = bot.process_message(
                user_id=tools_user_id,
                message_text=message,
                platform="whatsapp",
                source="test"
            )
            
            response_preview = response[:200] + "..." if len(response) > 200 else response
            print(f"   🤖 Hernando: {response_preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_whatsapp_specific():
    """Prueba funcionalidades específicas de WhatsApp"""
    print_separator("PRUEBA 6: FUNCIONALIDADES ESPECÍFICAS DE WHATSAPP")
    
    print(f"📱 Número de prueba: {TEST_PHONE}")
    print(f"🆔 Chat ID: {TEST_USER_ID}")
    print(f"🌐 WAHA API URL: {config.WAHA_API_URL or 'No configurado'}")
    print(f"🔑 WAHA API Key: {'Configurado' if config.WAHA_API_KEY else 'No configurado'}")
    print(f"📡 WAHA Session: {config.WAHA_SESSION}")
    
    if not config.WAHA_API_URL:
        print("\n⚠️ WAHA no está configurado. Para enviar mensajes reales necesitas:")
        print("   1. WAHA_API_URL: URL de tu instancia WAHA")
        print("   2. WAHA_API_KEY: Clave API de WAHA (opcional)")
        print("   3. WAHA_SESSION: Nombre de la sesión (default: 'default')")
        return False
    
    return True

def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "🚀 "*25)
    print("  PRUEBAS DE HERNANDO - AGENTE DE WHATSAPP")
    print("  Fundo Moraga")
    print("🚀 "*25)
    
    results = []
    
    # Verificar configuración
    if not test_configuration():
        print("\n❌ FALTA CONFIGURACIÓN CRÍTICA")
        print("   Necesitas al menos Cosmos DB y OpenAI configurados")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Conversación Básica", test_basic_conversation),
        ("Detección de Intenciones", test_intent_detection),
        ("Memoria Conversacional", test_conversation_memory),
        ("Análisis de Sentimiento", test_sentiment_analysis),
        ("Integración con Herramientas", test_tools_integration),
        ("Funcionalidades de WhatsApp", test_whatsapp_specific),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️ Pruebas interrumpidas por el usuario")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print_separator("RESUMEN DE PRUEBAS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Pruebas ejecutadas: {total}")
    print(f"Exitosas: {passed} ✅")
    print(f"Fallidas: {total - passed} ❌")
    print(f"Tasa de éxito: {(passed/total*100):.1f}%\n")
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {status} - {test_name}")
    
    print("\n" + "="*70)
    print("  Pruebas completadas")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
