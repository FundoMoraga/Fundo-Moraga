"""
Reporte de Pruebas Hernando WhatsApp
Verificación del número +569 4 1242609
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instagram_bot_enhanced import InstagramBotEnhanced as HernandoBot
import config

# Configurar salida UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

TEST_PHONE = "+56941242609"
TEST_USER_ID = f"wa_{TEST_PHONE}@s.whatsapp.net"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def test_whatsapp_connection():
    """Prueba la configuración de WhatsApp"""
    print_section("CONFIGURACIÓN DE WHATSAPP")
    
    print(f"Numero de prueba: {TEST_PHONE}")
    print(f"User ID: {TEST_USER_ID}")
    print(f"WAHA URL: {config.WAHA_API_URL or 'No configurado'}")
    print(f"WAHA Session: {config.WAHA_SESSION}")
    print(f"WAHA Key: {'Configurado' if config.WAHA_API_KEY else 'No configurado'}")
    
    # Verificar si el número está en la lista especial
    numeros_especiales = getattr(config, 'SPECIAL_PERSONA_WHATSAPP_NUMBERS', [])
    en_lista_especial = TEST_PHONE in numeros_especiales
    
    print(f"\nNumero en lista especial: {'SI' if en_lista_especial else 'NO'}")
    if numeros_especiales:
        print(f"Numeros especiales configurados: {', '.join(numeros_especiales)}")
    
    return bool(config.WAHA_API_URL)

def test_conversation():
    """Prueba una conversación básica"""
    print_section("PRUEBA DE CONVERSACION")
    
    try:
        bot = HernandoBot()
        print("Bot inicializado correctamente\n")
        
        messages = [
            "Hola, quiero informacion sobre el fundo",
            "Cuanto cuesta ir?",
            "Quiero reservar para el proximo sabado"
        ]
        
        for i, msg in enumerate(messages, 1):
            print(f"{i}. Usuario: {msg}")
            
            response = bot.process_message(
                user_id=f"{TEST_USER_ID}_test{i}",
                message_text=msg,
                platform="whatsapp",
                source="waha"
            )
            
            # Mostrar solo primeras líneas
            lines = response.split('\n')
            preview = '\n   '.join(lines[:3])
            if len(lines) > 3:
                preview += "\n   ..."
            
            print(f"   Hernando: {preview}\n")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("  REPORTE DE PRUEBAS - HERNANDO WHATSAPP")
    print("  Fundo Moraga")
    print("="*70)
    
    # Verificar configuración general
    print_section("VERIFICACION DE SERVICIOS")
    
    services = {
        "Cosmos DB": bool(config.COSMOS_CONNECTION_STRING or (config.COSMOS_ENDPOINT and config.COSMOS_KEY)),
        "OpenAI": bool(config.OPENAI_API_KEY),
        "WhatsApp (WAHA)": bool(config.WAHA_API_URL),
        "Google Calendar": bool(config.GOOGLE_CALENDAR_ID),
        "Payment Inbox": bool(config.PAYMENT_INBOX_USER),
    }
    
    for service, status in services.items():
        status_text = "OK" if status else "NO CONFIGURADO"
        symbol = "[+]" if status else "[-]"
        print(f"{symbol} {service}: {status_text}")
    
    # Ejecutar pruebas
    print("\n")
    waha_ok = test_whatsapp_connection()
    conv_ok = test_conversation()
    
    # Resumen
    print_section("RESUMEN")
    
    print(f"Configuracion de WhatsApp: {'OK' if waha_ok else 'FALTA CONFIGURAR'}")
    print(f"Prueba de conversacion: {'EXITOSA' if conv_ok else 'FALLIDA'}")
    
    if waha_ok and conv_ok:
        print("\nTODO FUNCIONANDO CORRECTAMENTE")
        print(f"Hernando esta listo para responder mensajes de WhatsApp")
        print(f"Numero de prueba: {TEST_PHONE}")
    else:
        print("\nSE REQUIERE ATENCION")
        if not waha_ok:
            print("- Configurar WAHA para envio de mensajes")
        if not conv_ok:
            print("- Revisar errores en el procesamiento de mensajes")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
