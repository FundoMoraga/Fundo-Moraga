"""
Worker HTTP simple para traducción de texto con Azure Translator.
"""
from flask import Flask, jsonify, request
import requests
import config

app = Flask(__name__)


def _missing_config():
    missing = []
    if not config.AZURE_TRANSLATOR_ENDPOINT:
        missing.append("AZURE_TRANSLATOR_ENDPOINT")
    if not config.AZURE_TRANSLATOR_KEY:
        missing.append("AZURE_TRANSLATOR_KEY")
    if not config.AZURE_TRANSLATOR_REGION:
        missing.append("AZURE_TRANSLATOR_REGION")
    return missing


@app.get("/health")
def health():
    missing = _missing_config()
    return jsonify(
        {
            "status": "ok" if not missing else "degraded",
            "missing": missing,
        }
    ), 200


@app.post("/translate")
def translate():
    if _missing_config():
        return (
            jsonify({"error": "Servicio no configurado"}),
            503,
        )

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    to_lang = (data.get("to") or "").strip()
    from_lang = (data.get("from") or "").strip()

    if not text:
        return jsonify({"error": "Se requiere 'text'"}), 400
    if not to_lang:
        return jsonify({"error": "Se requiere 'to' (idioma destino)"}), 400

    endpoint = config.AZURE_TRANSLATOR_ENDPOINT.rstrip("/")
    url = f"{endpoint}/translate"
    params = {"api-version": "3.0", "to": to_lang}
    if from_lang:
        params["from"] = from_lang

    headers = {
        "Ocp-Apim-Subscription-Key": config.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": config.AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }

    payload = [{"text": text}]
    try:
        resp = requests.post(url, params=params, headers=headers, json=payload, timeout=15)
    except requests.RequestException as exc:
        return jsonify({"error": "Error conectando a Azure", "details": str(exc)}), 502

    if resp.status_code >= 400:
        return (
            jsonify(
                {
                    "error": "Error de Azure Translator",
                    "status": resp.status_code,
                    "details": resp.text,
                }
            ),
            502,
        )

    data = resp.json()
    if not data or "translations" not in data[0]:
        return jsonify({"error": "Respuesta inesperada de Azure"}), 502

    translation = data[0]["translations"][0]
    detected = data[0].get("detectedLanguage", {})

    return jsonify(
        {
            "text": translation.get("text"),
            "to": translation.get("to"),
            "detected": detected.get("language"),
            "detected_score": detected.get("score"),
        }
    ), 200


if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
