"""
Cliente para Steel Browser - Navegación web con IA
Permite a Hernando navegar, extraer información y realizar investigaciones web
"""
import requests
import os
from typing import Dict, Any, Optional, List
import json

STEEL_BROWSER_URL = os.getenv("STEEL_BROWSER_URL", "https://steel-browser-hernando.up.railway.app")
STEEL_API_KEY = os.getenv("STEEL_API_KEY")  # Si requiere autenticación


class SteelBrowserClient:
    """Cliente para interactuar con Steel Browser"""
    
    def __init__(self):
        self.base_url = STEEL_BROWSER_URL.rstrip('/')
        self.api_key = STEEL_API_KEY
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def navigate(self, url: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """
        Navega a una URL y extrae contenido.
        
        Args:
            url: URL a visitar
            wait_for: Selector CSS o condición a esperar (opcional)
        
        Returns:
            Dict con contenido extraído
        """
        try:
            endpoint = f"{self.base_url}/api/navigate"
            payload = {"url": url}
            if wait_for:
                payload["wait_for"] = wait_for
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def extract_content(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrae contenido específico de una página.
        
        Args:
            url: URL a analizar
            selector: Selector CSS específico (opcional)
        
        Returns:
            Dict con contenido extraído
        """
        try:
            endpoint = f"{self.base_url}/api/extract"
            payload = {"url": url}
            if selector:
                payload["selector"] = selector
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def search_and_extract(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Busca en Google y extrae contenido de los resultados.
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados a procesar
        
        Returns:
            Dict con resultados y contenido extraído
        """
        try:
            endpoint = f"{self.base_url}/api/search"
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            response = self.session.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "query": query}
    
    def scrape_multiple(self, urls: List[str]) -> Dict[str, Any]:
        """
        Extrae contenido de múltiples URLs en paralelo.
        
        Args:
            urls: Lista de URLs a procesar
        
        Returns:
            Dict con resultados de cada URL
        """
        try:
            endpoint = f"{self.base_url}/api/scrape-batch"
            payload = {"urls": urls}
            
            response = self.session.post(endpoint, json=payload, timeout=90)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "urls": urls}
    
    def execute_script(self, url: str, script: str) -> Dict[str, Any]:
        """
        Ejecuta JavaScript en una página.
        
        Args:
            url: URL donde ejecutar el script
            script: Código JavaScript a ejecutar
        
        Returns:
            Dict con resultado de la ejecución
        """
        try:
            endpoint = f"{self.base_url}/api/execute"
            payload = {
                "url": url,
                "script": script
            }
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def screenshot(self, url: str, full_page: bool = False) -> Dict[str, Any]:
        """
        Captura screenshot de una página.
        
        Args:
            url: URL a capturar
            full_page: Si capturar página completa o solo viewport
        
        Returns:
            Dict con URL o base64 del screenshot
        """
        try:
            endpoint = f"{self.base_url}/api/screenshot"
            payload = {
                "url": url,
                "full_page": full_page
            }
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def research(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        """
        Realiza investigación web profunda sobre un tema.
        Busca, analiza múltiples fuentes y sintetiza información.
        
        Args:
            topic: Tema a investigar
            depth: Profundidad (light, medium, deep)
        
        Returns:
            Dict con hallazgos, fuentes y síntesis
        """
        try:
            endpoint = f"{self.base_url}/api/research"
            payload = {
                "topic": topic,
                "depth": depth
            }
            
            response = self.session.post(endpoint, json=payload, timeout=180)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "topic": topic}
    
    def search_images(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Busca imágenes en Google Images.
        
        Args:
            query: Término de búsqueda (ej: "Jeep Wrangler")
            max_results: Número máximo de imágenes a retornar (1-50)
        
        Returns:
            Dict con URLs de imágenes encontradas
            {
                "images": [
                    {"url": "...", "title": "...", "source": "..."},
                    ...
                ],
                "query": "Jeep Wrangler",
                "total_found": 10
            }
        """
        try:
            # Limitar resultados
            max_results = min(max(1, max_results), 50)
            
            endpoint = f"{self.base_url}/api/search-images"
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            response = self.session.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "query": query, "images": []}


# Singleton
_steel_client = None

def get_steel_browser_client() -> SteelBrowserClient:
    """Obtiene instancia singleton del cliente Steel Browser"""
    global _steel_client
    if _steel_client is None:
        _steel_client = SteelBrowserClient()
    return _steel_client
