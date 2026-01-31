"""
Scheduler para generación y publicación automática diaria de artículos del blog
Se ejecuta en segundo plano y genera contenido diariamente a las 08:00 AM Chile
"""
from __future__ import annotations
import threading
import time
from datetime import datetime, time as dt_time, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import config
from news_aggregator import get_news_aggregator
from blog_publisher import get_blog_publisher

# Singleton para el thread del scheduler
_scheduler_thread: Optional[threading.Thread] = None

# Zona horaria de Chile
CHILE_TZ = ZoneInfo("America/Santiago")

# Hora de publicación diaria (08:00 AM Chile)
DAILY_PUBLISH_HOUR = 8
DAILY_PUBLISH_MINUTE = 0

# Intervalo de chequeo (cada 30 minutos)
CHECK_INTERVAL_SECONDS = 30 * 60


def _is_time_to_publish() -> bool:
    """
    Verifica si es hora de publicar (08:00 AM Chile)
    Retorna True solo una vez por día
    """
    now_chile = datetime.now(CHILE_TZ)
    
    # Verificar si es la hora correcta (08:00 AM +/- 15 min)
    target_time = now_chile.replace(hour=DAILY_PUBLISH_HOUR, minute=DAILY_PUBLISH_MINUTE, second=0, microsecond=0)
    time_diff = abs((now_chile - target_time).total_seconds())
    
    # Si estamos dentro de la ventana de 30 minutos (CHECK_INTERVAL_SECONDS)
    if time_diff <= CHECK_INTERVAL_SECONDS:
        # Verificar si ya publicamos hoy
        last_publish_date = getattr(_is_time_to_publish, '_last_publish_date', None)
        today = now_chile.date()
        
        if last_publish_date != today:
            # Marcar como publicado hoy
            _is_time_to_publish._last_publish_date = today
            return True
    
    return False


def _generate_and_publish() -> None:
    """
    Ejecuta el proceso completo:
    1. Agrega noticias de múltiples fuentes
    2. Genera artículo original con IA
    3. Publica en el blog
    """
    try:
        print("\n" + "="*70)
        print(f"🚀 INICIANDO PUBLICACIÓN AUTOMÁTICA DIARIA")
        print(f"   📅 {datetime.now(CHILE_TZ).strftime('%d/%m/%Y %H:%M:%S %Z')}")
        print("="*70 + "\n")
        
        # Paso 1: Agregar noticias y generar artículo
        aggregator = get_news_aggregator()
        digest = aggregator.create_daily_digest()
        
        article = digest.get("article")
        if not article:
            print("❌ No se pudo generar artículo")
            return
        
        # Paso 2: Publicar artículo
        publisher = get_blog_publisher()
        result = publisher.publish_article(article, save_to_cosmos=True)
        
        if result.get("success"):
            print("\n" + "="*70)
            print("✅ PUBLICACIÓN COMPLETADA EXITOSAMENTE")
            print(f"   📝 Título: {article.get('title', 'N/A')}")
            print(f"   🔗 URL: {result.get('url', 'N/A')}")
            print(f"   📄 Archivo: {result.get('filepath', 'N/A')}")
            print("="*70 + "\n")
        else:
            print(f"\n❌ Error en publicación: {result.get('error', 'Unknown')}\n")
            
    except Exception as e:
        print(f"\n❌ Error en proceso de publicación automática: {e}\n")
        import traceback
        traceback.print_exc()


def _run_once_if_needed() -> None:
    """Ejecuta una verificación y publica si es necesario"""
    try:
        if _is_time_to_publish():
            print("⏰ Es hora de publicar contenido diario!")
            _generate_and_publish()
        else:
            now = datetime.now(CHILE_TZ)
            print(f"⏸️  No es hora de publicar (ahora: {now.strftime('%H:%M')} - objetivo: {DAILY_PUBLISH_HOUR:02d}:{DAILY_PUBLISH_MINUTE:02d})")
    except Exception as e:
        print(f"❌ Error en verificación del scheduler: {e}")


