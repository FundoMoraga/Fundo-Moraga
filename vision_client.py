"""
Cliente para Azure Computer Vision
Análisis de imágenes: objetos, personas, texto, marcas, etc.
Usa servicio HTTP de Railway si está disponible, o SDK directo como fallback.
"""
import config
import requests
from typing import Optional, Dict, Any, List
import base64

try:
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
    from msrest.authentication import CognitiveServicesCredentials
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False
    ComputerVisionClient = None
    CognitiveServicesCredentials = None


def _use_http_service() -> bool:
    """Verifica si debe usar el servicio HTTP de Railway."""
    return bool(getattr(config, "VISION_SERVICE_URL", None))


def _build_service_url(path: str) -> str:
    """Construye la URL del servicio HTTP con puerto 8080 si no está especificado."""
    service_url = config.VISION_SERVICE_URL
    if ":" not in service_url or service_url.count(":") == 1:  # No tiene puerto
        service_url = f"{service_url}:8080"
    return f"http://{service_url}{path}"


def _get_sdk_client() -> Optional[Any]:
    """Obtiene cliente de Computer Vision SDK si está configurado."""
    if not _SDK_AVAILABLE:
        return None
    endpoint = getattr(config, "AZURE_VISION_ENDPOINT", None)
    key = getattr(config, "AZURE_VISION_KEY", None)
    if not endpoint or not key:
        return None
    return ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))


def analyze_image(image_url: str) -> Optional[Dict[str, Any]]:
    """
    Analiza una imagen desde URL y extrae:
    - Objetos detectados
    - Personas detectadas
    - Descripciones
    - Etiquetas
    - Marcas/logos
    
    Args:
        image_url: URL de la imagen a analizar
    
    Returns:
        Dict con análisis completo o None si hay error
    """
    if _use_http_service():
        try:
            url = _build_service_url("/analyze")
            resp = requests.post(
                url,
                json={"image_url": image_url},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"⚠️ Vision Service HTTP falló (usando SDK como backup): {e}")
    
    # Fallback a SDK
    client = _get_sdk_client()
    if not client:
        return None
    
    try:
        features = [
            VisualFeatureTypes.objects,
            VisualFeatureTypes.people,
            VisualFeatureTypes.description,
            VisualFeatureTypes.tags,
            VisualFeatureTypes.brands,
        ]
        
        results = client.analyze_image_by_url(image_url, features)
        
        analysis = {
            "objects": [],
            "people": [],
            "description": "",
            "tags": [],
            "brands": [],
            "success": True,
        }
        
        # Procesar objetos
        if results.objects:
            analysis["objects"] = [
                {
                    "object": obj.object_name,
                    "confidence": round(obj.confidence * 100, 2),
                    "rectangle": {
                        "x": obj.rectangle.x,
                        "y": obj.rectangle.y,
                        "w": obj.rectangle.w,
                        "h": obj.rectangle.h,
                    }
                }
                for obj in results.objects
            ]
        
        # Procesar personas
        if hasattr(results, 'people') and results.people:
            analysis["people"] = [
                {
                    "confidence": round(person.confidence * 100, 2),
                    "rectangle": {
                        "x": person.face_rectangle.x,
                        "y": person.face_rectangle.y,
                        "w": person.face_rectangle.w,
                        "h": person.face_rectangle.h,
                    }
                }
                for person in results.people
            ]
        
        # Descripción
        if results.description:
            analysis["description"] = results.description.captions[0].text if results.description.captions else ""
            analysis["description_confidence"] = round(
                results.description.captions[0].confidence * 100, 2
            ) if results.description.captions else 0
        
        # Etiquetas
        if results.tags:
            analysis["tags"] = [
                {
                    "name": tag.name,
                    "confidence": round(tag.confidence * 100, 2)
                }
                for tag in results.tags
            ]
        
        # Marcas/logos
        if results.brands:
            analysis["brands"] = [
                {
                    "name": brand.name,
                    "confidence": round(brand.confidence * 100, 2),
                    "rectangle": {
                        "x": brand.rectangle.x,
                        "y": brand.rectangle.y,
                        "w": brand.rectangle.w,
                        "h": brand.rectangle.h,
                    }
                }
                for brand in results.brands
            ]
        
        return analysis
    
    except Exception as e:
        print(f"⚠️ Excepción en análisis de imagen: {e}")
        return None


def detect_objects(image_url: str) -> Optional[Dict[str, Any]]:
    """
    Detecta objetos en una imagen (especializado).
    
    Returns:
        Dict con lista de objetos detectados
    """
    analysis = analyze_image(image_url)
    if not analysis:
        return None
    
    return {
        "success": True,
        "objects_detected": analysis.get("objects", []),
        "total_objects": len(analysis.get("objects", [])),
    }


def detect_people(image_url: str) -> Optional[Dict[str, Any]]:
    """
    Detecta personas en una imagen.
    
    Returns:
        Dict con cantidad y posiciones de personas
    """
    analysis = analyze_image(image_url)
    if not analysis:
        return None
    
    return {
        "success": True,
        "people_detected": analysis.get("people", []),
        "total_people": len(analysis.get("people", [])),
    }


def get_image_description(image_url: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una descripción textual de la imagen.
    
    Returns:
        Dict con descripción y confianza
    """
    analysis = analyze_image(image_url)
    if not analysis:
        return None
    
    return {
        "success": True,
        "description": analysis.get("description", ""),
        "confidence": analysis.get("description_confidence", 0),
        "tags": analysis.get("tags", []),
    }


def extract_text_from_image(image_url: str) -> Optional[Dict[str, Any]]:
    """
    Extrae texto de una imagen (OCR).
    
    Note: Usa servicio OCR separado si está disponible.
    
    Returns:
        Dict con texto extraído
    """
    if _use_http_service():
        try:
            url = _build_service_url("/ocr")
            resp = requests.post(
                url,
                json={"image_url": image_url},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"⚠️ Error llamando servicio OCR HTTP: {e}")
    
    # Fallback a SDK
    client = _get_sdk_client()
    if not client:
        return None
    
    try:
        results = client.read_in_stream_async(image_url)
        operation_id = results.headers["Operation-Location"].split("/")[-1]
        
        while True:
            result = client.get_read_result(operation_id)
            if result.status.lower() not in ["not started", "running"]:
                break
        
        text = ""
        if result.status.lower() == "succeeded":
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    text += line.text + "\n"
        
        return {
            "success": True,
            "text": text.strip(),
        }
    
    except Exception as e:
        print(f"⚠️ Excepción en OCR: {e}")
        return None
