"""
Flask REST API — LLM Adversarial Prompt Detection Engine
POST /analyze  →  full detection result
GET  /health   →  liveness check
"""

import os
import sys
import time
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure engine package is importable when running from backend/
sys.path.insert(0, os.path.dirname(__file__))

from engine.hybrid_engine import analyze

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "llm-prompt-guard"}), 200


@app.route("/analyze", methods=["POST"])
def analyze_prompt():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Request body must include a 'prompt' field."}), 400

    prompt = data["prompt"]
    if not isinstance(prompt, str) or not prompt.strip():
        return jsonify({"error": "'prompt' must be a non-empty string."}), 400

    if len(prompt) > 10_000:
        return jsonify({"error": "Prompt exceeds maximum length of 10,000 characters."}), 400

    t0 = time.perf_counter()
    try:
        result = analyze(prompt)
    except Exception as exc:
        logger.exception("Analysis failed: %s", exc)
        return jsonify({"error": "Internal analysis error.", "detail": str(exc)}), 500

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    result["latency_ms"] = latency_ms

    logger.info(
        "label=%s score=%.3f latency=%.1fms rules=%d",
        result["label"],
        result["score"],
        latency_ms,
        len(result["rules_triggered"]),
    )
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    logger.info("Starting LLM Prompt Guard on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
