from flask import Flask, request, jsonify
import tempfile
import os
import requests  # ← was missing
from flask_cors import CORS
from extractor import process_pdf

app = Flask(__name__)

# ← This is the key fix: allow the specific origin and methods
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

@app.route('/api/llm', methods=['POST', 'OPTIONS'])
def proxy_llm():
    if request.method == 'OPTIONS':
        return '', 204          # preflight
    try:
        payload = request.get_json()
        resp = requests.post(
            "http://10.130.154.133:8000/v1/chat/completions",
            json=payload,
            timeout=300
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # ← was missing the 500

@app.route("/extract", methods=["POST", "OPTIONS"])
def extract():
    if request.method == 'OPTIONS':
        return '', 204
    print("\n========================")
    print("NEW EXTRACTION REQUEST")
    print("========================")
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    pdf = request.files["file"]
    print("Uploaded file:", pdf.filename)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.save(tmp.name)
            print("Saved temp PDF:", tmp.name)
            task_dir = process_pdf(tmp.name)
            print("Extraction complete, task dir:", task_dir)
        return jsonify({"success": True, "task_dir": task_dir})
    except Exception as e:
        print("EXTRACTION ERROR:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9700, debug=True)
