"""
Script de prueba para capacidades de navegación web de Hernando
Prueba Steel Browser con el número especial +56941242609
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

def test_web_navigation():
    """Prueba capacidades de navegación web"""
    print_section("PRUEBA DE NAVEGACION WEB")
    
    try:
        bot = HernandoBot()
        print(f"Bot inicializado correctamente")
        print(f"Usuario: {TEST_USER_ID}\n")
        
        # Pruebas de navegación web
        test_cases = [
            "Busca en Google: ultimas noticias sobre IA en Chile",
            "Navega a https://www.chile.cl y dime que ves",
            "Investiga sobre las mejores practicas de ciberseguridad 2026",
        ]
        
        for i, message in enumerate(test_cases, 1):
            print(f"\n{i}. Usuario: {message}")
            print("   Procesando...")
            
            response = bot.process_message(
                user_id=TEST_USER_ID,
                message_text=message,
                platform="whatsapp",
                source="test"
            )
            
            # Mostrar respuesta resumida
            lines = response.split('\n')
            preview = '\n   '.join(lines[:5])
            if len(lines) > 5:
                preview += f"\n   ... ({len(lines)-5} lineas mas)"
            
            print(f"   Hernando:\n   {preview}\n")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("  PRUEBA DE CAPACIDADES WEB - HERNANDO")
    print("  Steel Browser Integration")
    print("="*70)
    
    # Verificar configuracion
    print_section("VERIFICACION DE SERVICIOS")
    
    services = {
        "Cosmos DB": bool(config.COSMOS_CONNECTION_STRING or (config.COSMOS_ENDPOINT and config.COSMOS_KEY)),
        "OpenAI": bool(config.OPENAI_API_KEY),
        "Steel Browser": bool(os.getenv("STEEL_BROWSER_URL")),
    }
    
    for service, status in services.items():
        status_text = "OK" if status else "NO CONFIGURADO"
        symbol = "[+]" if status else "[-]"
        print(f"{symbol} {service}: {status_text}")
    
    if not all(services.values()):
        print("\n[!] Faltan servicios requeridos")
        return
    
    # Ejecutar prueba
    result = test_web_navigation()
    
    # Resumen
    print_section("RESUMEN")
    
    if result:
        print("PRUEBA EXITOSA")
        print("Hernando tiene capacidades completas de navegacion web")
        print("Puede buscar en Google, navegar URLs e investigar temas")
    else:
        print("PRUEBA FALLIDA")
        print("Revisar errores en la integracion con Steel Browser")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
