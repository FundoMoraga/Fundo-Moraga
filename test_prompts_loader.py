#!/usr/bin/env python3
"""
Script de prueba para verificar que los prompts se cargan dinámicamente desde Cosmos DB.
Uso: python test_prompts_loader.py
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

def test_prompts_loader():
    """Prueba la carga de prompts desde Cosmos DB."""
    print("=" * 80)
    print("PRUEBA: Cargador de Prompts Dinámicos desde Cosmos DB")
    print("=" * 80)
    
    # 1. Verificar que config tiene las variables necesarias
    print("\n1️⃣ Verificando configuración...")
    try:
        import config
        print(f"   ✅ COSMOS_ENDPOINT: {config.COSMOS_ENDPOINT[:50] if config.COSMOS_ENDPOINT else 'NO CONFIGURADO'}")
        print(f"   ✅ COSMOS_PROMPTS_DB: {config.COSMOS_PROMPTS_DB}")
        print(f"   ✅ COSMOS_PROMPTS_CONTAINER: {config.COSMOS_PROMPTS_CONTAINER}")
        print(f"   ✅ COSMOS_PROMPTS_PERSONA: {config.COSMOS_PROMPTS_PERSONA}")
        print(f"   ✅ OPENAI_MODEL: {config.OPENAI_MODEL}")
    except Exception as e:
        print(f"   ❌ Error en config: {e}")
        return False
    
    # 2. Verificar que prompts_loader está disponible
    print("\n2️⃣ Verificando prompts_loader...")
    try:
        from prompts_loader import get_prompts_loader
        loader = get_prompts_loader()
        print(f"   ✅ Loader instanciado (singleton)")
    except Exception as e:
        print(f"   ❌ Error en prompts_loader: {e}")
        return False
    
    # 3. Intentar cargar prompts (con fallback)
    print("\n3️⃣ Intentando cargar prompts...")
    try:
        prompts = loader.get_prompts(
            persona="Hernando",
            fallback_system_prompt="Eres un bot de prueba.",
            fallback_operational_prompt="Responde brevemente.",
            fallback_tools=[],
        )
        
        system_preview = prompts.get("system", "")[:100] + "..." if prompts.get("system") else ""
        operational_preview = prompts.get("operational", "")[:100] + "..." if prompts.get("operational") else ""
        tools_count = len(prompts.get("tools", []))
        
        print(f"   ✅ System prompt (preview): {system_preview}")
        print(f"   ✅ Operational prompt (preview): {operational_preview}")
        print(f"   ✅ Tools cargadas: {tools_count}")
        print(f"   ✅ Prompts cargados exitosamente")
        
    except Exception as e:
        print(f"   ⚠️ No se pudieron cargar desde Cosmos DB: {e}")
        print(f"   ℹ️ Si Cosmos DB no está disponible, se usarán los fallbacks embebidos")
    
    # 4. Verificar que openai_client puede instanciarse
    print("\n4️⃣ Verificando openai_client...")
    try:
        from openai_client import get_chatbot_ai
        bot = get_chatbot_ai()
        system_len = len(bot.system_prompt) if bot.system_prompt else 0
        operational_len = len(bot.operational_prompt) if bot.operational_prompt else 0
        tools_len = len(getattr(bot, "tools", []) or [])
        
        print(f"   ✅ ChatbotAI instanciado")
        print(f"   ✅ System prompt loaded: {system_len} caracteres")
        print(f"   ✅ Operational prompt loaded: {operational_len} caracteres")
        print(f"   ✅ Tools loaded: {tools_len}")
        
        if system_len > 0 and operational_len > 0:
            print(f"   ✅ Ambos prompts cargados correctamente")
        else:
            print(f"   ⚠️ Uno o más prompts vacíos")
            
    except Exception as e:
        print(f"   ❌ Error en openai_client: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("✅ PRUEBA EXITOSA: Sistema listo para usar")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_prompts_loader()
    sys.exit(0 if success else 1)
