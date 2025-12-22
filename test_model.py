"""
Test rápido para verificar que gpt-5.2 está funcionando
"""
from openai_client import ChatbotAI
import config

def test_model():
    print("="*70)
    print("🤖 VERIFICACIÓN DEL MODELO GPT-5.2")
    print("="*70)
    print()
    
    print(f"📋 Configuración:")
    print(f"   Modelo configurado: {config.OPENAI_MODEL}")
    print()
    
    try:
        # Inicializar cliente
        print("🔄 Inicializando cliente OpenAI...")
        chatbot = ChatbotAI()
        print(f"   ✅ Cliente inicializado")
        print(f"   Modelo activo: {chatbot.model}")
        print()
        
        # Hacer una pregunta simple
        print("💬 Enviando mensaje de prueba...")
        response = chatbot.generate_response(
            user_message="Hola, ¿cuál es tu nombre y qué modelo eres?",
            conversation_history=[],
            conversation_id="test_model_verification",
            platform="Test"
        )
        print()
        print("📝 Respuesta del modelo:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        print()
        
        print("="*70)
        print("✅ MODELO GPT-5.2 FUNCIONANDO CORRECTAMENTE")
        print("="*70)
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ ERROR AL VERIFICAR EL MODELO")
        print("="*70)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model()
