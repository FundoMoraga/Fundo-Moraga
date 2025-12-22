"""
Script para integrar advanced_ai_integration en instagram_bot.py
"""
import re

def integrate_advanced_ai():
    """Integra los módulos de IA avanzada en instagram_bot.py"""
    
    # Leer archivo
    with open("instagram_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Agregar import
    if "from advanced_ai_integration import get_advanced_ai_integration" not in content:
        import_line = "from advanced_ai_integration import get_advanced_ai_integration\n"
        # Agregar después de la última importación de payment_inbox_client
        content = content.replace(
            "from payment_inbox_client import get_payment_inbox_client, PaymentCheckResult\n",
            "from payment_inbox_client import get_payment_inbox_client, PaymentCheckResult\n" + import_line
        )
        print("✅ Import agregado")
    
    # 2. Agregar inicialización en __init__
    if "self.ai_integration = get_advanced_ai_integration()" not in content:
        content = content.replace(
            "        self.memory_store = get_memory_store()\n",
            "        self.memory_store = get_memory_store()\n        self.ai_integration = get_advanced_ai_integration()\n"
        )
        print("✅ Inicialización agregada en __init__")
    
    # 3. Agregar enriquecimiento después de obtener historial
    enrichment_code = '''
            # 3.5 Enriquecer mensaje con IA avanzada (intent, entities, predictions, recommendations)
            ai_enrichment = None
            try:
                sentiment_label = sentiment_data.get("sentiment") if sentiment_data else None
                ai_enrichment = self.ai_integration.enrich_user_message(
                    user_id=user_id,
                    message=message_text,
                    conversation_history=conversation_history,
                    sentiment=sentiment_label,
                    user_metadata=user_metadata
                )
                print(f"🧠 IA Avanzada:")
                print(f"   Intent: {ai_enrichment['intent']['intent']} ({ai_enrichment['intent']['confidence']:.0%})")
                if ai_enrichment['entities']['dates']:
                    print(f"   Fechas: {ai_enrichment['entities']['dates']}")
                if ai_enrichment['predictions']['predicted_needs']:
                    print(f"   Predicción: {ai_enrichment['predictions']['predicted_needs'][0] if ai_enrichment['predictions']['predicted_needs'] else 'N/A'}")
                if ai_enrichment['recommendations']['primary_recommendation']:
                    print(f"   Recomendación: {ai_enrichment['recommendations']['primary_recommendation']['activity']}")
            except Exception as e:
                print(f"⚠️ Error en enriquecimiento IA: {e}")
'''
    
    if "ai_enrichment = None" not in content:
        # Buscar la sección donde se recupera el historial
        pattern = r"(            conversation_history = self\.conversation_store\.get_conversation_history\(\n.*?\n.*?\n            \))\n\n(            platform = platform_label)"
        replacement = r"\1" + enrichment_code + "\n\2"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("✅ Enriquecimiento IA agregado")
    
    # 4. Agregar combinación de contexto antes de generate_response
    context_code = '''
            # Combinar lead_context con el contexto enriquecido de IA
            combined_context = lead_context
            if ai_enrichment and ai_enrichment.get('enriched_context'):
                combined_context = (lead_context + "\\n\\n" + ai_enrichment['enriched_context']).strip()

'''
    
    if "combined_context = lead_context" not in content:
        content = content.replace(
            "            prompt_platform = \"Web\"\n\n            ai_result = self.chatbot_ai.generate_response(",
            f"            prompt_platform = \"Web\"\n{context_code}            ai_result = self.chatbot_ai.generate_response("
        )
        # Reemplazar extra_context
        content = content.replace(
            "                extra_context=lead_context,\n                return_events=True,",
            "                extra_context=combined_context,\n                return_events=True,"
        )
        print("✅ Contexto combinado agregado")
    
    # 5. Agregar registro de interacción después de guardar resumen
    interaction_log_code = '''
            # 6.5 Registrar interacción para aprendizaje continuo
            if ai_enrichment:
                try:
                    # Determinar satisfacción basada en sentimiento
                    satisfaction_score = 0.5  # neutral por defecto
                    if sentiment_data:
                        sentiment_scores = sentiment_data
                        if sentiment_scores.get('positive', 0) > 0.6:
                            satisfaction_score = 0.8
                        elif sentiment_scores.get('negative', 0) > 0.6:
                            satisfaction_score = 0.2
                    
                    self.ai_integration.log_interaction_result(
                        user_id=user_id,
                        intent=ai_enrichment['intent']['intent'],
                        was_successful=(satisfaction_score > 0.5),
                        satisfaction_score=satisfaction_score,
                        response_generated=bool(response_text and len(response_text) > 10)
                    )
                    print(f"📊 Interacción registrada (satisfacción: {satisfaction_score:.0%})")
                except Exception as e:
                    print(f"⚠️ Error registrando interacción: {e}")
'''
    
    if "# 6.5 Registrar interacción para aprendizaje continuo" not in content:
        # Buscar después de guardar resumen en Memoria
        pattern = r"(            except Exception as e:\n                print\(f\"⚠️ No se pudo guardar el resumen en Memoria: \{e\}\"\))\n\n(            # 7\. Si el modelo ejecutó herramientas)"
        replacement = r"\1" + interaction_log_code + "\n\2"
        content = re.sub(pattern, replacement, content)
        print("✅ Registro de interacción agregado")
    
    # Guardar archivo
    with open("instagram_bot.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("\n✅ Integración completada exitosamente")
    print("📝 Cambios realizados:")
    print("   1. Import de advanced_ai_integration")
    print("   2. Inicialización en __init__")
    print("   3. Enriquecimiento de mensajes con IA")
    print("   4. Contexto combinado para GPT")
    print("   5. Registro de interacciones")

if __name__ == "__main__":
    integrate_advanced_ai()
