"""
Script para generar artículos placeholder adicionales del blog
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blog_publisher import BlogPublisher
from datetime import datetime, timezone, timedelta

# Artículos placeholder adicionales
PLACEHOLDER_ARTICLES = [
    {
        "title": "Novedades Temporada 2026: Nuevas Rutas",
        "subtitle": "Inauguramos 3 nuevos circuitos 4x4 con diferentes niveles de dificultad",
        "slug": "novedades-temporada-2026",
        "category": "noticias",
        "keywords": ["temporada 2026", "nuevas rutas", "circuitos 4x4", "fundo moraga", "batuco"],
        "excerpt": "Descubre las nuevas rutas que hemos inaugurado para la temporada 2026. Tres circuitos diseñados profesionalmente para todos los niveles.",
        "reading_time_minutes": 4,
        "content_html": """
        <h2>Nuevos Circuitos 2026</h2>
        <p>En Fundo Moraga estamos orgullosos de presentar tres nuevos circuitos off-road profesionalmente diseñados para la temporada 2026. Estos trazados han sido cuidadosamente planificados para ofrecer desafíos progresivos, desde principiantes hasta pilotos experimentados.</p>
        
        <h2>Circuito Principiante: El Despertar</h2>
        <p>Un recorrido de 2.5 kilómetros diseñado específicamente para quienes dan sus primeros pasos en el off-road. Con pendientes suaves, cruces de agua controlados, y secciones de tierra compactada, este circuito permite familiarizarse con las técnicas básicas del manejo todoterreno en un entorno seguro y supervisado. Ideal para familias y grupos corporativos que buscan una primera experiencia 4x4.</p>
        
        <p>El circuito incluye estaciones de aprendizaje donde nuestros instructores explican técnicas esenciales: uso de tracción 4x4, cruces de agua, manejo en pendientes, y recuperación básica. Es la puerta de entrada perfecta al mundo del off-road, construyendo confianza gradualmente mientras los participantes disfrutan de los hermosos paisajes de Batuco.</p>
        
        <h2>Circuito Intermedio: El Desafío</h2>
        <p>Para conductores con experiencia previa, el circuito intermedio ofrece 4 kilómetros de terreno variado con obstáculos técnicos que requieren planificación y ejecución precisa. Incluye secciones rocosas, vados profundos, pendientes pronunciadas de hasta 35 grados, y zonas de arena suelta que pondrán a prueba tus habilidades de lectura de terreno y control del vehículo.</p>
        
        <p>Este circuito está diseñado para enseñar técnicas avanzadas como el uso de diferenciales, líneas de ataque en obstáculos complejos, y recuperación con winch. Los participantes aprenden a evaluar riesgos, seleccionar trayectorias óptimas, y trabajar en equipo cuando la situación lo requiere. Es perfecto para entusiastas que buscan mejorar significativamente sus capacidades de manejo todoterreno.</p>
        
        <h2>Circuito Experto: La Conquista</h2>
        <p>Nuestro circuito más desafiante, reservado para pilotos experimentados y vehículos preparados. Con 6 kilómetros de terreno extremadamente técnico, incluye rocas de tamaño considerable, cruces de agua profundos, pendientes de hasta 45 grados, y secciones de barro profundo que requieren habilidad excepcional y vehículos con modificaciones apropiadas.</p>
        
        <p>Este circuito no es para todos. Requiere experiencia previa demostrable, vehículo en excelente condición mecánica, y equipo de recuperación completo. Nuestros instructores evalúan cada vehículo y conductor antes de autorizar el acceso. Es el test definitivo de habilidad de pilotaje y preparación de vehículo, diseñado para quienes buscan el máximo desafío en un entorno controlado.</p>
        
        <h2>Seguridad y Sostenibilidad</h2>
        <p>Todos nuestros circuitos han sido diseñados con protocolos rigurosos de seguridad. Contamos con sistemas de comunicación en todo el recorrido, vehículos de rescate en stand-by, y personal capacitado en primeros auxilios. Además, hemos implementado medidas de protección ambiental para minimizar el impacto en la flora y fauna local, incluyendo drenajes controlados y señalización de áreas sensibles.</p>
        
        <p>Trabajamos activamente en la restauración de áreas afectadas y educamos a todos los visitantes sobre prácticas responsables de off-road. Nuestra filosofía es "deja solo huellas, lleva solo fotografías" - queremos que las futuras generaciones puedan disfrutar de estos paisajes tal como los encontramos.</p>
        
        <h2>Reserva tu Experiencia</h2>
        <p>Los nuevos circuitos están disponibles desde febrero de 2026. Ofrecemos sesiones guiadas con instructor, alquiler de vehículos preparados para quienes no tienen su propio 4x4, y paquetes especiales para grupos y empresas. Las reservas se pueden realizar a través de nuestro sitio web o contactando directamente con nuestro equipo.</p>
        
        <p>Ven a Fundo Moraga y descubre por qué somos el destino off-road premium de la Región Metropolitana. A solo 15 minutos de Santiago, te espera la aventura de tu vida.</p>
        """
    },
    {
        "title": "Protocolos de Seguridad en Terrenos Off-Road",
        "subtitle": "Normas y mejores prácticas para disfrutar del off-road de forma segura",
        "slug": "seguridad-off-road-protocolos",
        "category": "guias",
        "keywords": ["seguridad off-road", "protocolos", "normas", "buenas prácticas", "4x4"],
        "excerpt": "La seguridad es primordial en el off-road. Conoce los protocolos esenciales para disfrutar de la aventura responsablemente.",
        "reading_time_minutes": 9,
        "content_html": """
        <h2>La Seguridad como Prioridad</h2>
        <p>El off-road es una actividad emocionante que ofrece experiencias únicas, pero también conlleva riesgos inherentes que deben ser gestionados con protocolos claros y disciplina constante. La diferencia entre una aventura memorable y un accidente serio a menudo se reduce a seguir procedimientos de seguridad establecidos y mantener una mentalidad de prevención en todo momento.</p>
        
        <p>En Fundo Moraga hemos desarrollado protocolos de seguridad basados en estándares internacionales y más de una década de experiencia operativa. Estos protocolos no solo protegen a participantes y personal, sino que también preservan el medio ambiente y mantienen nuestras instalaciones en condiciones óptimas para futuras generaciones de entusiastas.</p>
        
        <h2>Briefing Pre-Salida Obligatorio</h2>
        <p>Ningún vehículo sale a circuito sin completar el briefing de seguridad. Durante esta sesión de 15-20 minutos, cubrimos: señales de mano para comunicación sin radio, protocolos de emergencia, límites del recorrido, zonas prohibidas, y comportamientos esperados. Todos los participantes deben confirmar comprensión antes de iniciar.</p>
        
        <p>El briefing incluye demostración de equipo de seguridad: extintores, botiquín de primeros auxilios, sistema de comunicación, y equipo de recuperación. Explicamos cómo y cuándo usar cada elemento. También revisamos las condiciones actuales del terreno - lluvia reciente, áreas inundadas, o tramos cerrados temporalmente por mantenimiento.</p>
        
        <h2>Regla del Nunca Solo</h2>
        <p>Nunca sales solo a circuito, sin excepciones. Incluso conductores experimentados deben ir acompañados de al menos otro vehículo. Esta regla ha salvado vidas - cuando ocurre un problema mecánico o médico, tener respaldo inmediato es crucial. En terrenos remotos, la ayuda puede tardar horas en llegar si te encuentras completamente aislado.</p>
        
        <p>En grupos, establecemos sistema de buddy: cada vehículo tiene un "compañero" específico que monitorea y con quien mantiene contacto visual o por radio. Si pierdes contacto con tu buddy, detienes y esperas hasta restablecer comunicación. Parece simple, pero este sistema ha prevenido innumerables situaciones peligrosas.</p>
        
        <h2>Uso de Equipo de Protección Personal</h2>
        <p>El equipamiento personal básico incluye: calzado cerrado con buen agarre (nada de sandalias o zapatillas ligeras), ropa que cubra brazos y piernas completamente para protección contra ramas y sol, gafas de sol para reducir fatiga visual, y bloqueador solar de alto factor incluso en días nublados. En circuitos técnicos, recomendamos guantes de trabajo para manipular equipos.</p>
        
        <p>Los pasajeros deben usar cinturón de seguridad en todo momento, incluso en maniobras lentas. Los impactos laterales en off-road pueden ser sorpresivamente violentos. Si tu vehículo tiene barra antivuelco interior, considera usar casco - muchos clubes off-road lo requieren obligatoriamente en competencias por buenas razones.</p>
        
        <h2>Protocolos de Recuperación Segura</h2>
        <p>Las recuperaciones (sacar vehículos atascados) son momentos de alto riesgo. Protocolo obligatorio: todos los ocupantes salen de ambos vehículos y se ubican mínimo 1.5 veces el largo de la correa de recuperación, perpendiculares a la línea de tensión. Las correas bajo tensión extrema pueden romperse y convertirse en proyectiles letales.</p>
        
        <p>Nunca uses cadenas o cables metálicos para recuperación dinámica - solo correas textiles diseñadas específicamente para ese propósito. Inspecciona cada correa antes de usar - cualquier deshilachado o daño significa reemplazo inmediato. Usa mantas de recuperación sobre la correa para atrapar energía en caso de ruptura.</p>
        
        <p>En recuperaciones con winch, la línea de trabajo debe tener siempre una manta de recuperación sobre ella. El operador del winch usa guantes y mantiene posición lateral a la línea, nunca directamente en línea con la tensión. Los observadores se ubican detrás de rocas grandes o vehículos pesados si es posible.</p>
        
        <h2>Gestión de Cruces de Agua</h2>
        <p>Los cruces de agua son engañosamente peligrosos. Protocolo estándar: el líder del grupo camina el cruce primero, verificando profundidad, corriente, y fondo firme. Usa un palo largo para testear - las corrientes pueden desestabilizarte fácilmente. Si la profundidad supera los respiraderos del motor o la corriente es fuerte, no cruces.</p>
        
        <p>Al cruzar, mantén velocidad constante y moderada - demasiado rápido crea olas que pueden inundar el motor, demasiado lento puede atascarte. Nunca cambies de marcha en medio del cruce. Si el motor se apaga dentro del agua, no intentes arrancarlo - puede causar daños catastróficos por hydrolock. Sal y recupera en seco.</p>
        
        <h2>Manejo de Pendientes Pronunciadas</h2>
        <p>En descensos pronunciados, usa control de descenso (hill descent control) si tu vehículo lo tiene, o primera marcha baja y motor como freno. Nunca apuntes ruedas cuesta arriba en un descenso - es receta para volcamiento. Mantén trayectoria recta cuando sea posible; los giros laterales en pendientes agudas aumentan riesgo de rodar.</p>
        
        <p>En ascensos, selecciona la línea correcta antes de comprometerte. Una vez iniciado, mantén momento constante - si pierdes tracción y te detienes a mitad de subida, estás en situación peligrosa. Si debes retroceder, hazlo lentamente, con alguien guiándote por afuera si es posible.</p>
        
        <h2>Señalización y Comunicación</h2>
        <p>Usamos sistema de señales de mano estandarizado: puño cerrado = detente, palma abierta = más despacio, pulgar arriba = adelante/OK, brazo cruzado sobre cabeza = emergencia. Todos los participantes deben conocer y usar estas señales consistentemente. En grupos grandes, el líder repite señales para que todo el convoy las vea.</p>
        
        <p>Los radios portátiles son obligatorios en expediciones largas. Canal acordado previamente, checks cada 15 minutos. Protocolo de emergencia: "Mayday, mayday, mayday" seguido de ubicación y naturaleza de emergencia. Todos los vehículos escuchan canal en todo momento, incluso si no están transmitiendo.</p>
        
        <h2>Respeto por Límites Personales</h2>
        <p>Nunca presiones a alguien para intentar un obstáculo que le genere ansiedad significativa. El off-road debe ser desafiante pero no aterrador. Hay líneas alternativas para casi todo obstáculo. Un conductor ansioso comete errores, poniendo en riesgo vehículo y ocupantes. Mejor dar vuelta y buscar otra ruta.</p>
        
        <p>Si sientes que un obstáculo excede tus habilidades o capacidades de tu vehículo, comunícalo sin vergüenza. Los conductores experimentados respetan enormemente a quienes conocen sus límites. Siempre puedes volver otro día con más experiencia o vehículo mejor preparado.</p>
        
        <h2>Protocolo de Emergencias Médicas</h2>
        <p>Todo grupo debe tener al menos una persona con entrenamiento en primeros auxilios. El botiquín debe incluir: vendas estériles, torniquete CAT, desinfectante, medicamentos básicos (analgésicos, antihistamínicos), manta térmica, y guantes de látex. En áreas remotas, considera llevar radio satelital o dispositivo SPOT para emergencias donde no hay cobertura celular.</p>
        
        <p>Ante emergencia médica seria: 1) Detén todo movimiento inmediatamente, 2) Evalúa la situación - no te conviertas en segunda víctima, 3) Inicia primeros auxilios si estás entrenado, 4) Contacta servicios de emergencia inmediatamente, 5) Prepara punto de encuentro para ambulancia/helicóptero. Coordenadas GPS exactas pueden salvar vidas.</p>
        
        <h2>Fundo Moraga: Tu Espacio Seguro para Aventuras</h2>
        <p>En Fundo Moraga implementamos todos estos protocolos y más. Nuestros circuitos están diseñados con rutas de escape, puntos de comunicación, y acceso para vehículos de emergencia. Personal capacitado monitorea todas las actividades, y nuestro sistema de respuesta rápida puede llegar a cualquier punto del predio en minutos.</p>
        
        <p>Ofrecemos capacitaciones específicas en seguridad off-road donde practicas estos protocolos en entorno controlado. Aprende de nuestros instructores experimentados que han visto y resuelto situaciones de todo tipo. La inversión en conocimiento de seguridad es la mejor preparación para disfrutar el off-road por años.</p>
        
        <p>Visítanos y descubre cómo la seguridad profesional se combina con la emoción de la aventura todoterreno.</p>
        """
    }
]

def generate_placeholders():
    """Genera los artículos placeholder"""
    publisher = BlogPublisher()
    
    print("\n" + "="*70)
    print("🚀 GENERANDO ARTÍCULOS PLACEHOLDER")
    print("="*70 + "\n")
    
    for i, article_data in enumerate(PLACEHOLDER_ARTICLES, 1):
        print(f"\n[{i}/{len(PLACEHOLDER_ARTICLES)}] Generando: {article_data['title']}")
        
        article_data["generated_at"] = (datetime.now(timezone.utc) - timedelta(days=10+i)).isoformat()
        article_data["author"] = "Hernando IA"
        article_data["status"] = "draft"
        
        try:
            result = publisher.publish_article(article_data, save_to_cosmos=False)
            if result.get("success"):
                print(f"✅ {result['filepath']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*70)
    print("✅ GENERACIÓN COMPLETADA")
    print("="*70 + "\n")

if __name__ == "__main__":
    generate_placeholders()
