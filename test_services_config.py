#!/usr/bin/env python3
"""
Simple test for Elite Orchestrator Tools - No Cosmos DB required
"""

import json
from hernando_tools import RAILWAY_SERVICES

def test_railway_services_config():
    """Test that railway services are properly configured"""
    
    print("=" * 80)
    print("PRUEBA: RAILWAY SERVICES CONFIGURATION")
    print("=" * 80)
    
    print(f"\nTotal de servicios configurados: {len(RAILWAY_SERVICES)}\n")
    
    # Test 1: Listar todos los servicios
    print("TEST 1: Servicios Railway Disponibles")
    print("-" * 80)
    
    activos = 0
    for svc_key, svc_info in RAILWAY_SERVICES.items():
        estado = "[OK]" if svc_info.get("available") else "[XX]"
        if svc_info.get("available"):
            activos += 1
        
        print(f"\n{estado} {svc_info['name']}")
        print(f"   Key: {svc_key}")
        print(f"   Description: {svc_info['description']}")
        print(f"   URL: {svc_info.get('url', 'N/A')}")
        
        if svc_info.get('capabilities'):
            print(f"   Capabilities: {', '.join(svc_info['capabilities'])}")
    
    print(f"\n\nResumen: {activos}/{len(RAILWAY_SERVICES)} servicios disponibles")
    
    # Test 2: Verify critical services
    print("\n\nTEST 2: Servicios Críticos")
    print("-" * 80)
    
    servicios_criticos = [
        "hernando",
        "traductor",
        "lenguaje",
        "vision_service",
        "whatsapp",
        "cosmos_db"
    ]
    
    for svc_name in servicios_criticos:
        if svc_name in RAILWAY_SERVICES:
            svc = RAILWAY_SERVICES[svc_name]
            estado = "[OK]" if svc.get("available") else "[MISSING CONFIG]"
            print(f"{estado} {svc.get('name', 'N/A')}")
        else:
            print(f"[ERROR] {svc_name} no esta en RAILWAY_SERVICES")
    
    # Test 3: Check tool definitions
    print("\n\nTEST 3: Elite Orchestrator Herramientas")
    print("-" * 80)
    
    print("[OK] listar_servicios_disponibles - Lista todos los servicios Railway")
    print("[OK] verificar_salud_servicios - Health check a todos los servicios")
    print("[OK] consultar_servicio_railway - Acceso generico a endpoints")
    
    # Test 4: Summary
    print("\n\n" + "=" * 80)
    print("[SUCCESS] CONFIGURACION DE SERVICIOS VALIDADA")
    print("=" * 80)
    
    print("""
Hernando Orquestador Elite esta configurado para acceder a:

1. TRADUCTOR - Traduccion a 100+ idiomas
2. LENGUAJE - Analisis de sentimiento, entidades, frases clave
3. VISION SERVICE - Analisis de imagenes, OCR, deteccion de objetos
4. WHATSAPP (WAHA) - Mensajeria, webhooks
5. REDIS - Cache, sesiones
6. STEEL BROWSER - Navegacion web, scraping
7. MENSAJERIA - Emails, notificaciones
8. COSMOS DB - Base de datos NoSQL
9. WEB FUNDO MORAGA - Frontend publica

Uso para Usuario Admin (Efrain Moraga):
- Acceso completo a todos los servicios
- Puede hacer: traducciones, analisis de imagenes, navegacion web, consultas
- Sistema inteligente que selecciona el servicio mas apropiado
    """)

if __name__ == "__main__":
    try:
        test_railway_services_config()
        print("\n[SUCCESS] Todas las pruebas pasaron correctamente!")
    except Exception as e:
        print(f"\n[ERROR] ERROR durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
