"""
Cliente para Azure AI Language (Text Analytics) - Análisis de sentimiento y extracción.
Usa el servicio HTTP de Railway si está disponible, o el SDK directo como fallback.
"""
import config
import requests
from typing import Optional, Dict, Any

try:
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False
    TextAnalyticsClient = None
    AzureKeyCredential = None


def _use_http_service() -> bool:
    """Verifica si debe usar el servicio HTTP de Railway."""
    return bool(getattr(config, "LANGUAGE_SERVICE_URL", None))


def _get_sdk_client() -> Optional[Any]:
    """Obtiene cliente de Text Analytics SDK si está configurado."""
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
    # Intenta servicio HTTP primero
    if _use_http_service():
        try:
            url = f"http://{config.LANGUAGE_SERVICE_URL}/classify"
            resp = requests.post(url, json={"text": text}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                sentiment_info = data.get("sentiment")
                if sentiment_info:
                    scores = sentiment_info.get("scores", {})
                    return {
                        "sentiment": sentiment_info.get("overall"),
                        "positive": scores.get("positive", 0.0),
                        "neutral": scores.get("neutral", 0.0),
                        "negative": scores.get("negative", 0.0),
                    }
        except Exception as e:
            print(f"⚠️ Error llamando servicio Language HTTP, usando SDK: {e}")
    
    # Fallback a SDK directo
    client = _get_sdk_client()
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
    # Intenta servicio HTTP primero
    if _use_http_service():
        try:
            url = f"http://{config.LANGUAGE_SERVICE_URL}/classify"
            resp = requests.post(url, json={"text": text}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                lang_info = data.get("language")
                if lang_info:
                    return {
                        "name": lang_info.get("name"),
                        "iso": lang_info.get("iso6391Name"),
                        "confidence": lang_info.get("confidenceScore", 0.0),
                    }
        except Exception as e:
            print(f"⚠️ Error llamando servicio Language HTTP: {e}")
    
    # Fallback a SDK
    client = _get_sdk_client()
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
    # Intenta servicio HTTP primero
    if _use_http_service():
        try:
            url = f"http://{config.LANGUAGE_SERVICE_URL}/extract"
            resp = requests.post(url, json={"text": text, "tasks": ["key_phrases"]}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("keyPhrases")
        except Exception as e:
            print(f"⚠️ Error llamando servicio Language HTTP: {e}")
    
    # Fallback a SDK
    client = _get_sdk_client()
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
