"""
Cliente para Azure AI Language (Text Analytics) - Análisis de sentimiento y extracción.
Usa el SDK directamente para menor latencia.
"""
import config
from typing import Optional, Dict, Any

try:
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False
    TextAnalyticsClient = None
    AzureKeyCredential = None


def _get_client() -> Optional[Any]:
    """Obtiene cliente de Text Analytics si está configurado."""
    if not _SDK_AVAILABLE:
        return None
    endpoint = getattr(config, "AZURE_LANGUAGE_ENDPOINT", None)
    key = getattr(config, "AZURE_LANGUAGE_KEY", None)
    if not endpoint or not key:
        return None
    return TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def analyze_sentiment(text: str) -> Optional[Dict[str, Any]]:
    """
    Analiza el sentimiento de un texto.
    
    Returns:
        Dict con 'sentiment' (positive/neutral/negative), 'scores' {positive, neutral, negative}
        None si no está disponible o hay error
    """
    client = _get_client()
    if not client:
        return None
    
    try:
        results = client.analyze_sentiment([text])
        result = results[0]
        if result.is_error:
            print(f"⚠️ Error en análisis de sentimiento: {result.error}")
            return None
        
        return {
            "sentiment": result.sentiment,
            "positive": result.confidence_scores.positive,
            "neutral": result.confidence_scores.neutral,
            "negative": result.confidence_scores.negative,
        }
    except Exception as e:
        print(f"⚠️ Excepción en análisis de sentimiento: {e}")
        return None


def detect_language(text: str) -> Optional[Dict[str, Any]]:
    """Detecta el idioma de un texto."""
    client = _get_client()
    if not client:
        return None
    
    try:
        results = client.detect_language([text])
        result = results[0]
        if result.is_error:
            return None
        
        return {
            "name": result.primary_language.name,
            "iso": result.primary_language.iso6391_name,
            "confidence": result.primary_language.confidence_score,
        }
    except Exception as e:
        print(f"⚠️ Excepción en detección de idioma: {e}")
        return None


def extract_key_phrases(text: str) -> Optional[list]:
    """Extrae frases clave de un texto."""
    client = _get_client()
    if not client:
        return None
    
    try:
        results = client.extract_key_phrases([text])
        result = results[0]
        if result.is_error:
            return None
        return result.key_phrases
    except Exception as e:
        print(f"⚠️ Excepción en extracción de frases clave: {e}")
        return None
