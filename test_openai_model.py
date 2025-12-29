"""
Script para verificar si el modelo gpt-5.2 funciona con la API de OpenAI
"""
from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

print(f"🧪 Probando modelo: {config.OPENAI_MODEL}")
print(f"   API Key: {config.OPENAI_API_KEY[:20]}...")

try:
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "user", "content": "Responde solo: OK"}
        ],
        max_completion_tokens=10  # GPT-5.2 usa max_completion_tokens en lugar de max_tokens
    )
    
    print(f"\n✅ ÉXITO - El modelo {config.OPENAI_MODEL} funciona correctamente")
    print(f"   Respuesta: {response.choices[0].message.content}")
    print(f"   Modelo usado: {response.model}")
    print(f"   Tokens: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"\n❌ ERROR - El modelo {config.OPENAI_MODEL} NO funciona")
    print(f"   Tipo de error: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")
    
    if "does not exist" in str(e).lower() or "not found" in str(e).lower():
        print(f"\n💡 SOLUCIÓN: El modelo '{config.OPENAI_MODEL}' no existe en OpenAI.")
        print(f"   Modelos válidos disponibles:")
        print(f"   - gpt-4o (recomendado para producción)")
        print(f"   - gpt-4o-mini (recomendado para chatbots - más económico)")
        print(f"   - gpt-4-turbo")
        print(f"   - gpt-3.5-turbo")
