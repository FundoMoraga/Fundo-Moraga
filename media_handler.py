"""
Módulo para gestionar la recepción y almacenamiento de archivos adjuntos desde WhatsApp.
Solo accesible para usuarios autorizados (SPECIAL_PERSONA_WHATSAPP_NUMBERS).
"""
import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import mimetypes
import config
import private_knowledge


def download_and_save_media(
    media_url: str,
    filename: Optional[str] = None,
    mimetype: Optional[str] = None,
    user_id: Optional[str] = None,
    caption: Optional[str] = None
) -> Dict[str, Any]:
    """
    Descarga un archivo multimedia de WAHA y lo guarda en el volumen privado.
    
    Args:
        media_url: URL del archivo en WAHA
        filename: Nombre del archivo (opcional, se genera automáticamente)
        mimetype: MIME type del archivo
        user_id: ID del usuario que envió el archivo
        caption: Texto/caption que acompañó al archivo
    
    Returns:
        Diccionario con información del archivo guardado
    """
    # Verificar autorización
    if not private_knowledge.is_authorized_user(user_id):
        return {
            "success": False,
            "error": "No tienes autorización para subir archivos al volumen privado"
        }
    
    # Asegurar que el directorio base existe
    base_path = Path("/app/private_knowledge")
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
    
    # Organizar por fecha y tipo
    today = datetime.now().strftime("%Y-%m-%d")
    file_category = _categorize_by_mimetype(mimetype)
    
    # Crear estructura: /app/private_knowledge/uploads/2026-01-29/images/
    upload_dir = base_path / "uploads" / today / file_category
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre de archivo si no se proporciona
    if not filename:
        ext = _get_extension_from_mimetype(mimetype)
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"file_{timestamp}{ext}"
    
    # Sanitizar nombre de archivo
    safe_filename = _sanitize_filename(filename)
    file_path = upload_dir / safe_filename
    
    # Si el archivo ya existe, agregar sufijo numérico
    counter = 1
    original_stem = file_path.stem
    original_suffix = file_path.suffix
    while file_path.exists():
        safe_filename = f"{original_stem}_{counter}{original_suffix}"
        file_path = upload_dir / safe_filename
        counter += 1
    
    try:
        # Descargar archivo de WAHA
        headers = {}
        if config.WAHA_API_KEY:
            headers["X-Api-Key"] = config.WAHA_API_KEY
        
        response = requests.get(media_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Guardar archivo
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # Crear archivo de metadatos si hay caption
        if caption:
            metadata_path = file_path.with_suffix(file_path.suffix + ".meta.txt")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(f"Fecha: {datetime.now().isoformat()}\n")
                f.write(f"Usuario: {user_id}\n")
                f.write(f"Caption: {caption}\n")
                f.write(f"MIME Type: {mimetype}\n")
        
        # Calcular tamaño
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        relative_path = file_path.relative_to(base_path)
        
        return {
            "success": True,
            "path": str(relative_path),
            "filename": safe_filename,
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
            "mimetype": mimetype,
            "category": file_category,
            "saved_at": datetime.now().isoformat(),
            "has_caption": bool(caption)
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Error descargando archivo: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error guardando archivo: {str(e)}"
        }


def _categorize_by_mimetype(mimetype: Optional[str]) -> str:
    """Categoriza el archivo por su MIME type."""
    if not mimetype:
        return "otros"
    
    mimetype = mimetype.lower()
    
    if mimetype.startswith("image/"):
        return "imagenes"
    elif mimetype.startswith("video/"):
        return "videos"
    elif mimetype.startswith("audio/"):
        return "audios"
    elif mimetype in ["application/pdf"]:
        return "pdfs"
    elif mimetype in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-word"
    ]:
        return "documentos"
    elif mimetype in [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]:
        return "hojas_calculo"
    elif mimetype in [
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ]:
        return "presentaciones"
    elif mimetype.startswith("text/"):
        return "textos"
    else:
        return "otros"


def _get_extension_from_mimetype(mimetype: Optional[str]) -> str:
    """Obtiene la extensión de archivo basada en el MIME type."""
    if not mimetype:
        return ".bin"
    
    ext = mimetypes.guess_extension(mimetype)
    if ext:
        return ext
    
    # Extensiones comunes que mimetypes a veces no reconoce
    common_exts = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }
    
    return common_exts.get(mimetype.lower(), ".bin")


def _sanitize_filename(filename: str) -> str:
    """Sanitiza el nombre de archivo para evitar problemas de seguridad."""
    # Eliminar caracteres peligrosos
    dangerous_chars = ['/', '\\', '..', '\0', '\n', '\r', '\t']
    safe_name = filename
    
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Limitar longitud
    if len(safe_name) > 200:
        name_part = safe_name[:190]
        ext_part = Path(safe_name).suffix
        safe_name = name_part + ext_part
    
    return safe_name


def format_save_confirmation(result: Dict[str, Any]) -> str:
    """
    Formatea un mensaje de confirmación amigable para el usuario.
    
    Args:
        result: Resultado de download_and_save_media
    
    Returns:
        Mensaje formateado para el usuario
    """
    if not result.get("success"):
        error = result.get("error", "Error desconocido")
        return f"❌ No pude guardar el archivo: {error}"
    
    categoria_emoji = {
        "imagenes": "🖼️",
        "videos": "🎥",
        "audios": "🎵",
        "pdfs": "📄",
        "documentos": "📝",
        "hojas_calculo": "📊",
        "presentaciones": "📊",
        "textos": "📃",
        "otros": "📁"
    }
    
    emoji = categoria_emoji.get(result.get("category", "otros"), "📁")
    filename = result.get("filename", "archivo")
    size_mb = result.get("size_mb", 0)
    category = result.get("category", "otros").replace("_", " ")
    path = result.get("path", "")
    
    mensaje = f"""{emoji} ¡Archivo guardado exitosamente!

📁 Nombre: {filename}
📏 Tamaño: {size_mb} MB
📂 Categoría: {category}
🗂️ Ruta: {path}

Ya está disponible en tu volumen privado. Puedes pedirme que te muestre los archivos en cualquier momento."""
    
    if result.get("has_caption"):
        mensaje += "\n\n💬 También guardé el texto que acompañó al archivo."
    
    return mensaje
