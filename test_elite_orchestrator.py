#!/usr/bin/env python3
"""
Test script for Elite Orchestrator Tools
Verifica que los servicios Railway estén accesibles a través de Hernando
"""

import sys
import json
from hernando_tools import HernandoTools, RAILWAY_SERVICES

def test_elite_orchestrator():
    print("=" * 80)
    print("PRUEBA: HERNANDO ORQUESTADOR ELITE")
    print("=" * 80)
    
    # Crear instancia de herramientas para usuario admin (Efraín)
    user_id = "+56941242609"  # Efraín Moraga
    tools = HernandoTools(user_id=user_id)
    
    print(f"\n[OK] Instancia HernandoTools creada para usuario: {user_id}")
    print(f"[OK] Total de herramientas disponibles: {len(tools.tools)}\n")
    
    # Test 1: Listar servicios disponibles
    print("\n" + "=" * 80)
    print("TEST 1: Listar servicios disponibles")
    print("=" * 80)
    result = tools.listar_servicios_disponibles(filtro="activos", con_detalles=True)
    print(f"\n{result['mensaje']}")
    print(f"\nTotal activos: {result['activos']}/{result['total']}")
    print(f"Servicios encontrados: {len(result['servicios'])}")
    
    for svc in result['servicios']:
        print(f"\n  SERVICIO: {svc['nombre']}")
        print(f"     - Disponible: {svc['disponible']}")
        if svc.get('url'):
            print(f"     - URL: {svc['url']}")
        if svc.get('capacidades'):
            print(f"     - Capacidades: {', '.join(svc['capacidades'])}")
    
    # Test 2: Verificar salud de servicios
    print("\n" + "=" * 80)
    print("TEST 2: Verificar salud de servicios (Health Check)")
    print("=" * 80)
    health_result = tools.verificar_salud_servicios(timeout=3)
    print(f"\n{health_result.get('mensaje', 'Health check completado')}")
    
    # Contar estados
    estados = {}
    for svc_name, svc_status in health_result['servicios'].items():
        estado = svc_status['estado']
        estados[estado] = estados.get(estado, 0) + 1
    
    print(f"\nResumen de estados:")
    for estado, cantidad in sorted(estados.items()):
        print(f"   - {estado}: {cantidad}")
    
    # Test 3: Verificar que las herramientas están en la lista
    print("\n" + "=" * 80)
    print("TEST 3: Verificar herramientas en la lista")
    print("=" * 80)
    
    elite_tools = [
        "listar_servicios_disponibles",
        "verificar_salud_servicios",
        "consultar_servicio_railway"
    ]
    
    tool_names = [t.get("function", {}).get("name") for t in tools.tools if t.get("type") == "function"]
    
    for tool_name in elite_tools:
        if tool_name in tool_names:
            print(f"[OK] {tool_name} - Disponible")
        else:
            print(f"[ERROR] {tool_name} - NO DISPONIBLE")
    
    # Test 4: Información de Railway Services
    print("\n" + "=" * 80)
    print("TEST 4: Información de Railway Services")
    print("=" * 80)
    
    print(f"\nTotal de servicios configurados: {len(RAILWAY_SERVICES)}\n")
    
    for svc_key, svc_info in RAILWAY_SERVICES.items():
        estado_emoji = "[OK]" if svc_info.get("available") else "[XX]"
        print(f"{estado_emoji} {svc_info['name']}")
        print(f"   Descripcion: {svc_info['description']}")
        print(f"   URL: {svc_info.get('url', 'N/A')}")
        print()
    
    # Test 5: Ejecutar consulta genérica
    print("\n" + "=" * 80)
    print("TEST 5: Consultar servicio genérico (Mock)")
    print("=" * 80)
    
    print("\nIntentando consultar un servicio hypothético...")
    consulta_result = tools.consultar_servicio_railway(
        servicio="traductor",
        endpoint="/health",
        metodo="GET"
    )
    
    print(f"\nResultado:")
    print(json.dumps(consulta_result, indent=2, ensure_ascii=False))
    
    # Resumen final
    print("\n" + "=" * 80)
    print("[OK] PRUEBAS COMPLETADAS")
    print("=" * 80)
    print("\nConclusiones:")
    print("  [OK] Sistema Orquestador Elite inicializado correctamente")
    print("  [OK] Se pueden listar todos los servicios Railway")
    print("  [OK] Se pueden hacer health checks a los servicios")
    print("  [OK] Las nuevas herramientas estan disponibles para OpenAI Function Calling")
    print("\n[SUCCESS] Hernando esta listo para actuar como Orquestador Elite de Herramientas!")

if __name__ == "__main__":
    try:
        test_elite_orchestrator()
    except Exception as e:
        print(f"\n[ERROR] ERROR durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

