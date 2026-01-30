"""
Cliente para Vision Service - Análisis doctoral de imágenes con Azure Computer Vision
Proporciona análisis de alto nivel académico para imágenes encontradas en búsquedas
"""
import requests
import os
from typing import Dict, Any, Optional, List
import json

VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://localhost:8080")


class VisionServiceClient:
    """Cliente para interactuar con Vision Service"""
    
    def __init__(self):
        self.base_url = VISION_SERVICE_URL.rstrip('/')
        self.session = requests.Session()
    
    def health(self) -> Dict[str, Any]:
        """
        Verifica salud del servicio Vision.
        
        Returns:
            Dict con estado del servicio
        """
        try:
            endpoint = f"{self.base_url}/health"
            response = self.session.get(endpoint, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}
    
    def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """
        Analiza una imagen de forma doctoral con Azure Computer Vision.
        Extrae objetos, personas, descripción, tags, marcas.
        
        Args:
            image_url: URL de la imagen a analizar
        
        Returns:
            Dict con análisis completo de la imagen
            {
                "objects": [{"object": "...", "confidence": 95.2, "rectangle": {...}}, ...],
                "people": [{"confidence": 95.0, "rectangle": {...}}, ...],
                "description": "Descripción detallada de la imagen...",
                "description_confidence": 98.5,
                "tags": [{"name": "...", "confidence": 95.2}, ...],
                "brands": [{"name": "...", "confidence": 95.2, "rectangle": {...}}, ...],
                "success": true
            }
        """
        try:
            endpoint = f"{self.base_url}/analyze"
            payload = {"image_url": image_url}
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "image_url": image_url,
                "success": False,
                "objects": [],
                "people": [],
                "description": "",
                "tags": [],
                "brands": []
            }
    
    def extract_text(self, image_url: str) -> Dict[str, Any]:
        """
        Extrae texto de una imagen (OCR) con análisis doctoral.
        Útil para documentos, señales, etc.
        
        Args:
            image_url: URL de la imagen
        
        Returns:
            Dict con texto extraído
            {
                "text": "Texto extraído de la imagen...",
                "success": true
            }
        """
        try:
            endpoint = f"{self.base_url}/ocr"
            payload = {"image_url": image_url}
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "text": "", "success": False}
    
    def analyze_batch(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Analiza múltiples imágenes en paralelo.
        
        Args:
            image_urls: Lista de URLs de imágenes
        
        Returns:
            Lista de análisis por imagen
        """
        results = []
        for url in image_urls:
            try:
                result = self.analyze_image(url)
                result["image_url"] = url
                results.append(result)
            except Exception as e:
                results.append({
                    "image_url": url,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def analyze_with_doctorate_synthesis(self, image_url: str, doctoral_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza imagen con síntesis doctoral avanzada.
        Proporciona análisis de nivel académico con contexto especializado.
        
        Args:
            image_url: URL de la imagen
            doctoral_context: Contexto de área doctoral (tecnología, medicina, etc.)
        
        Returns:
            Dict con análisis doctoral enriquecido
        """
        analysis = self.analyze_image(image_url)
        
        if not analysis.get("success", False):
            return analysis
        
        # Enriquecer análisis con síntesis doctoral
        synthesis = {
            "image_url": image_url,
            "academic_summary": self._synthesize_academic_summary(analysis, doctoral_context),
            "key_findings": self._extract_key_findings(analysis),
            "objects_taxonomy": self._categorize_objects_taxonomy(analysis.get("objects", [])),
            "relevance_score": self._calculate_relevance(analysis),
            "raw_analysis": analysis
        }
        
        return synthesis
    
    @staticmethod
    def _synthesize_academic_summary(analysis: Dict[str, Any], context: Optional[str] = None) -> str:
        """Sintetiza análisis en formato académico"""
        parts = []
        
        if analysis.get("description"):
            parts.append(f"Descripción: {analysis['description']}")
        
        if analysis.get("objects"):
            obj_list = ", ".join([o["object"] for o in analysis["objects"][:5]])
            parts.append(f"Objetos principales: {obj_list}")
        
        if analysis.get("tags"):
            tag_list = ", ".join([t["name"] for t in analysis["tags"][:5]])
            parts.append(f"Clasificación: {tag_list}")
        
        if context:
            parts.append(f"Contexto: {context}")
        
        return "; ".join(parts)
    
    @staticmethod
    def _extract_key_findings(analysis: Dict[str, Any]) -> List[str]:
        """Extrae hallazgos clave de análisis"""
        findings = []
        
        # Objetos principales
        if analysis.get("objects"):
            top_objects = sorted(
                analysis["objects"],
                key=lambda x: x.get("confidence", 0),
                reverse=True
            )[:3]
            for obj in top_objects:
                findings.append(f"Objeto: {obj['object']} ({obj['confidence']}% confianza)")
        
        # Personas detectadas
        if analysis.get("people"):
            findings.append(f"Personas detectadas: {len(analysis['people'])}")
        
        # Marcas detectadas
        if analysis.get("brands"):
            for brand in analysis["brands"]:
                findings.append(f"Marca: {brand['name']} ({brand['confidence']}% confianza)")
        
        return findings
    
    @staticmethod
    def _categorize_objects_taxonomy(objects: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categoriza objetos por taxonomía académica"""
        taxonomy = {
            "living_beings": [],
            "vehicles": [],
            "structures": [],
            "tools_equipment": [],
            "other": []
        }
        
        vehicle_keywords = ["jeep", "car", "truck", "vehicle", "auto", "coche", "vehículo"]
        living_keywords = ["person", "people", "animal", "dog", "cat", "bird", "gente", "animal"]
        structure_keywords = ["building", "house", "bridge", "road", "estructura", "edificio"]
        tool_keywords = ["tool", "equipment", "device", "machinery", "herramienta", "equipo"]
        
        for obj in objects:
            obj_name = obj.get("object", "").lower()
            
            if any(kw in obj_name for kw in living_keywords):
                taxonomy["living_beings"].append(obj_name)
            elif any(kw in obj_name for kw in vehicle_keywords):
                taxonomy["vehicles"].append(obj_name)
            elif any(kw in obj_name for kw in structure_keywords):
                taxonomy["structures"].append(obj_name)
            elif any(kw in obj_name for kw in tool_keywords):
                taxonomy["tools_equipment"].append(obj_name)
            else:
                taxonomy["other"].append(obj_name)
        
        # Limpiar categorías vacías
        return {k: v for k, v in taxonomy.items() if v}
    
    @staticmethod
    def _calculate_relevance(analysis: Dict[str, Any]) -> float:
        """Calcula puntuación de relevancia (0-100)"""
        score = 0.0
        
        # Descripción con confianza
        if analysis.get("description_confidence"):
            score += analysis["description_confidence"] * 0.4
        
        # Cantidad y confianza de objetos
        if analysis.get("objects"):
            avg_confidence = sum(o.get("confidence", 0) for o in analysis["objects"]) / len(analysis["objects"])
            score += avg_confidence * 0.3
        
        # Tags (clasificación)
        if analysis.get("tags"):
            avg_confidence = sum(t.get("confidence", 0) for t in analysis["tags"]) / len(analysis["tags"])
            score += avg_confidence * 0.2
        
        # Marcas detectadas (+10 puntos bonus)
        if analysis.get("brands"):
            score += 10
        
        # Normalizar a 0-100
        return min(100.0, score)


# Singleton
_vision_client = None


def get_vision_service_client() -> VisionServiceClient:
    """Obtiene instancia singleton del cliente Vision Service"""
    global _vision_client
    if _vision_client is None:
        _vision_client = VisionServiceClient()
    return _vision_client
