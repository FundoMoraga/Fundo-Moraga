#!/usr/bin/env python3
"""
Script de build para inyectar configuraciones dinámicas en HTMLs estáticos
Reemplaza placeholders con valores de variables de entorno
"""
import os
import re
from pathlib import Path

# Configuración
GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID", "G-XXXXXXXXXX")
WEB_DIR = Path("Web")

# Placeholders a reemplazar
REPLACEMENTS = {
    "G-XXXXXXXXXX": GOOGLE_ANALYTICS_ID,
}

def process_html_file(filepath: Path) -> bool:
    """Procesa un archivo HTML reemplazando placeholders"""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Aplicar reemplazos
        for placeholder, value in REPLACEMENTS.items():
            if placeholder in content:
                content = content.replace(placeholder, value)
                print(f"  ✓ Reemplazado '{placeholder}' → '{value}' en {filepath.name}")
        
        # Solo escribir si hubo cambios
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return True
        return False
        
    except Exception as e:
        print(f"  ❌ Error procesando {filepath}: {e}")
        return False

def main():
    print("="*60)
    print("🔧 BUILD SCRIPT - Configuración dinámica de HTMLs")
    print("="*60)
    print(f"\nConfiguraciones:")
    print(f"  GOOGLE_ANALYTICS_ID: {GOOGLE_ANALYTICS_ID}")
    print(f"  WEB_DIR: {WEB_DIR}")
    
    # Buscar todos los HTMLs
    html_files = list(WEB_DIR.rglob("*.html"))
    print(f"\n📄 Encontrados {len(html_files)} archivos HTML\n")
    
    processed = 0
    for html_file in html_files:
        if process_html_file(html_file):
            processed += 1
    
    print(f"\n✅ Build completado: {processed}/{len(html_files)} archivos actualizados")
    
    if GOOGLE_ANALYTICS_ID == "G-XXXXXXXXXX":
        print("\n⚠️  WARNING: GOOGLE_ANALYTICS_ID no configurado")
        print("   Configura la variable de entorno antes de deploy:")
        print("   export GOOGLE_ANALYTICS_ID=G-TU-ID-REAL")

if __name__ == "__main__":
    main()
