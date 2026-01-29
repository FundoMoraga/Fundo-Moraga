"""
Módulo para acceder a documentos privados del volumen persistente.
Solo accesible para números de WhatsApp autorizados (SPECIAL_PERSONA_WHATSAPP_NUMBERS).
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import config


KNOWLEDGE_BASE_PATH = Path("/app/private_knowledge")


def is_authorized_user(user_id: Optional[str]) -> bool:
    """Verifica si el usuario está autorizado para acceder a documentos privados."""
    if not user_id:
        return False
    normalized_id = user_id.lower()
    for known in getattr(config, "SPECIAL_PERSONA_WHATSAPP_NUMBERS", []):
        candidate = known.lower()
        if not candidate:
            continue
        if candidate in normalized_id or normalized_id in candidate:
            return True
    return False


def list_documents(directory: str = "") -> List[Dict[str, str]]:
    """
    Lista todos los documentos disponibles en el volumen.
    
    Args:
        directory: Subdirectorio dentro del knowledge base (opcional)
    
    Returns:
        Lista de diccionarios con información de archivos
    """
    if not KNOWLEDGE_BASE_PATH.exists():
        return []
    
    search_path = KNOWLEDGE_BASE_PATH / directory if directory else KNOWLEDGE_BASE_PATH
    
    if not search_path.exists():
        return []
    
    documents = []
    try:
        for item in search_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(KNOWLEDGE_BASE_PATH)
                documents.append({
                    "name": item.name,
                    "path": str(relative_path),
                    "size": item.stat().st_size,
                    "extension": item.suffix,
                    "directory": str(relative_path.parent) if relative_path.parent != Path(".") else "root"
                })
    except Exception as e:
        print(f"Error listing documents: {e}")
    
    return documents


def read_document(file_path: str, max_chars: int = 10000) -> Optional[str]:
    """
    Lee el contenido de un documento de texto.
    
    Args:
        file_path: Ruta relativa al documento dentro del knowledge base
        max_chars: Máximo de caracteres a leer (para evitar sobrecarga)
    
    Returns:
        Contenido del archivo como string, o None si hay error
    """
    if not KNOWLEDGE_BASE_PATH.exists():
        return None
    
    full_path = KNOWLEDGE_BASE_PATH / file_path
    
    if not full_path.exists() or not full_path.is_file():
        return None
    
    # Verificar que el archivo esté dentro del knowledge base (seguridad)
    try:
        full_path.resolve().relative_to(KNOWLEDGE_BASE_PATH.resolve())
    except ValueError:
        return None
    
    try:
        # Intentar leer como texto
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
            if len(content) == max_chars:
                content += "\n...(contenido truncado)"
            return content
    except UnicodeDecodeError:
        # Si no es texto, retornar info del archivo
        return f"[Archivo binario: {file_path}, tamaño: {full_path.stat().st_size} bytes]"
    except Exception as e:
        return f"[Error leyendo archivo: {str(e)}]"


def search_documents(query: str) -> List[Dict[str, str]]:
    """
    Busca documentos por nombre o contenido.
    
    Args:
        query: Término de búsqueda
    
    Returns:
        Lista de documentos que coinciden con la búsqueda
    """
    all_docs = list_documents()
    query_lower = query.lower()
    
    results = []
    for doc in all_docs:
        # Buscar en nombre de archivo
        if query_lower in doc["name"].lower() or query_lower in doc["path"].lower():
            results.append(doc)
            continue
        
        # Para archivos de texto pequeños, buscar en contenido
        if doc["extension"] in [".txt", ".md", ".json", ".csv"]:
            content = read_document(doc["path"], max_chars=50000)
            if content and query_lower in content.lower():
                results.append({**doc, "match": "content"})
    
    return results


def get_document_summary() -> str:
    """
    Genera un resumen de los documentos disponibles.
    
    Returns:
        String con resumen formateado
    """
    docs = list_documents()
    
    if not docs:
        return "No hay documentos disponibles en el knowledge base privado."
    
    summary = f"Tienes {len(docs)} documento(s) disponible(s):\n\n"
    
    # Agrupar por directorio
    by_dir: Dict[str, List[Dict]] = {}
    for doc in docs:
        dir_name = doc["directory"]
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(doc)
    
    for dir_name, dir_docs in sorted(by_dir.items()):
        summary += f"📁 {dir_name}:\n"
        for doc in sorted(dir_docs, key=lambda x: x["name"]):
            size_kb = doc["size"] / 1024
            summary += f"  - {doc['name']} ({size_kb:.1f} KB)\n"
        summary += "\n"
    
    return summary.strip()


# Funciones auxiliares para integración con Hernando

def get_private_knowledge_tools():
    """
    Retorna herramientas para que Hernando acceda a documentos privados.
    Solo se activan para usuarios autorizados.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "list_private_documents",
                "description": "Lista todos los documentos privados disponibles del dueño. Solo usar cuando Efraín pregunta qué documentos tiene disponibles.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_private_document",
                "description": "Lee el contenido de un documento privado específico. Solo usar cuando Efraín solicita ver el contenido de un archivo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Ruta del archivo a leer (ej: 'documento.txt' o 'carpeta/archivo.pdf')"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_private_documents",
                "description": "Busca documentos privados por nombre o contenido. Solo usar cuando Efraín busca algo específico en sus archivos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Término de búsqueda"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]


def execute_private_knowledge_function(function_name: str, arguments: dict) -> str:
    """
    Ejecuta una función de acceso a knowledge privado.
    
    Args:
        function_name: Nombre de la función
        arguments: Argumentos de la función
    
    Returns:
        Resultado formateado como string
    """
    if function_name == "list_private_documents":
        return get_document_summary()
    
    elif function_name == "read_private_document":
        file_path = arguments.get("file_path", "")
        content = read_document(file_path)
        if content is None:
            return f"No se pudo leer el archivo '{file_path}'. Verifica que exista."
        return f"Contenido de {file_path}:\n\n{content}"
    
    elif function_name == "search_private_documents":
        query = arguments.get("query", "")
        results = search_documents(query)
        if not results:
            return f"No se encontraron documentos que coincidan con '{query}'."
        
        response = f"Encontré {len(results)} documento(s) con '{query}':\n\n"
        for doc in results:
            match_type = doc.get("match", "nombre")
            response += f"- {doc['path']} ({match_type})\n"
        return response
    
    return "Función no reconocida."
