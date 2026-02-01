"""
Cliente de Pexels API para obtener imágenes de forma gratuita
Documentación: https://www.pexels.com/api/documentation/
"""
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PexelsClient:
    """Cliente para consumir la API de Pexels y obtener imágenes relevantes"""
    
    BASE_URL = "https://api.pexels.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de Pexels
        
        Args:
            api_key: Clave API de Pexels (opcional - sin clave funciona con límites)
        """
        self.api_key = api_key
        self.headers = {
            "User-Agent": "Fundo-Moraga-Blog/1.0"
        }
        if api_key:
            self.headers["Authorization"] = api_key
    
    def search_images(
        self,
        query: str,
        per_page: int = 5,
        page: int = 1,
        orientation: str = "landscape"
    ) -> list[Dict[str, Any]]:
        """
        Busca imágenes en Pexels por palabra clave
        
        Args:
            query: Término de búsqueda
            per_page: Número de resultados (max 80)
            page: Número de página
            orientation: "landscape", "portrait", o "square"
        
        Returns:
            Lista de imágenes con información de URLs
        """
        try:
            url = f"{self.BASE_URL}/search"
            params: Dict[str, Any] = {
                "query": query,
                "per_page": min(per_page, 80),
                "page": page,
                "orientation": orientation,
                "size": "large"  # Preferir imágenes grandes
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get("photos", [])
            
            logger.info(f"✅ Pexels: {len(photos)} imágenes encontradas para '{query}'")
            return photos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error buscando en Pexels: {e}")
            return []
    
    def get_curated_images(
        self,
        per_page: int = 5,
        page: int = 1,
        orientation: str = "landscape"
    ) -> list[Dict[str, Any]]:
        """
        Obtiene imágenes curadas (recomendadas) de Pexels
        Útil como fallback cuando no hay búsqueda específica
        
        Args:
            per_page: Número de resultados
            page: Número de página
            orientation: Orientación de la imagen
        
        Returns:
            Lista de imágenes curadas
        """
        try:
            url = f"{self.BASE_URL}/curated"
            params: Dict[str, Any] = {
                "per_page": min(per_page, 80),
                "page": page,
                "orientation": orientation,
                "size": "large"
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get("photos", [])
            
            logger.info(f"✅ Pexels Curated: {len(photos)} imágenes obtenidas")
            return photos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo imágenes curadas: {e}")
            return []
    
    def get_best_image_url(
        self,
        photos: list[Dict[str, Any]],
        size: str = "large"
    ) -> Optional[str]:
        """
        Selecciona la mejor URL de imagen de una lista de fotos
        
        Args:
            photos: Lista de fotos de Pexels
            size: Tamaño deseado ("large", "medium", "small")
        
        Returns:
            URL de la mejor imagen o None
        """
        if not photos:
            return None
        
        best_photo = photos[0]
        src = best_photo.get("src", {})
        
        # Intentar obtener en orden de preferencia
        size_map = {
            "large": src.get("large", src.get("medium", src.get("small"))),
            "medium": src.get("medium", src.get("large", src.get("small"))),
            "small": src.get("small", src.get("medium", src.get("large")))
        }
        
        url = size_map.get(size)
        
        if url:
            # Incluir atribución en parámetros de la URL para tracking
            photographer = best_photo.get("photographer", "Photographer")
            logger.info(f"✅ Imagen seleccionada: {photographer} - {url[:50]}...")
        
        return url
    
    def format_attribution(self, photo: Dict[str, Any]) -> str:
        """
        Genera atribución apropiada para la foto
        
        Args:
            photo: Objeto de foto de Pexels
        
        Returns:
            String de atribución HTML
        """
        photographer = photo.get("photographer", "Unknown")
        photo_url = photo.get("url", "https://www.pexels.com")
        
        return f'<a href="{photo_url}" target="_blank">Photo by {photographer} on Pexels</a>'


def get_pexels_client(api_key: Optional[str] = None) -> PexelsClient:
    """Factory para obtener instancia del cliente Pexels"""
    return PexelsClient(api_key=api_key)
