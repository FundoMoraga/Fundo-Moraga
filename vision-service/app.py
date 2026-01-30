"""
Servicio HTTP para Azure Computer Vision
Expone endpoints REST para análisis de imágenes
"""
from flask import Flask, request, jsonify
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
import os

app = Flask(__name__)

# Configuración desde variables de entorno
VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")
VISION_KEY = os.getenv("AZURE_VISION_KEY")

if not VISION_ENDPOINT or not VISION_KEY:
    raise ValueError("Faltan AZURE_VISION_ENDPOINT o AZURE_VISION_KEY en variables de entorno")

# Cliente de Computer Vision
vision_client = ComputerVisionClient(VISION_ENDPOINT, CognitiveServicesCredentials(VISION_KEY))


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "vision"})


@app.route("/analyze", methods=["POST"])
def analyze_image():
    """
    Analiza una imagen completa
    Body: {"image_url": "https://..."}
    """
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        
        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400
        
        # Features a analizar
        features = [
            VisualFeatureTypes.objects,
            VisualFeatureTypes.tags,
            VisualFeatureTypes.description,
            VisualFeatureTypes.brands,
        ]
        
        # Intentar agregar people (no siempre disponible)
        try:
            features.append(VisualFeatureTypes.faces)
        except:
            pass
        
        results = vision_client.analyze_image(image_url, features)
        
        response = {
            "objects": [],
            "people": [],
            "description": "",
            "tags": [],
            "brands": [],
            "success": True,
        }
        
        # Objetos
        if results.objects:
            response["objects"] = [
                {
                    "object": obj.object_property,
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
        
        # Rostros (como proxy de personas)
        if hasattr(results, 'faces') and results.faces:
            response["people"] = [
                {
                    "confidence": 95.0,  # Estimado
                    "rectangle": {
                        "x": face.face_rectangle.left,
                        "y": face.face_rectangle.top,
                        "w": face.face_rectangle.width,
                        "h": face.face_rectangle.height,
                    }
                }
                for face in results.faces
            ]
        
        # Descripción
        if results.description and results.description.captions:
            response["description"] = results.description.captions[0].text
            response["description_confidence"] = round(results.description.captions[0].confidence * 100, 2)
        
        # Tags
        if results.tags:
            response["tags"] = [
                {"name": tag.name, "confidence": round(tag.confidence * 100, 2)}
                for tag in results.tags
            ]
        
        # Marcas
        if results.brands:
            response["brands"] = [
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
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/ocr", methods=["POST"])
def extract_text():
    """
    Extrae texto de una imagen (OCR)
    Body: {"image_url": "https://..."}
    """
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        
        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400
        
        # Iniciar operación de lectura
        read_response = vision_client.read(image_url, raw=True)
        operation_location = read_response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        
        # Esperar a que termine
        import time
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            result = vision_client.get_read_result(operation_id)
            if result.status.lower() not in ["notstarted", "running"]:
                break
            time.sleep(1)
            attempt += 1
        
        # Extraer texto
        text = ""
        if result.status.lower() == "succeeded":
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    text += line.text + "\n"
        
        return jsonify({
            "text": text.strip(),
            "success": True
        })
    
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
