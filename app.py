"""
app.py - Main Flask Application for MergeMate.

Routes:
- GET  /                  : Renders the MergeMate web interface.
- POST /api/parse         : Parses raw text or uploaded file for Git conflict markers.
- POST /api/resolve       : Resolves parsed conflicts according to user selections.
- GET  /api/sample/<name> : Returns bundled sample conflict files for quick testing.
"""

import os
from flask import Flask, render_template, request, jsonify
from conflict_parser import parse_conflict_text, resolve_conflicts

app = Flask(__name__)

# Directory where sample conflict files reside
SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_conflicts")


@app.route("/")
def index():
    """Renders the main application dashboard."""
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def api_parse():
    """
    Parses conflict text sent via JSON.
    Expects JSON: { "text": "..." }
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")

    if not text.strip():
        return jsonify({
            "success": False,
            "error": "No text provided. Please paste code or upload a file."
        }), 400

    parsed = parse_conflict_text(text)
    return jsonify({
        "success": True,
        "has_conflicts": parsed["has_conflicts"],
        "conflict_count": parsed["conflict_count"],
        "line_ending": parsed["line_ending"],
        "blocks": parsed["blocks"]
    })


@app.route("/api/resolve", methods=["POST"])
def api_resolve():
    """
    Reconstructs clean, resolved code.
    Expects JSON:
    {
        "blocks": [...],
        "resolutions": { "1": "ours", "2": "theirs", ... },
        "line_ending": "\r\n" or "\n" (optional)
    }
    """
    data = request.get_json(silent=True) or {}
    blocks = data.get("blocks", [])
    resolutions = data.get("resolutions", {})
    line_ending = data.get("line_ending")

    if not blocks:
        return jsonify({
            "success": False,
            "error": "No blocks provided for resolution."
        }), 400

    resolved_code = resolve_conflicts(blocks, resolutions, target_ending=line_ending)
    return jsonify({
        "success": True,
        "resolved_code": resolved_code
    })


@app.route("/api/sample/<sample_name>", methods=["GET"])
def api_sample(sample_name):
    """
    Loads bundled sample conflict files for 1-click user testing.
    Allowed samples: 'simple', 'calculator', 'diff3'
    """
    sample_mapping = {
        "simple": "simple_greeting.txt",
        "calculator": "app_calculator.py",
        "diff3": "sample_diff3.py"
    }

    filename = sample_mapping.get(sample_name)
    if not filename:
        return jsonify({"success": False, "error": "Sample not found"}), 404

    filepath = os.path.join(SAMPLES_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"success": True, "filename": filename, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Render and cloud platforms supply the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    # In development, run in debug mode; in production, debug is False
    is_debug = os.environ.get("FLASK_ENV") != "production"
    print(f"[*] Starting MergeMate on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=is_debug)