def _loop() -> None:
    """Loop principal del scheduler"""
    print("\n" + "="*70)
    print("🤖 NEWS SCHEDULER INICIADO")
    print(f"   ⏰ Publicación diaria: {DAILY_PUBLISH_HOUR:02d}:{DAILY_PUBLISH_MINUTE:02d} (Chile)")
    print(f"   🔄 Intervalo de chequeo: {CHECK_INTERVAL_SECONDS // 60} minutos")
    print("="*70 + "\n")
    
    while True:
        try:
            _run_once_if_needed()
        except Exception as e:
            print(f"❌ Error en loop del scheduler: {e}")
        
        # Esperar hasta el próximo chequeo
        time.sleep(CHECK_INTERVAL_SECONDS)


def start_news_scheduler() -> None:
    """
    Inicia el scheduler en un thread de background
    Solo se ejecuta si NEWS_SCHEDULER_ENABLED=True en config
    """
    global _scheduler_thread
    
    # Verificar si está habilitado
    if not getattr(config, 'NEWS_SCHEDULER_ENABLED', True):
        print("⚠️  News Scheduler deshabilitado en configuración")
        return
    
    # Verificar si ya está corriendo
    if _scheduler_thread and _scheduler_thread.is_alive():
        print("⚠️  News Scheduler ya está corriendo")
        return
    
    # Iniciar thread
    _scheduler_thread = threading.Thread(target=_loop, daemon=True, name="NewsScheduler")
    _scheduler_thread.start()
    
    print(f"✅ News Scheduler iniciado (Thread: {_scheduler_thread.name})")


def run_now() -> None:
    """
    Ejecuta la generación y publicación INMEDIATAMENTE (sin esperar horario)
    Útil para testing y publicaciones manuales
    """
    print("🚀 Ejecutando publicación inmediata (modo manual)...")
    _generate_and_publish()


def get_next_publish_time() -> str:
    """Retorna la próxima hora de publicación en formato legible"""
    now = datetime.now(CHILE_TZ)
    next_publish = now.replace(hour=DAILY_PUBLISH_HOUR, minute=DAILY_PUBLISH_MINUTE, second=0, microsecond=0)
    
    # Si ya pasó hoy, usar mañana
    if now >= next_publish:
        next_publish += timedelta(days=1)
    
    return next_publish.strftime("%d/%m/%Y %H:%M %Z")


# CLI para testing y administración
def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(description="News Scheduler para publicaciones automáticas del blog")
    parser.add_argument("--now", action="store_true", help="Ejecutar publicación inmediata (ignora horario)")
    parser.add_argument("--loop", action="store_true", help="Ejecutar en loop daemon (producción)")
    parser.add_argument("--test", action="store_true", help="Verificar configuración sin publicar")
    parser.add_argument("--next", action="store_true", help="Mostrar próxima hora de publicación")
    
    args = parser.parse_args()
    
    if args.now:
        run_now()
        return 0
    
    elif args.loop:
        print("🔄 Iniciando scheduler en modo loop...")
        _loop()
        return 0
    
    elif args.test:
        print("🧪 VERIFICACIÓN DE CONFIGURACIÓN")
        print("="*50)
        print(f"✓ Hora de publicación: {DAILY_PUBLISH_HOUR:02d}:{DAILY_PUBLISH_MINUTE:02d} (Chile)")
        print(f"✓ Intervalo de chequeo: {CHECK_INTERVAL_SECONDS // 60} min")
        print(f"✓ Próxima publicación: {get_next_publish_time()}")
        print(f"✓ Hora actual Chile: {datetime.now(CHILE_TZ).strftime('%d/%m/%Y %H:%M:%S %Z')}")
        
        # Verificar dependencias
        try:
            aggregator = get_news_aggregator()
            print("✓ NewsAggregator: OK")
        except Exception as e:
            print(f"❌ NewsAggregator: {e}")
        
        try:
            publisher = get_blog_publisher()
            print("✓ BlogPublisher: OK")
        except Exception as e:
            print(f"❌ BlogPublisher: {e}")
        
        print("="*50)
        return 0
    
    elif args.next:
        print(f"📅 Próxima publicación: {get_next_publish_time()}")
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
