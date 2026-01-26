"""
Script automático para evaluar interacciones de Hernando
Ejecuta el análisis completo sin interacción manual
"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.evaluar_interacciones import InteractionEvaluator


def run_automatic_evaluation():
    """Ejecuta evaluación automática con reporte de 7 días"""
    print("\n" + "="*80)
    print("  🔍 EVALUACIÓN AUTOMÁTICA DE INTERACCIONES DE HERNANDO")
    print("="*80 + "\n")
    
    try:
        evaluator = InteractionEvaluator()
        
        # Ejecutar reporte de últimos 7 días
        evaluator.generate_summary_report(days=7)
        
        print("\n" + "="*80)
        print("  ✅ EVALUACIÓN COMPLETADA")
        print("="*80 + "\n")
        
        print("💡 Para análisis más específicos, ejecuta:")
        print("   python scripts/evaluar_interacciones.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la evaluación: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_automatic_evaluation()
    sys.exit(0 if success else 1)
