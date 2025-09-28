from flask import Flask, request, jsonify
import os
import threading
from analysis import analyze_video
import subprocess

# ----------------------------
# Flask backend
# ----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Dance Analysis Server is running!"})

@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400
    
    video_file = request.files["video"]
    os.makedirs("Dataset", exist_ok=True)
    video_path = os.path.join("Dataset", video_file.filename)
    video_file.save(video_path)
    
    results = analyze_video(video_path)
    return jsonify({"message": f"{video_file.filename} uploaded successfully!", "results": results})

def run_flask():
    # Bind to 0.0.0.0 internally
    app.run(host="0.0.0.0", port=5000, debug=False)

# ----------------------------
# Streamlit frontend
# ----------------------------
def run_streamlit():
    subprocess.run([
        "streamlit", "run", "frontend.py",
        "--server.address=0.0.0.0",
        "--server.port=8501",
        "--server.headless=true"
    ])

if __name__ == "__main__":
    # Flask backend in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run Streamlit (blocking)
    run_streamlit()
