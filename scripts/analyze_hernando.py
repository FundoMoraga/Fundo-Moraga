#!/usr/bin/env python3
"""Análisis de conversaciones de Hernando"""
import sys
sys.path.insert(0, '.')

from scripts.export_conversations import ConversationExporter

exporter = ConversationExporter()
summary = exporter.generate_summary(days=30)

print("\n" + "="*70)
print("📈 RESUMEN DE CONVERSACIONES DE HERNANDO (Últimos 30 días)")
print("="*70)

print(f"\n📊 Estadísticas Generales:")
print(f"   • Total de conversaciones: {summary['total_conversations']}")
print(f"   • Total de mensajes: {summary['total_messages']}")
print(f"   • Mensajes promedio/conversación: {summary['avg_messages_per_conversation']:.1f}")
print(f"   • Duración promedio: {summary['avg_duration_seconds']} segundos (~{summary['avg_duration_seconds']//60} min)")

print(f"\n🎯 Intenciones y Captura:")
print(f"   • Conversaciones con intención de reserva: {summary['conversations_with_booking_intent']} ({summary['conversations_with_booking_intent']/max(1, summary['total_conversations'])*100:.1f}%)")
print(f"   • Conversaciones con contacto capturado: {summary['conversations_with_contact_info']} ({summary['conversations_with_contact_info']/max(1, summary['total_conversations'])*100:.1f}%)")

print(f"\n😊 Distribución de Sentimientos:")
for sentiment, count in sorted(summary['sentiment_distribution'].items(), key=lambda x: x[1], reverse=True):
    pct = (count / summary['total_messages']) * 100
    print(f"   • {sentiment}: {count} ({pct:.1f}%)")

print(f"\n🏆 Top 5 Conversaciones (por duración):")
for i, conv in enumerate(summary['top_conversations'][:5], 1):
    booking = "✓ Reserva" if conv['booking_intent'] else ""
    contact = "✓ Contacto" if conv['has_contact'] else ""
    flags = f" [{booking} {contact}]" if booking or contact else ""
    mins = conv['duration_seconds'] // 60
    secs = conv['duration_seconds'] % 60
    print(f"   {i}. {conv['total_messages']} msg, {mins}m {secs}s, Sentimiento: {conv['sentiment']}{flags}")

print("\n="*70)

# Exportar a JSON completo
print("\n📁 Exportando conversaciones anonimizadas...")
filepath = exporter.export_to_json(days=30, anonymize=True)
print(f"✅ Archivo guardado: {filepath}")
