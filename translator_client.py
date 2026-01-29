"""
Cliente para el servicio de traducción (Azure Translator).
Usa el servicio HTTP de Railway si está disponible, o el endpoint directo de Azure como fallback.
"""
import config
import requests
from typing import Optional, Dict, Any


def _use_http_service() -> bool:
    return bool(getattr(config, "TRANSLATOR_SERVICE_URL", None))


def _build_service_url(path: str) -> str:
    service_url = config.TRANSLATOR_SERVICE_URL
    # Railway services listen on port 8080
    if ":" not in service_url:
        service_url = f"{service_url}:8080"
    return f"http://{service_url}{path}"


def translate_text(text: str, to_lang: str, from_lang: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Traduce texto usando servicio HTTP interno o Azure Translator directo.

    Returns:
        Dict con "text", "to", "detected" y "detected_score" si hay éxito.
        None si no está disponible o hay error.
    """
    if not text or not to_lang:
        return None

    # Servicio HTTP interno (Railway)
    if _use_http_service():
        try:
            url = _build_service_url("/translate")
            payload = {"text": text, "to": to_lang}
            if from_lang:
                payload["from"] = from_lang
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"⚠️ Error llamando servicio Translator HTTP: {e}")

    # Fallback a Azure Translator directo
    endpoint = getattr(config, "AZURE_TRANSLATOR_ENDPOINT", None)
    key = getattr(config, "AZURE_TRANSLATOR_KEY", None)
    region = getattr(config, "AZURE_TRANSLATOR_REGION", None)
    if not endpoint or not key or not region:
        return None

    try:
        endpoint = endpoint.rstrip("/")
        url = f"{endpoint}/translate"
        params = {"api-version": "3.0", "to": to_lang}
        if from_lang:
            params["from"] = from_lang

        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Ocp-Apim-Subscription-Region": region,
            "Content-Type": "application/json",
        }

        payload = [{"text": text}]
        resp = requests.post(url, params=params, headers=headers, json=payload, timeout=15)
        if resp.status_code >= 400:
            print(f"⚠️ Error Azure Translator: {resp.status_code} {resp.text}")
            return None

        data = resp.json()
        if not data or "translations" not in data[0]:
            return None

        translation = data[0]["translations"][0]
        detected = data[0].get("detectedLanguage", {})
        return {
            "text": translation.get("text"),
            "to": translation.get("to"),
            "detected": detected.get("language"),
            "detected_score": detected.get("score"),
        }
    except Exception as e:
        print(f"⚠️ Excepción Azure Translator: {e}")
        return None
