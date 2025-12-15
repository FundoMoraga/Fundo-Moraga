"""
Script de prueba para la captura natural de información y envío de emails
"""
import sys
from instagram_bot import InstagramBot

def test_lead_capture():
    """
    Prueba el flujo completo de captura de información y envío de email
    """
    print("=" * 70)
    print("🧪 PRUEBA: Captura Natural de Información y Envío de Emails")
    print("=" * 70)
    print()
    
    bot = InstagramBot()
    test_user_id = "test_user_123"
    
    print("📝 Simulando conversación natural donde el usuario comparte información...")
    print()
    
    # Mensaje 1: Usuario se presenta
    print("👤 Usuario: Hola, soy María González")
    response1 = bot.process_message(test_user_id, "Hola, soy María González")
    print(f"🤖 Hernando: {response1}")
    print()
    print("-" * 70)
    print()
    
    # Mensaje 2: Usuario expresa su interés
    print("👤 Usuario: Quiero cotizar un evento corporativo para 80 personas en marzo")
    response2 = bot.process_message(test_user_id, "Quiero cotizar un evento corporativo para 80 personas en marzo")
    print(f"🤖 Hernando: {response2}")
    print()
    print("-" * 70)
    print()
    
    # Mensaje 3: Usuario comparte su contacto
    print("👤 Usuario: Mi email es maria.gonzalez@empresa.com y mi teléfono es +56 9 8765 4321")
    response3 = bot.process_message(test_user_id, "Mi email es maria.gonzalez@empresa.com y mi teléfono es +56 9 8765 4321")
    print(f"🤖 Hernando: {response3}")
    print()
    print("-" * 70)
    print()
    
    # Si la captura fue exitosa, se habrá enviado un email
    if "he registrado tu consulta" in response3.lower():
        print("✅ ÉXITO: Información capturada y email enviado")
        print()
        print("📧 Verifica tu bandeja de entrada en contacto@fundomoraga.com")
        print("   para confirmar la recepción del email con el resumen del lead")
    else:
        print("⚠️ La captura puede necesitar más contexto en la conversación")
        print("   Prueba agregando más mensajes donde el usuario comparta información")
    
    print()
    print("=" * 70)
    print("🧪 Prueba completada")
    print("=" * 70)

def test_offroad_info():
    """
    Prueba que la información de Off-Road esté actualizada con horarios y precios
    """
    print()
    print("=" * 70)
    print("🧪 PRUEBA: Información Actualizada de Off-Road")
    print("=" * 70)
    print()
    
    bot = InstagramBot()
    test_user_id = "test_user_offroad_456"
    
    print("👤 Usuario: ¿Cuáles son los horarios y precios de las actividades off-road?")
    response = bot.process_message(test_user_id, "¿Cuáles son los horarios y precios de las actividades off-road?")
    print(f"🤖 Hernando: {response}")
    print()
    
    # Verificar que la respuesta incluya la información actualizada
    check_items = [
        ("Lunes a Viernes" in response or "9:00" in response, "Horarios entre semana"),
        ("$15.000" in response or "$15,000" in response, "Precios"),
        ("$200.000" in response or "$200,000" in response, "Precio fin de semana")
    ]
    
    print("-" * 70)
    print("📊 Verificación de información:")
    print()
    for check, description in check_items:
        status = "✅" if check else "❌"
        print(f"  {status} {description}")
    
    print()
    print("=" * 70)
    print("🧪 Prueba completada")
    print("=" * 70)

if __name__ == "__main__":
    print("\n")
    print("🚀 INICIANDO PRUEBAS DE FUNCIONALIDADES NUEVAS")
    print()
    
    try:
        # Prueba 1: Captura de información
        test_lead_capture()
        
        print("\n\n")
        
        # Prueba 2: Info de Off-Road
        test_offroad_info()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
