"""
Test de envío de email con Resend después de verificar dominio
"""
from resend_client import get_resend_client

def test_envio_email():
    print("="*70)
    print("📧 PRUEBA DE ENVÍO DE EMAIL CON RESEND")
    print("="*70)
    print()
    
    resend_client = get_resend_client()
    
    print(f"📤 Enviando email de prueba...")
    print(f"   From: {resend_client.from_email}")
    print(f"   To: {resend_client.to_email}")
    print()
    
    # Enviar email de prueba
    result = resend_client.send_conversation_summary(
        user_name="Usuario de Prueba",
        user_interest="Verificación de dominio en Resend - Email de prueba para confirmar que el dominio fundomoraga.com está correctamente configurado y los emails se envían sin errores.",
        user_contact="test@ejemplo.com / +56 9 1234 5678",
        conversation_id="test_verificacion_resend_20251215",
        platform="Test"
    )
    
    print("="*70)
    print("📊 RESULTADO:")
    print("="*70)
    print()
    
    if result["success"]:
        print("✅ EMAIL ENVIADO EXITOSAMENTE")
        print()
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   Timestamp: {result.get('timestamp')}")
        print()
        print("🎉 El dominio fundomoraga.com está correctamente verificado")
        print("📬 Revisa la bandeja de contacto@fundomoraga.com")
        print()
        print("="*70)
        print("✅ SISTEMA 100% OPERATIVO - LISTO PARA PRODUCCIÓN")
        print("="*70)
    else:
        print("❌ ERROR AL ENVIAR EMAIL")
        print()
        print(f"   Error: {result.get('error')}")
        print()
        print("⚠️  Verifica:")
        print("   1. Que el dominio esté completamente verificado en Resend")
        print("   2. Que los registros DNS estén correctos")
        print("   3. Que la API key sea válida")
        print()
        print("="*70)

if __name__ == "__main__":
    test_envio_email()
