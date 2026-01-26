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

