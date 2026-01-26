"""
Script para Evaluar las Interacciones de Hernando
Analiza conversaciones reales, métricas de performance y calidad de respuestas
"""
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import Counter
import json

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from cosmos_client import get_conversation_store, get_memory_store


class InteractionEvaluator:
    """Evalúa la calidad de las interacciones de Hernando"""
    
    def __init__(self):
        self.store = get_conversation_store()
        self.memory_store = get_memory_store()
    
    def print_header(self, title: str):
        """Imprime encabezado decorado"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    
    def print_section(self, title: str):
        """Imprime sección"""
        print(f"\n{'-'*80}")
        print(f"  {title}")
        print(f"{'-'*80}\n")
    
    def get_recent_conversations(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """Obtiene conversaciones recientes"""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            query = f"""
                SELECT DISTINCT c.userId, c.conversationId, c.timestamp
                FROM c 
                WHERE c.timestamp >= '{cutoff}'
                AND c.role IN ('user', 'assistant')
                ORDER BY c.timestamp DESC
            """
            
            items = list(self.store.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Agrupar por conversación
            conversations = {}
            for item in items:
                key = f"{item['userId']}_{item['conversationId']}"
                if key not in conversations:
                    conversations[key] = {
                        'user_id': item['userId'],
                        'conversation_id': item['conversationId'],
                        'first_message': item['timestamp']
                    }
            
            return list(conversations.values())[:limit]
            
        except Exception as e:
            print(f"❌ Error obteniendo conversaciones: {e}")
            return []
    
    def get_conversation_details(self, user_id: str, conversation_id: str) -> Dict:
        """Obtiene detalles completos de una conversación"""
        try:
            messages = self.store.get_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=100
            )
            
            if not messages:
                return None
            
            # Analizar conversación
            user_messages = [m for m in messages if m.get('role') == 'user']
            bot_messages = [m for m in messages if m.get('role') == 'assistant']
            
            # Extraer metadata
            sentiments = []
            intents = []
            tools_used = []
            
            for msg in messages:
                metadata = msg.get('metadata', {})
                if metadata.get('sentiment'):
                    sentiments.append(metadata['sentiment'])
                if metadata.get('intent'):
                    intents.append(metadata['intent'])
                if metadata.get('tools_executed'):
                    tools_used.extend(metadata['tools_executed'])
            
            # Calcular duración
            if len(messages) >= 2:
                try:
                    first = datetime.fromisoformat(messages[-1]['timestamp'].replace('Z', '+00:00'))
                    last = datetime.fromisoformat(messages[0]['timestamp'].replace('Z', '+00:00'))
                    duration_minutes = (last - first).total_seconds() / 60
                except:
                    duration_minutes = None
            else:
                duration_minutes = None
            
            return {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'message_count': len(messages),
                'user_message_count': len(user_messages),
                'bot_message_count': len(bot_messages),
                'duration_minutes': duration_minutes,
                'sentiments': sentiments,
                'intents': intents,
                'tools_used': tools_used,
                'messages': messages
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo detalles: {e}")
            return None
    
    def analyze_conversation_quality(self, details: Dict) -> Dict:
        """Analiza la calidad de una conversación"""
        quality = {
            'score': 0,
            'issues': [],
            'strengths': [],
            'category': 'unknown'
        }
        
        score = 100  # Empezar con 100 puntos
        
        # 1. Ratio de mensajes (ideal ~1:1 o 1:1.2)
        if details['user_message_count'] > 0:
            ratio = details['bot_message_count'] / details['user_message_count']
            if 0.8 <= ratio <= 1.5:
                quality['strengths'].append(f"Balance conversacional bueno ({ratio:.1f}:1)")
            elif ratio > 2:
                score -= 15
                quality['issues'].append(f"Bot demasiado verboso ({ratio:.1f}:1)")
            elif ratio < 0.5:
                score -= 10
                quality['issues'].append(f"Bot poco responsivo ({ratio:.1f}:1)")
        
        # 2. Uso de herramientas
        if details['tools_used']:
            unique_tools = set(details['tools_used'])
            quality['strengths'].append(f"Usó {len(unique_tools)} herramientas: {', '.join(unique_tools)}")
            score += 10
        else:
            if details['message_count'] > 4:
                quality['issues'].append("No usó herramientas en conversación larga")
                score -= 5
        
        # 3. Análisis de sentimiento
        if details['sentiments']:
            sentiment_counts = Counter(details['sentiments'])
            most_common = sentiment_counts.most_common(1)[0][0]
            
            if most_common == 'negative':
                quality['issues'].append("Sentimiento predominante negativo")
                score -= 20
            elif most_common == 'positive':
                quality['strengths'].append("Sentimiento predominante positivo")
                score += 15
        
        # 4. Duración de conversación
        if details['duration_minutes']:
            if details['duration_minutes'] < 1:
                quality['category'] = 'quick_question'
            elif 1 <= details['duration_minutes'] <= 10:
                quality['category'] = 'normal_conversation'
                quality['strengths'].append(f"Duración apropiada ({details['duration_minutes']:.1f} min)")
            elif 10 < details['duration_minutes'] <= 30:
                quality['category'] = 'extended_conversation'
                quality['strengths'].append(f"Conversación extendida ({details['duration_minutes']:.1f} min)")
            else:
                quality['category'] = 'very_long'
                quality['issues'].append(f"Conversación muy larga ({details['duration_minutes']:.1f} min)")
                score -= 10
        
        # 5. Intenciones detectadas
        if details['intents']:
            intent_counts = Counter(details['intents'])
            quality['strengths'].append(f"Intenciones detectadas: {dict(intent_counts)}")
        
        quality['score'] = max(0, min(100, score))
        
        return quality
    
    def generate_summary_report(self, days: int = 7):
        """Genera reporte completo de interacciones"""
        self.print_header(f"📊 EVALUACIÓN DE INTERACCIONES - ÚLTIMOS {days} DÍAS")
        
        print(f"📅 Período: {datetime.now() - timedelta(days=days)} → {datetime.now()}")
        print(f"🔍 Analizando conversaciones...\n")
        
        # Obtener conversaciones
        conversations = self.get_recent_conversations(days=days)
        
        if not conversations:
            print("❌ No se encontraron conversaciones en el período especificado")
            print("💡 Esto puede indicar:")
            print("   - El sistema no ha recibido tráfico")
            print("   - Hay un problema con la conexión a Cosmos DB")
            print("   - Los datos tienen más antigüedad\n")
            return
        
        print(f"✅ Encontradas {len(conversations)} conversaciones únicas\n")
        
        # Analizar cada conversación
        all_details = []
        all_qualities = []
        
        for conv in conversations[:20]:  # Limitar a 20 para no saturar
            details = self.get_conversation_details(conv['user_id'], conv['conversation_id'])
            if details:
                quality = self.analyze_conversation_quality(details)
                all_details.append(details)
                all_qualities.append(quality)
        
        if not all_details:
            print("❌ No se pudieron obtener detalles de las conversaciones")
            return
        
        # === MÉTRICAS GENERALES ===
        self.print_section("📈 MÉTRICAS GENERALES")
        
        total_messages = sum(d['message_count'] for d in all_details)
        total_user_msgs = sum(d['user_message_count'] for d in all_details)
        total_bot_msgs = sum(d['bot_message_count'] for d in all_details)
        avg_quality = sum(q['score'] for q in all_qualities) / len(all_qualities)
        
        print(f"Total de mensajes: {total_messages}")
        print(f"  └─ Usuarios: {total_user_msgs} ({total_user_msgs/total_messages*100:.1f}%)")
        print(f"  └─ Bot: {total_bot_msgs} ({total_bot_msgs/total_messages*100:.1f}%)")
        print(f"\nMensajes por conversación (promedio): {total_messages/len(all_details):.1f}")
        print(f"Calidad promedio: {avg_quality:.1f}/100")
        
        # Distribución de sentimientos
        all_sentiments = []
        for d in all_details:
            all_sentiments.extend(d['sentiments'])
        
        if all_sentiments:
            sentiment_dist = Counter(all_sentiments)
            print(f"\nDistribución de sentimientos:")
            for sentiment, count in sentiment_dist.most_common():
                percentage = count / len(all_sentiments) * 100
                emoji = "😊" if sentiment == "positive" else "😐" if sentiment == "neutral" else "😞"
                print(f"  {emoji} {sentiment.capitalize()}: {count} ({percentage:.1f}%)")
        
        # Herramientas más usadas
        all_tools = []
        for d in all_details:
            all_tools.extend(d['tools_used'])
        
        if all_tools:
            tool_dist = Counter(all_tools)
            print(f"\nHerramientas más usadas:")
            for tool, count in tool_dist.most_common(5):
                print(f"  🔧 {tool}: {count} veces")
        
        # === CATEGORÍAS DE CONVERSACIÓN ===
        self.print_section("📂 CATEGORÍAS DE CONVERSACIÓN")
        
        categories = Counter(q['category'] for q in all_qualities)
        category_names = {
            'quick_question': '⚡ Consultas rápidas',
            'normal_conversation': '💬 Conversaciones normales',
            'extended_conversation': '📖 Conversaciones extendidas',
            'very_long': '⏰ Conversaciones muy largas',
            'unknown': '❓ Sin categorizar'
        }
        
        for cat, count in categories.most_common():
            percentage = count / len(all_qualities) * 100
            print(f"{category_names.get(cat, cat)}: {count} ({percentage:.1f}%)")
        
        # === TOP 5 MEJORES CONVERSACIONES ===
        self.print_section("🏆 TOP 5 MEJORES CONVERSACIONES")
        
        top_convs = sorted(
            zip(all_details, all_qualities),
            key=lambda x: x[1]['score'],
            reverse=True
        )[:5]
        
        for idx, (detail, quality) in enumerate(top_convs, 1):
            print(f"\n{idx}. Conversación {detail['conversation_id'][:20]}...")
            print(f"   Usuario: {detail['user_id'][:30]}...")
            print(f"   Calidad: {quality['score']}/100")
            print(f"   Mensajes: {detail['message_count']}")
            if quality['strengths']:
                print(f"   ✅ Fortalezas: {quality['strengths'][0]}")
        
        # === TOP 5 CONVERSACIONES CON PROBLEMAS ===
        self.print_section("⚠️ TOP 5 CONVERSACIONES CON OPORTUNIDADES DE MEJORA")
        
        bottom_convs = sorted(
            zip(all_details, all_qualities),
            key=lambda x: x[1]['score']
        )[:5]
        
        for idx, (detail, quality) in enumerate(bottom_convs, 1):
            print(f"\n{idx}. Conversación {detail['conversation_id'][:20]}...")
            print(f"   Usuario: {detail['user_id'][:30]}...")
            print(f"   Calidad: {quality['score']}/100")
            print(f"   Mensajes: {detail['message_count']}")
            if quality['issues']:
                print(f"   ❌ Problemas detectados:")
                for issue in quality['issues']:
                    print(f"      - {issue}")
        
        # === RECOMENDACIONES ===
        self.print_section("💡 RECOMENDACIONES")
        
        recommendations = []
        
        # Analizar patrones comunes
        avg_messages = total_messages / len(all_details)
        if avg_messages < 3:
            recommendations.append("🔴 Conversaciones muy cortas - considerar mejorar engagement inicial")
        
        if all_sentiments:
            negative_rate = sentiment_dist.get('negative', 0) / len(all_sentiments)
            if negative_rate > 0.3:
                recommendations.append("🔴 Alto nivel de sentimiento negativo - revisar tono y respuestas")
        
        tool_usage_rate = sum(1 for d in all_details if d['tools_used']) / len(all_details)
        if tool_usage_rate < 0.3:
            recommendations.append("🟡 Bajo uso de herramientas - considerar prompts más proactivos")
        
        if avg_quality < 70:
            recommendations.append("🔴 Calidad promedio baja - revisar logs y ajustar respuestas")
        elif avg_quality < 85:
            recommendations.append("🟡 Calidad promedio media - hay espacio para mejoras")
        else:
            recommendations.append("🟢 Calidad promedio excelente - mantener el estándar")
        
        if recommendations:
            for rec in recommendations:
                print(f"  {rec}")
        else:
            print("  ✅ No se detectaron áreas críticas de mejora")
        
        # === EJEMPLO DE CONVERSACIÓN ===
        if all_details:
            self.print_section("💬 EJEMPLO DE CONVERSACIÓN REAL (Primera encontrada)")
            
            example = all_details[0]
            print(f"Usuario: {example['user_id'][:30]}...")
            print(f"Mensajes: {example['message_count']}")
            print(f"\nÚltimos 6 mensajes:\n")
            
            for msg in example['messages'][:6]:
                role = "👤 Usuario" if msg['role'] == 'user' else "🤖 Hernando"
                content = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
                timestamp = msg.get('timestamp', '')[:19]
                print(f"{role} [{timestamp}]:")
                print(f"  {content}\n")
        
        # === FOOTER ===
        self.print_header("✅ EVALUACIÓN COMPLETADA")
        
        print(f"📊 Resumen final:")
        print(f"  - Conversaciones analizadas: {len(all_details)}")
        print(f"  - Calidad promedio: {avg_quality:.1f}/100")
        print(f"  - Total mensajes: {total_messages}")
        
        score_emoji = "🏆" if avg_quality >= 85 else "✅" if avg_quality >= 70 else "⚠️"
        print(f"\n{score_emoji} Estado general: {'EXCELENTE' if avg_quality >= 85 else 'BUENO' if avg_quality >= 70 else 'NECESITA MEJORAS'}")
        print()
    
    def analyze_specific_conversation(self, user_id: str, conversation_id: Optional[str] = None):
        """Analiza una conversación específica en detalle"""
        self.print_header(f"🔍 ANÁLISIS DETALLADO DE CONVERSACIÓN")
        
        if not conversation_id:
            conversation_id = self.store.get_latest_conversation_id(user_id)
            if not conversation_id:
                print(f"❌ No se encontraron conversaciones para el usuario: {user_id}")
                return
        
        print(f"Usuario: {user_id}")
        print(f"Conversación: {conversation_id}\n")
        
        details = self.get_conversation_details(user_id, conversation_id)
        if not details:
            print("❌ No se pudieron obtener detalles")
            return
        
        quality = self.analyze_conversation_quality(details)
        
        print(f"📊 Métricas:")
        print(f"  - Total mensajes: {details['message_count']}")
        print(f"  - Usuario: {details['user_message_count']}")
        print(f"  - Bot: {details['bot_message_count']}")
        print(f"  - Duración: {details['duration_minutes']:.1f} minutos" if details['duration_minutes'] else "  - Duración: N/A")
        print(f"  - Calidad: {quality['score']}/100")
        print(f"  - Categoría: {quality['category']}")
        
        if quality['strengths']:
            print(f"\n✅ Fortalezas:")
            for strength in quality['strengths']:
                print(f"  - {strength}")
        
        if quality['issues']:
            print(f"\n⚠️ Problemas detectados:")
            for issue in quality['issues']:
                print(f"  - {issue}")
        
        print(f"\n💬 Transcripción completa:\n")
        for idx, msg in enumerate(reversed(details['messages']), 1):
            role = "👤 Usuario" if msg['role'] == 'user' else "🤖 Hernando"
            timestamp = msg.get('timestamp', '')[:19]
            metadata = msg.get('metadata', {})
            
            print(f"{idx}. {role} [{timestamp}]")
            print(f"   {msg['message']}")
            
            if metadata.get('sentiment'):
                print(f"   📊 Sentimiento: {metadata['sentiment']}")
            if metadata.get('intent'):
                print(f"   🎯 Intención: {metadata['intent']}")
            if metadata.get('tools_executed'):
                print(f"   🔧 Herramientas: {', '.join(metadata['tools_executed'])}")
            print()


def main():
    """Función principal"""
    print("\n" + "="*80)
    print("  🔍 EVALUADOR DE INTERACCIONES DE HERNANDO")
    print("="*80)
    
    evaluator = InteractionEvaluator()
    
    # Menú de opciones
    print("\nOpciones disponibles:")
    print("  1. Reporte completo (últimos 7 días)")
    print("  2. Reporte completo (últimos 30 días)")
    print("  3. Analizar conversación específica")
    print("  4. Salir")
    
    try:
        option = input("\nSelecciona una opción (1-4): ").strip()
        
        if option == "1":
            evaluator.generate_summary_report(days=7)
        elif option == "2":
            evaluator.generate_summary_report(days=30)
        elif option == "3":
            user_id = input("Ingresa el User ID: ").strip()
            conv_id = input("Ingresa el Conversation ID (o Enter para usar el más reciente): ").strip()
            evaluator.analyze_specific_conversation(
                user_id=user_id,
                conversation_id=conv_id if conv_id else None
            )
        elif option == "4":
            print("\n👋 ¡Hasta luego!")
            return
        else:
            print("\n❌ Opción no válida")
    
    except KeyboardInterrupt:
        print("\n\n👋 Evaluación cancelada")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
