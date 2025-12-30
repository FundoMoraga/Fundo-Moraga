#!/usr/bin/env python3
"""
Script mejorado para exportar conversaciones de Hernando desde Cosmos DB
Agrupa mensajes por conversationId y genera análisis detallado
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import hashlib
from collections import defaultdict, Counter

from azure.cosmos import CosmosClient
from config import (
    COSMOS_ENDPOINT,
    COSMOS_KEY,
    COSMOS_DATABASE,
    COSMOS_CONTAINER,
)


class ConversationExporter:
    def __init__(self):
        """Inicializa el cliente de Cosmos DB"""
        try:
            self.client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
            self.database = self.client.get_database_client(COSMOS_DATABASE)
            self.container = self.database.get_container_client(COSMOS_CONTAINER)
            print(f"✅ Conectado a Cosmos DB: {COSMOS_DATABASE}/{COSMOS_CONTAINER}")
        except Exception as e:
            print(f"❌ Error conectando a Cosmos DB: {e}")
            raise

    def anonymize_email(self, email: str) -> str:
        """Anonimiza emails manteniendo patrón reconocible"""
        if not email or "@" not in email:
            return "user@example.com"
        
        local, domain = email.split("@", 1)
        hash_val = hashlib.md5(local.encode()).hexdigest()[:6]
        return f"user_{hash_val}@{domain}"

    def anonymize_phone(self, phone: str) -> str:
        """Anonimiza números de teléfono"""
        if not phone:
            return "+56 9 XXXX XXXX"
        
        # Mantiene primeros 3 y últimos 2 dígitos
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 5:
            return f"+56 9 {digits[-6:-2]}XX{digits[-2:]}"
        return "+56 9 XXXX XXXX"

    def anonymize_name(self, name: str) -> str:
        """Anonimiza nombres"""
        if not name:
            return "Usuario"
        
        parts = name.split()
        if len(parts) == 1:
            return f"{parts[0][0]}***"
        
        return f"{parts[0][0]}*** {parts[-1][0]}***"

    def anonymize_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Anonimiza una conversación completa"""
        anon = conversation.copy()
        
        # Anonimizar campos directos
        if "user_id" in anon:
            anon["user_id_hash"] = hashlib.md5(str(anon["user_id"]).encode()).hexdigest()[:8]
            del anon["user_id"]
        
        if "user_name" in anon:
            anon["user_name"] = self.anonymize_name(anon["user_name"])
        
        if "user_email" in anon:
            anon["user_email"] = self.anonymize_email(anon["user_email"])
        
        if "user_phone" in anon:
            anon["user_phone"] = self.anonymize_phone(anon["user_phone"])
        
        # Anonimizar en metadatos
        if "user_metadata" in anon and isinstance(anon["user_metadata"], dict):
            metadata = anon["user_metadata"].copy()
            if "name" in metadata:
                metadata["name"] = self.anonymize_name(metadata["name"])
            if "email" in metadata:
                metadata["email"] = self.anonymize_email(metadata["email"])
            if "phone" in metadata:
                metadata["phone"] = self.anonymize_phone(metadata["phone"])
            anon["user_metadata"] = metadata
        
        # Anonimizar en mensajes
        if "messages" in anon and isinstance(anon["messages"], list):
            anon_messages = []
            for msg in anon["messages"]:
                anon_msg = msg.copy()
                # Reemplazar patrones de email
                if "text" in anon_msg:
                    anon_msg["text"] = re.sub(
                        r"[\w\.-]+@[\w\.-]+\.\w+",
                        "user@example.com",
                        anon_msg["text"]
                    )
                    # Reemplazar teléfonos
                    anon_msg["text"] = re.sub(
                        r"\+?56[0-9\s\-]{9,}",
                        "+56 9 XXXX XXXX",
                        anon_msg["text"]
                    )
                anon_messages.append(anon_msg)
            anon["messages"] = anon_messages
        
        return anon

    def get_recent_conversations(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """Obtiene conversaciones recientes"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            query = f"""
            SELECT * FROM c 
            WHERE c.timestamp >= @cutoff_date
            ORDER BY c.timestamp DESC
            """
            
            items = list(self.container.query_items(
                query=query,
                parameters=[{"name": "@cutoff_date", "value": cutoff_date}],
                max_item_count=limit,
                enable_cross_partition_query=True  # Habilitar cross-partition query
            ))
            
            print(f"✅ Obtenidas {len(items)} conversaciones de los últimos {days} días")
            return items
            
        except Exception as e:
            print(f"❌ Error obteniendo conversaciones: {e}")
            # Intentar con read_all_items como fallback
            try:
                print("⚠️  Intentando con read_all_items como fallback...")
                items = []
                for item in self.container.read_all_items(max_item_count=limit):
                    try:
                        item_date = datetime.fromisoformat(item.get("timestamp", ""))
                        if item_date >= datetime.fromisoformat(cutoff_date):
                            items.append(item)
                    except:
                        pass
                print(f"✅ Obtenidas {len(items)} conversaciones con fallback")
                return items
            except Exception as e2:
                print(f"❌ Error en fallback: {e2}")
                return []

    def calculate_metrics(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de una conversación"""
        messages = conversation.get("messages", [])
        
        metrics = {
            "total_messages": len(messages),
            "user_messages": sum(1 for m in messages if m.get("role") == "user"),
            "bot_messages": sum(1 for m in messages if m.get("role") == "assistant"),
            "avg_message_length": sum(len(m.get("text", "")) for m in messages) / len(messages) if messages else 0,
            "intent": conversation.get("intent", "unknown"),
            "sentiment": conversation.get("sentiment", "neutral"),
            "booking_completed": conversation.get("booking_completed", False),
            "lead_captured": conversation.get("lead_captured", False),
        }
        
        # Calcular duración
        if messages and len(messages) > 1:
            first_time = messages[0].get("timestamp", conversation.get("created_at", ""))
            last_time = messages[-1].get("timestamp", "")
            try:
                duration = (datetime.fromisoformat(last_time) - datetime.fromisoformat(first_time)).total_seconds()
                metrics["duration_seconds"] = int(duration)
            except:
                metrics["duration_seconds"] = 0
        
        return metrics

    def export_to_json(self, days: int = 7, anonymize: bool = True) -> str:
        """Exporta conversaciones a JSON"""
        print(f"\n📊 Exportando conversaciones de los últimos {days} días...")
        
        conversations = self.get_recent_conversations(days=days)
        
        exported_data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_conversations": len(conversations),
            "anonymized": anonymize,
            "conversations": []
        }
        
        for conv in conversations:
            # Anonimizar si es necesario
            if anonymize:
                conv = self.anonymize_conversation(conv)
            
            # Calcular métricas
            metrics = self.calculate_metrics(conv)
            conv["metrics"] = metrics
            
            exported_data["conversations"].append(conv)
        
        # Guardar a archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        anonymized_suffix = "_anonymized" if anonymize else ""
        filename = f"exported_conversations_{days}days{anonymized_suffix}_{timestamp}.json"
        filepath = f"exports/{filename}"
        
        # Crear directorio si no existe
        import os
        os.makedirs("exports", exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(exported_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Exportadas {len(conversations)} conversaciones")
        print(f"📁 Guardadas en: {filepath}")
        
        return filepath

    def generate_summary(self, days: int = 7) -> Dict[str, Any]:
        """Genera un resumen de las conversaciones"""
        conversations = self.get_recent_conversations(days=days)
        
        summary = {
            "period_days": days,
            "total_conversations": len(conversations),
            "total_messages": 0,
            "avg_messages_per_conversation": 0,
            "booking_completed": 0,
            "lead_captured": 0,
            "intents": {},
            "sentiments": {},
            "top_conversations": []
        }
        
        for conv in conversations:
            messages = conv.get("messages", [])
            summary["total_messages"] += len(messages)
            
            if conv.get("booking_completed"):
                summary["booking_completed"] += 1
            
            if conv.get("lead_captured"):
                summary["lead_captured"] += 1
            
            intent = conv.get("intent", "unknown")
            summary["intents"][intent] = summary["intents"].get(intent, 0) + 1
            
            sentiment = conv.get("sentiment", "neutral")
            summary["sentiments"][sentiment] = summary["sentiments"].get(sentiment, 0) + 1
        
        if summary["total_conversations"] > 0:
            summary["avg_messages_per_conversation"] = summary["total_messages"] / summary["total_conversations"]
        
        # Top 5 conversaciones
        top_convs = sorted(conversations, 
                          key=lambda x: len(x.get("messages", [])), 
                          reverse=True)[:5]
        
        for conv in top_convs:
            summary["top_conversations"].append({
                "timestamp": conv.get("timestamp", ""),
                "messages_count": len(conv.get("messages", [])),
                "intent": conv.get("intent", ""),
                "sentiment": conv.get("sentiment", ""),
                "booking_completed": conv.get("booking_completed", False)
            })
        
        return summary


def main():
    """Función principal"""
    import sys
    
    # Parsear argumentos
    days = 7
    anonymize = True
    
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])
    
    if "--no-anonymize" in sys.argv:
        anonymize = False
    
    try:
        exporter = ConversationExporter()
        
        # Exportar a JSON
        filepath = exporter.export_to_json(days=days, anonymize=anonymize)
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("📈 RESUMEN DE CONVERSACIONES")
        print("="*60)
        
        summary = exporter.generate_summary(days=days)
        
        print(f"\n📊 Período: {summary['period_days']} días")
        print(f"💬 Total de conversaciones: {summary['total_conversations']}")
        print(f"📝 Total de mensajes: {summary['total_messages']}")
        print(f"⏱️  Mensajes promedio/conversación: {summary['avg_messages_per_conversation']:.1f}")
        
        print(f"\n✅ Reservas completadas: {summary['booking_completed']} ({summary['booking_completed']/max(1, summary['total_conversations'])*100:.1f}%)")
        print(f"📧 Leads capturados: {summary['lead_captured']} ({summary['lead_captured']/max(1, summary['total_conversations'])*100:.1f}%)")
        
        print(f"\n🎯 Intenciones detectadas:")
        for intent, count in sorted(summary["intents"].items(), key=lambda x: x[1], reverse=True):
            print(f"   • {intent}: {count}")
        
        print(f"\n😊 Sentimientos:")
        for sentiment, count in sorted(summary["sentiments"].items(), key=lambda x: x[1], reverse=True):
            print(f"   • {sentiment}: {count}")
        
        print(f"\n🏆 Top 5 conversaciones (por cantidad de mensajes):")
        for i, conv in enumerate(summary["top_conversations"], 1):
            print(f"   {i}. {conv['messages_count']} mensajes - Intent: {conv['intent']} - Booking: {conv['booking_completed']}")
        
        print(f"\n✨ Anonimización: {'Sí ✅' if anonymize else 'No ❌'}")
        print(f"📁 Archivo guardado: {filepath}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
