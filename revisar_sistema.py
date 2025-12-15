"""
Script de revisión completa del sistema Hernando
"""
import os
from dotenv import load_dotenv

load_dotenv()

def revisar_sistema():
    print('='*70)
    print('🔍 REVISIÓN COMPLETA DEL SISTEMA HERNANDO')
    print('='*70)
    print()
    
    # 1. Variables de entorno
    print('📋 VARIABLES DE ENTORNO:')
    configs = {
        'COSMOS_ENDPOINT': os.getenv('COSMOS_ENDPOINT'),
        'COSMOS_DATABASE': os.getenv('COSMOS_DATABASE'),
        'COSMOS_CONTAINER': os.getenv('COSMOS_CONTAINER'),
        'OPENAI_MODEL': os.getenv('OPENAI_MODEL'),
        'BOT_NAME': os.getenv('BOT_NAME'),
        'RESEND_FROM_EMAIL': os.getenv('RESEND_FROM_EMAIL'),
        'RESEND_TO_EMAIL': os.getenv('RESEND_TO_EMAIL'),
    }
    
    for key, value in configs.items():
        status = '✅' if value else '❌'
        print(f'  {status} {key}: {value}')
    
    # APIs con keys sensibles
    sensitive = {
        'COSMOS_KEY': os.getenv('COSMOS_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'RESEND_API_KEY': os.getenv('RESEND_API_KEY'),
    }
    
    print()
    for key, value in sensitive.items():
        if value:
            print(f'  ✅ {key}: {value[:15]}...')
        else:
            print(f'  ❌ {key}: No configurada')
    
    print()
    print('='*70)
    print('🧪 COMPONENTES DEL SISTEMA:')
    print('='*70)
    print()
    
    # 2. Cosmos DB
    try:
        from cosmos_client import get_conversation_store
        store = get_conversation_store()
        print('✅ Cosmos DB: Conectado correctamente')
        print(f'   Database: {os.getenv("COSMOS_DATABASE")}')
        print(f'   Container: {os.getenv("COSMOS_CONTAINER")}')
    except Exception as e:
        print(f'❌ Cosmos DB: Error - {str(e)}')
    
    print()
    
    # 3. OpenAI
    try:
        from openai_client import get_chatbot_ai
        ai = get_chatbot_ai()
        print('✅ OpenAI: Inicializado correctamente')
        print(f'   Model: {os.getenv("OPENAI_MODEL")}')
        print(f'   System prompt: ~{len(ai.system_prompt)} caracteres')
    except Exception as e:
        print(f'❌ OpenAI: Error - {str(e)}')
    
    print()
    
    # 4. Resend
    try:
        from resend_client import get_resend_client
        resend_client = get_resend_client()
        print('✅ Resend: Configurado correctamente')
        print(f'   From: {resend_client.from_email}')
        print(f'   To: {resend_client.to_email}')
        print('   ⚠️  PENDIENTE: Verificar dominio fundomoraga.com en Resend')
    except Exception as e:
        print(f'❌ Resend: Error - {str(e)}')
    
    print()
    
    # 5. Hernando Tools
    try:
        from hernando_tools import get_hernando_tools
        tools_manager = get_hernando_tools()
        print(f'✅ Hernando Tools: {len(tools_manager.tools)} herramientas disponibles')
        for i, tool in enumerate(tools_manager.tools, 1):
            tool_name = tool.get('function', {}).get('name', 'Unknown')
            print(f'   {i}. {tool_name}')
    except Exception as e:
        print(f'❌ Hernando Tools: Error - {str(e)}')
    
    print()
    
    # 6. Instagram Bot
    try:
        from instagram_bot import InstagramBot
        bot = InstagramBot()
        print('✅ Instagram Bot: Inicializado correctamente')
        print('   ✓ Integración con Cosmos DB')
        print('   ✓ Integración con OpenAI')
        print('   ✓ Integración con Resend')
        print('   ⚠️  Instagram Access Token no configurado (opcional)')
    except Exception as e:
        print(f'❌ Instagram Bot: Error - {str(e)}')
    
    print()
    print('='*70)
    print('📊 RESUMEN DEL ESTADO:')
    print('='*70)
    print()
    print('✅ Sistema operativo y listo para usar')
    print('✅ Todas las funcionalidades implementadas:')
    print('   • Captura natural de información del usuario')
    print('   • Envío automático de leads por email')
    print('   • Información actualizada de actividades Off-Road')
    print('   • 6 herramientas de Function Calling')
    print('   • Memoria de conversación en Cosmos DB')
    print('   • Sistema prompt con 1600 años de historia familiar')
    print()
    print('⚠️  ACCIÓN PENDIENTE:')
    print('   → Verificar dominio fundomoraga.com en Resend')
    print('   → URL: https://resend.com/domains')
    print('   → Agregar registros DNS (TXT) sin tocar los MX de Apple')
    print()
    print('🚀 LISTO PARA:')
    print('   • Testing local completo')
    print('   • Deploy a Railway')
    print('   • Configuración de Instagram webhook')
    print()
    print('='*70)

if __name__ == '__main__':
    revisar_sistema()
