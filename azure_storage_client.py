import logging
import os
from typing import Iterable, Optional

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")
AZURE_STORAGE_URL_BASE = os.getenv("AZURE_STORAGE_URL_BASE")

# Inicializa el cliente solo si hay credenciales completas; de lo contrario deja
# el módulo usable y con errores claros en tiempo de ejecución (no al importar).
blob_service_client: Optional[BlobServiceClient] = None
container_client = None

if AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
    except Exception as exc:  # pragma: no cover - defensivo
        logging.error("No se pudo inicializar BlobServiceClient: %s", exc)
else:
    logging.warning("Azure Storage no configurado: faltan AZURE_STORAGE_CONNECTION_STRING o AZURE_STORAGE_CONTAINER")


def _require_clients() -> None:
    if not blob_service_client or not container_client:
        raise RuntimeError("Azure Blob Storage no está configurado correctamente.")


def get_blob_url(blob_name: str) -> str:
    """Devuelve la URL pública de un blob dado su nombre."""
    if not AZURE_STORAGE_URL_BASE:
        raise RuntimeError("Falta AZURE_STORAGE_URL_BASE para construir URLs de blobs.")
    return f"{AZURE_STORAGE_URL_BASE}{blob_name}"


def list_blobs(prefix: Optional[str] = None) -> Iterable[str]:
    """Lista blobs en el contenedor, opcionalmente filtrando por prefijo (images/, videos/, data/)."""
    _require_clients()
    return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]


def upload_blob(blob_name: str, data: bytes, content_type: str = "text/plain", overwrite: bool = False) -> str:
    """
    Carga un blob a Azure Storage.
    
    Args:
        blob_name: Nombre del blob (ej: 'documentos/reporte_2024.txt')
        data: Contenido en bytes
        content_type: Tipo MIME (ej: 'text/plain', 'application/pdf', 'text/csv')
        overwrite: Si sobrescribir si existe
    
    Returns:
        URL pública del blob
    """
    _require_clients()
    try:
        container_client.upload_blob(blob_name, data, content_type=content_type, overwrite=overwrite)
        logging.info(f"Blob subido: {blob_name}")
        return get_blob_url(blob_name)
    except Exception as e:
        logging.error(f"Error subiendo blob {blob_name}: {e}")
        raise


def upload_text_blob(blob_name: str, content: str, overwrite: bool = False) -> str:
    """
    Carga un archivo de texto a Azure Storage.
    
    Args:
        blob_name: Nombre del blob
        content: Contenido de texto
        overwrite: Si sobrescribir si existe
    
    Returns:
        URL pública del blob
    """
    return upload_blob(blob_name, content.encode("utf-8"), content_type="text/plain", overwrite=overwrite)


def download_blob(blob_name: str) -> bytes:
    """
    Descarga un blob desde Azure Storage.
    
    Args:
        blob_name: Nombre del blob
    
    Returns:
        Contenido en bytes
    """
    _require_clients()
    try:
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall()
    except Exception as e:
        logging.error(f"Error descargando blob {blob_name}: {e}")
        raise


def delete_blob(blob_name: str) -> bool:
    """
    Elimina un blob de Azure Storage.
    
    Args:
        blob_name: Nombre del blob
    
    Returns:
        True si se eliminó, False si no existe
    """
    _require_clients()
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        logging.info(f"Blob eliminado: {blob_name}")
        return True
    except Exception as e:
        logging.warning(f"Blob no encontrado o error al eliminar {blob_name}: {e}")
        return False


def blob_exists(blob_name: str) -> bool:
    """
    Verifica si un blob existe en Azure Storage.
    
    Args:
        blob_name: Nombre del blob
    
    Returns:
        True si existe, False si no
    """
    _require_clients()
    try:
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.exists()
    except Exception:
        return False


def upload_blog_image(image_data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """
    Sube una imagen del blog a Azure Storage en la carpeta assets/images/blog/
    
    Args:
        image_data: Datos binarios de la imagen
        filename: Nombre del archivo (ej: 'featured_20260201.jpg')
        content_type: Tipo MIME de la imagen
    
    Returns:
        URL pública de la imagen
    """
    blob_name = f"assets/images/blog/{filename}"
    return upload_blob(blob_name, image_data, content_type=content_type, overwrite=True)

