import os
import re
import joblib
import datetime
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename

# ========== CONFIGURATION ==========
app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ========== MONGODB CONNECTION ==========
MONGO_URI = "mongodb://localhost:27017/"
try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client["ransomware_db"]
    logs = mongo_db["scan_logs"]
    mongo_ok = True
    print("✅ Connected to MongoDB successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    mongo_ok = False

# ========== MODEL LOAD ==========
try:
    model = joblib.load("model.pkl")
    label_encoder = joblib.load("encoders.pkl")
    print("✅ Model & encoders loaded successfully")
except Exception as e:
    print("❌ Model loading failed:", e)
    model = None

# ========== FEATURE EXTRACTION ==========
def calc_entropy(data):
    if not data:
        return 0
    freq = np.bincount(np.frombuffer(data, dtype=np.uint8))
    freq = freq[freq > 0] / len(data)
    return -np.sum(freq * np.log2(freq))

def extract_features(file_path):
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        features = {
            "file_size": os.path.getsize(file_path),
            "entropy": calc_entropy(content),
            "num_strings": len(re.findall(rb"[ -~]{4,}", content)),
            "non_ascii_ratio": sum(c > 127 for c in content) / len(content) if len(content) > 0 else 0,
            "printable_ratio": len(re.findall(rb"[ -~]", content)) / len(content) if len(content) > 0 else 0,
            "is_pe": int(content[:2] == b"MZ"),
            "extension": hash(os.path.splitext(file_path)[1]) % 10,
        }

        return features
    except Exception as e:
        print("⚠️ Feature extraction failed:", e)
        return None

# ========== HELPERS ==========
def sanitize_for_mongo(data):
    """Convert numpy types to plain Python types."""
    if isinstance(data, dict):
        return {k: sanitize_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_mongo(v) for v in data]
    elif isinstance(data, (np.int64, np.int32)):
        return int(data)
    elif isinstance(data, (np.float64, np.float32)):
        return float(data)
    elif isinstance(data, (np.bool_)):
        return bool(data)
    else:
        return data

# ========== ROUTES ==========
@app.route("/")
def index():
    """Serve the frontend index page."""
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    """Serve other static frontend files."""
    return send_from_directory(app.static_folder, path)

@app.route("/api/scan_file", methods=["POST"])
def scan_file():
    """Scan an uploaded file for ransomware-like characteristics."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    features = extract_features(file_path)
    if not features or model is None:
        return jsonify({"error": "Feature extraction or model loading failed"}), 500

    # ✅ Only use the 5 features your model was trained on
    X = np.array([[features["file_size"],
                   features["entropy"],
                   features["num_strings"],
                   features["non_ascii_ratio"],
                   features["is_pe"]]])

    # Predict
    pred = int(model.predict(X)[0])
    result_text = "🚨 Ransomware Detected!" if pred == 1 else "✅ File is Safe."

    # Sanitize and save entry to MongoDB
    entry = {
        "filename": filename,
        "features": sanitize_for_mongo(features),
        "prediction": pred,
        "result": result_text,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    if mongo_ok:
        try:
             result = logs.insert_one(entry)
             entry["_id"] = str(result.inserted_id)  # ✅ convert ObjectId to string
        except Exception as e:
            print(f"⚠️ MongoDB insert failed: {e}")
            entry["_id"] = None

    print(f"🧩 Scanned: {filename} → {result_text}")
    return jsonify(entry)

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Retrieve all scan logs."""
    if not mongo_ok:
        return jsonify([])
    all_logs = list(logs.find({}, {"_id": 0}))
    return jsonify(all_logs)

# ========== MAIN ==========
if __name__ == "__main__":
    app.run(debug=True)
