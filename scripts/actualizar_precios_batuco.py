"""
Script para actualizar precios y servicios de Batuco Off Road en Cosmos DB
Actualiza el documento hernando_personalidad_v1 con información correcta
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cosmos_client import get_memory_store
from datetime import datetime
import config

def actualizar_precios_batuco():
    """Actualiza información de precios y servicios en Cosmos DB"""
    
    try:
        # Conectar a Cosmos (contenedor de prompts)
        from azure.cosmos import CosmosClient
        
        cosmos_endpoint = config.COSMOS_ENDPOINT
        cosmos_key = config.COSMOS_KEY
        
        if not cosmos_endpoint or not cosmos_key:
            print("❌ Faltan credenciales de Cosmos DB")
            return False
        
        client = CosmosClient(cosmos_endpoint, cosmos_key)
        database = client.get_database_client(config.COSMOS_PROMPTS_DB)  # "Entrenamiento"
        container = database.get_container_client(config.COSMOS_PROMPTS_CONTAINER)  # "Hernando"
        
        # Leer documento actual
        doc_id = "hernando_personalidad_v1"
        print(f"📖 Leyendo documento {doc_id}...")
        
        try:
            doc = container.read_item(item=doc_id, partition_key="Hernando")
        except:
            print(f"❌ No se encontró el documento {doc_id}")
            return False
        
        # Texto actualizado para la sección de actividades off-road
        nueva_seccion_offroad = """🚙 ACTIVIDADES TODOTERRENO:
Las actividades off-road son operadas EXCLUSIVAMENTE por Batuco Off Road:

HORARIOS:
- Lunes a Viernes: 9:00 AM - 5:00 PM
- Sábado: Solo grupos privados (reserva anticipada)
- Domingo: Generalmente cerrado, salvo "Fecha Libre" anunciada en Instagram

PRECIOS:
- Lunes a Viernes: $15.000 automóviles, $10.000 motos (por vehículo/día)
- Sábado y Domingo: $200.000 por día (arriendo completo del campo)
- EXCEPCIÓN "Fecha Libre": Cuando se anuncia por Instagram @batuco_offroad, se abre sábado o domingo con tarifa normal de semana ($15.000 vehículos / $10.000 motos)

SERVICIOS INCLUIDOS:
✅ Baño disponible en el lugar
✅ Rutas trazadas (la más larga: ~3 km, extensible hasta 7 km)
✅ Campo abierto para exploración
✅ Zona de estacionamiento

ACTIVIDADES:
- Rutas 4x4
- Enduro
- Experiencias todoterreno
- Eventos de aventura motorizada
- Eventos privados/corporativos: Valores y condiciones personalizadas

IMPORTANTE: 
- Para eventos privados/corporativos contactar: contacto@fundomoraga.com / +5699 9392122
- Las "Fechas Libres" se anuncian exclusivamente por Instagram (@batuco_offroad)"""

        # Nueva sección sobre "Fecha Libre"
        seccion_fecha_libre = """

## "FECHA LIBRE" - DOMINGOS ESPECIALES

¿Qué es una "Fecha Libre"?
- Son domingos especiales que abrimos al público con tarifa normal de semana
- Se anuncian con anticipación en Instagram: @batuco_offroad y @fundomoraga
- Horario: 10:00 AM - 5:00 PM
- Precio: $15.000 por automóvil, $10.000 por moto (igual que lunes a viernes)
- No es necesario arrendar el día completo

¿Cómo saber cuándo hay "Fecha Libre"?
- Revisa nuestro Instagram @batuco_offroad donde se publican con anticipación
- Síguenos para estar al tanto de estas oportunidades especiales
- Cuando pregunten por domingos, menciona esta opción y sugiere revisar Instagram

IMPORTANTE: 
- Los domingos regulares NO están disponibles (solo sábado con arriendo completo)
- "Fecha Libre" es la ÚNICA excepción para domingos
- Siempre deriva a Instagram para confirmar próximas fechas libres"""

        # Preguntas frecuentes adicionales
        nuevas_preguntas = """

¿Tienen baño disponible?
- Sí. Contamos con baño en el lugar para uso de visitantes.

¿Cuánto cuesta ir un fin de semana?
- Sábado y domingo: $200.000 por día (arriendo completo del campo)
- EXCEPCIÓN: En "Fechas Libres" (anunciadas por Instagram), el precio es el normal de semana: $15.000 vehículos / $10.000 motos
- Para sábados con grupos, coordinamos según disponibilidad"""

        # Actualizar contenido
        content = doc.get('content', '')
        
        # Buscar y reemplazar sección de actividades todoterreno
        import re
        
        # Patrón para encontrar la sección de actividades todoterreno
        pattern_offroad = r'🚙 ACTIVIDADES TODOTERRENO:.*?(?=\n\n[📷🏞️]|\n\n## HISTORIA)'
        
        if re.search(pattern_offroad, content, re.DOTALL):
            content = re.sub(pattern_offroad, nueva_seccion_offroad, content, flags=re.DOTALL)
            print("✅ Actualizada sección de ACTIVIDADES TODOTERRENO")
        else:
            print("⚠️ No se encontró la sección de actividades todoterreno")
        
        # Agregar sección de "Fecha Libre" antes de PREGUNTAS FRECUENTES
        if '## PREGUNTAS FRECUENTES' in content and '"FECHA LIBRE"' not in content:
            content = content.replace('## PREGUNTAS FRECUENTES', seccion_fecha_libre + '\n\n## PREGUNTAS FRECUENTES')
            print("✅ Agregada sección 'FECHA LIBRE'")
        
        # Agregar nuevas preguntas frecuentes
        if '¿Tienen baño disponible?' not in content:
            # Buscar el final de PREGUNTAS FRECUENTES
            pattern_faq_end = r'(¿El fundo está abierto al público general\?.*?previa coordinación formal\.)'
            if re.search(pattern_faq_end, content, re.DOTALL):
                content = re.sub(
                    pattern_faq_end,
                    r'\1' + nuevas_preguntas,
                    content,
                    flags=re.DOTALL
                )
                print("✅ Agregadas nuevas preguntas frecuentes")
        
        # Actualizar documento
        doc['content'] = content
        doc['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
        
        print("💾 Guardando cambios en Cosmos DB...")
        container.replace_item(item=doc, body=doc)
        
        print("✅ ¡Actualización completada exitosamente!")
        print("\n📋 Resumen de cambios:")
        print("  - Precios actualizados (sábado/domingo: $200.000)")
        print("  - Información de 'Fecha Libre' agregada")
        print("  - Baño agregado a servicios")
        print("  - Preguntas frecuentes actualizadas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔄 Actualizando precios y servicios de Batuco Off Road en Cosmos DB...\n")
    success = actualizar_precios_batuco()
    
    if success:
        print("\n✅ Todo listo. Los cambios estarán disponibles en la próxima respuesta de Hernando.")
        print("\n💡 Prueba preguntando:")
        print("   - '¿Cuánto cuesta ir un sábado?'")
        print("   - '¿Tienen baño?'")
        print("   - '¿Qué es una fecha libre?'")
    else:
        print("\n❌ Hubo un error. Revisa los logs arriba.")
