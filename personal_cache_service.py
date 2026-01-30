"""
Servicio de inicialización del Cache Personal de Efraín.
Asegura que el cache sea estructural y accesible 24/7 en toda la aplicación.

Este módulo se carga al iniciar el servidor y mantiene:
1. Cache personal en Redis (persistente, sin TTL)
2. Prompts de Cosmos DB (cacheados 1h)
3. Manual de instrucciones en memoria (rápido acceso)
4. Sincronización automática cada 30min

GARANTÍA: El cache está listo para usar desde el primer mensaje de Efraín.
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

# Variables globales para el servicio
_personal_cache_service = None
_service_thread = None
_service_running = False


class PersonalCacheService:
    """Servicio de cache personal que corre en background"""
    
    def __init__(self):
        self.enabled = False
        self.personal_cache = None
        self.sync_interval_seconds = 1800  # 30 minutos
        self.last_sync = None
        self._init()
    
    def _init(self):
        """Inicializa el servicio"""
        try:
            from personal_context_cache import get_personal_cache
            self.personal_cache = get_personal_cache()
            
            if not self.personal_cache.enabled:
                print("⚠️ Cache personal deshabilitado (Redis no disponible)")
                self.enabled = False
                return
            
            self.enabled = True
            print("✅ Servicio de Cache Personal inicializado")
            print(f"   📌 Disponible para: Efraín Moraga (+56957513744, +56941242609)")
            print(f"   📌 Almacenamiento: Redis (persistente, sin TTL)")
            print(f"   📌 Manual de instrucciones: {len(self.personal_cache._instructions_manual)} capacidades")
            print(f"   📌 Sincronización: cada {self.sync_interval_seconds}s (30min)")
            
        except Exception as e:
            print(f"❌ Error inicializando servicio de cache personal: {e}")
            self.enabled = False
    
    def sync_cosmos_prompts(self):
        """
        Sincroniza los prompts de Cosmos DB con el cache.
        Se ejecuta periódicamente para mantener actualizado.
        """
        if not self.enabled or not self.personal_cache:
            return
        
        try:
            # Forzar recarga de prompts de Cosmos DB
            prompts = self.personal_cache._load_cosmos_prompts(force_reload=True)
            
            if prompts:
                print(f"🔄 Sincronización de prompts Cosmos DB completada ({len(prompts)} prompts)")
                self.last_sync = datetime.now(timezone.utc)
            
        except Exception as e:
            print(f"⚠️ Error sincronizando prompts Cosmos DB: {e}")

    def sync_instructions_manual(self):
        """
        Sincroniza el manual de instrucciones en Redis.
        """
        if not self.enabled or not self.personal_cache:
            return

        try:
            self.personal_cache.refresh_instructions_manual()
        except Exception as e:
            print(f"⚠️ Error sincronizando manual de instrucciones: {e}")
    
    def get_status(self) -> dict:
        """Retorna estado del servicio"""
        if not self.enabled:
            return {"enabled": False, "reason": "Redis no disponible"}
        
        return {
            "enabled": True,
            "cache_loaded": self.personal_cache is not None,
            "instructions_count": len(self.personal_cache._instructions_manual) if self.personal_cache else 0,
            "cosmos_prompts_cache_ttl": self.personal_cache.COSMOS_PROMPTS_CACHE_TTL if self.personal_cache else 0,
            "last_sync": self.last_sync.isoformat() if self.last_sync else "Nunca",
            "next_sync": (self.last_sync + timedelta(seconds=self.sync_interval_seconds)).isoformat() if self.last_sync else "Próximamente",
        }
    
    def run_background_sync(self):
        """Ejecuta sincronización en background"""
        print("🌀 Iniciando hilo de sincronización del cache personal...")
        
        while _service_running:
            try:
                self.sync_cosmos_prompts()
                self.sync_instructions_manual()
                time.sleep(self.sync_interval_seconds)
            except Exception as e:
                print(f"❌ Error en hilo de sincronización: {e}")
                time.sleep(60)  # Reintentar después de 1 minuto


def init_personal_cache_service():
    """
    Inicializa el servicio de cache personal.
    Se llama una sola vez al arrancar la aplicación.
    """
    global _personal_cache_service, _service_thread, _service_running
    
    if _personal_cache_service is not None:
        print("⚠️ Servicio de cache personal ya inicializado")
        return _personal_cache_service
    
    try:
        # Crear servicio
        _personal_cache_service = PersonalCacheService()
        
        if not _personal_cache_service.enabled:
            print("⚠️ Cache personal deshabilitado")
            return _personal_cache_service
        
        # Sincronizar prompts una vez al iniciar
        _personal_cache_service.sync_cosmos_prompts()
        _personal_cache_service.sync_instructions_manual()
        
        # Iniciar hilo de sincronización automática
        _service_running = True
        _service_thread = threading.Thread(
            target=_personal_cache_service.run_background_sync,
            daemon=True,
            name="PersonalCacheSyncThread"
        )
        _service_thread.start()
        
        print("✅ Servicio de Cache Personal iniciado exitosamente")
        print(f"🔄 Sincronización automática cada {_personal_cache_service.sync_interval_seconds}s")
        
    except Exception as e:
        print(f"❌ Error inicializando servicio de cache personal: {e}")
    
    return _personal_cache_service


def get_personal_cache_service() -> Optional[PersonalCacheService]:
    """Obtiene la instancia del servicio (singleton)"""
    global _personal_cache_service
    
    if _personal_cache_service is None:
        init_personal_cache_service()
    
    return _personal_cache_service


def stop_personal_cache_service():
    """Detiene el servicio de cache personal"""
    global _service_running, _service_thread
    
    _service_running = False
    
    if _service_thread:
        _service_thread.join(timeout=5)
        print("🛑 Servicio de Cache Personal detenido")


# Health check para monitoreo
def personal_cache_health_check() -> dict:
    """Retorna estado de salud del servicio de cache personal"""
    service = get_personal_cache_service()
    
    if not service:
        return {
            "status": "error",
            "message": "Servicio no inicializado"
        }
    
    status_data = service.get_status()
    
    if not status_data.get("enabled"):
        return {
            "status": "warning",
            "message": status_data.get("reason", "Desconocido")
        }
    
    return {
        "status": "healthy",
        "service": status_data
    }
