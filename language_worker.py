"""
Worker HTTP para clasificación y extracción de texto usando Azure AI Language (Text Analytics).

Endpoints:
- GET /health: estado y variables faltantes
- POST /classify: análisis de sentimiento y detección de idioma
- POST /extract: frases clave, entidades y PII (opcional)
"""
from flask import Flask, jsonify, request
import os

try:
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential
except Exception:
    # Carga diferida: permitimos que /health funcione aun sin dependencias
    TextAnalyticsClient = None  # type: ignore
    AzureKeyCredential = None  # type: ignore

app = Flask(__name__)

# Variables de entorno locales (no importar config para evitar dependencias de Cosmos)
AZURE_LANGUAGE_ENDPOINT = os.getenv("AZURE_LANGUAGE_ENDPOINT", "").rstrip("/")
AZURE_LANGUAGE_KEY = os.getenv("AZURE_LANGUAGE_KEY")


def _missing_config():
    missing = []
    if not AZURE_LANGUAGE_ENDPOINT:
        missing.append("AZURE_LANGUAGE_ENDPOINT")
    if not AZURE_LANGUAGE_KEY:
        missing.append("AZURE_LANGUAGE_KEY")
    # Dependencias del paquete
    if TextAnalyticsClient is None or AzureKeyCredential is None:
        missing.append("azure-ai-textanalytics (pip)")
    return missing


def _get_client():
    endpoint = AZURE_LANGUAGE_ENDPOINT
    key = AZURE_LANGUAGE_KEY
    if not endpoint or not key or TextAnalyticsClient is None or AzureKeyCredential is None:
        return None
    return TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))


@app.get("/health")
def health():
    missing = _missing_config()
    status = "ok" if not missing else "degraded"
    return jsonify({"status": status, "missing": missing}), 200


@app.post("/classify")
def classify():
    missing = _missing_config()
    if missing:
        return jsonify({"error": "Servicio no configurado", "missing": missing}), 503

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Se requiere 'text'"}), 400

    client = _get_client()
    if client is None:
        return jsonify({"error": "Cliente no disponible"}), 503

    try:
        # Detección de idioma
        lang_result = client.detect_language([text])[0]
        detected_lang = None
        if not lang_result.is_error:
            detected_lang = {
                "name": lang_result.primary_language.name,
                "iso6391Name": lang_result.primary_language.iso6391_name,
                "confidenceScore": lang_result.primary_language.confidence_score,
            }

        # Análisis de sentimiento
        sent_result = client.analyze_sentiment([text])
        sent = sent_result[0]
        sentiment = None
        if not sent.is_error:
            sentiment = {
                "overall": sent.sentiment,
                "scores": {
                    "positive": sent.confidence_scores.positive,
                    "neutral": sent.confidence_scores.neutral,
                    "negative": sent.confidence_scores.negative,
                },
                "sentences": [
                    {
                        "text": s.text,
                        "sentiment": s.sentiment,
                        "scores": {
                            "positive": s.confidence_scores.positive,
                            "neutral": s.confidence_scores.neutral,
                            "negative": s.confidence_scores.negative,
                        },
                    }
                    for s in sent.sentences
                ],
            }

        return jsonify({"language": detected_lang, "sentiment": sentiment}), 200
    except Exception as exc:
        return jsonify({"error": "Error analizando texto", "details": str(exc)}), 502


@app.post("/extract")
def extract():
    missing = _missing_config()
    if missing:
        return jsonify({"error": "Servicio no configurado", "missing": missing}), 503

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    tasks = data.get("tasks") or ["key_phrases", "entities", "pii"]
    if not text:
        return jsonify({"error": "Se requiere 'text'"}), 400

    client = _get_client()
    if client is None:
        return jsonify({"error": "Cliente no disponible"}), 503

    result = {}
    try:
        if "key_phrases" in tasks:
            kp = client.extract_key_phrases([text])[0]
            if not kp.is_error:
                result["keyPhrases"] = kp.key_phrases

        if "entities" in tasks:
            ents = client.recognize_entities([text])[0]
            if not ents.is_error:
                result["entities"] = [
                    {
                        "text": e.text,
                        "category": e.category,
                        "subcategory": getattr(e, "subcategory", None),
                        "confidenceScore": e.confidence_score,
                    }
                    for e in ents.entities
                ]

        if "pii" in tasks:
            pii = client.recognize_pii_entities([text])[0]
            if not pii.is_error:
                result["piiEntities"] = [
                    {
                        "text": e.text,
                        "category": e.category,
                        "confidenceScore": e.confidence_score,
                    }
                    for e in pii.entities
                ]

        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": "Error extrayendo información", "details": str(exc)}), 502


if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
