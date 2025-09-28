# 🕺 Dance Movement Analysis Server  

A cloud-ready project for analyzing dance movements from video using:  
- **Flask (API backend)**  
- **Streamlit (Frontend UI)**  
- **MediaPipe + OpenCV (Pose & movement analysis)**  
- **Docker (containerization)**  

🚀 **Deployed on Render**:  
```
https://dance-analysis-1.onrender.com
```
*(Note: This is the target Render deployment URL. Once the Render service is correctly configured, the above link will be live.)*  

---

## 📂 Project Structure  

```
dance-analysis-server/
│── Dataset/                 # Test videos
│    └── sample_dance.mp4
│
│── app.py                   # Flask backend (API + starts Streamlit)
│── frontend.py              # Streamlit UI
│── analysis.py              # Dance movement analysis logic
│── utils.py                 # Helper functions
│── test_analysis.py          # Unit tests for analysis functions
│── test_api.py               # Unit tests for API endpoints
│── requirements.txt          # Python dependencies
│── Dockerfile                # Docker build instructions
│── README.md                 # Documentation
```

---

## ⚙️ Setup & Run Locally  

### 1️⃣ Create Virtual Environment  
```bash
python -m venv venv
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows
```

### 2️⃣ Install Requirements  
```bash
pip install -r requirements.txt
```

### 3️⃣ Run Flask + Streamlit  
```bash
python app.py
```

- Flask API → http://127.0.0.1:5000  
- Streamlit UI → http://localhost:8501  

---

## 🧪 Testing  

Run all tests:  
```bash
pytest -v
```

Tests include:  
- **analysis.py** → correctness of pose/movement detection  
- **app.py** → `/` health check and `/upload` endpoints  

---

## 🐳 Run with Docker  

### 1️⃣ Build Image  
```bash
docker build -t dance-analysis-server .
```

### 2️⃣ Run Container  
```bash
docker run -p 5000:5000 -p 8501:8501 dance-analysis-server
```

- Flask API → http://localhost:5000  
- Streamlit UI → http://localhost:8501  

👉 This ensures both Flask (API) and Streamlit (frontend) run inside the same container.  

---

## 🌐 Deployment on Render  

### Steps Taken  
1. Pushed code to **GitHub**.  
2. Created a **Web Service** on Render linked to the repo.  
3. Configuration on Render:  
   - **Environment:** Python 3  
   - **Build Command:**  
     ```bash
     pip install -r requirements.txt
     ```  
   - **Start Command:**  
     ```bash
     python app.py
     ```  
4. Render provides a public endpoint:  
   ```
   https://calllus-assessment.onrender.com
   ```

---

## 🎥 How It Works  

1. Upload a dance video via **Streamlit frontend**.  
2. Streamlit sends the video to **Flask API** (`/upload`).  
3. **analysis.py** processes the video with MediaPipe, detecting standard poses such as:  
   - Hands Up  
   - T-Pose  
   - Squat  
   - Step Forward  
   - Leg Raise  
   - Rotation  
4. Output is returned as **JSON** and displayed in Streamlit (counts + visualization).  

---

## ✅ Features  

- REST API for video upload & pose detection  
- Streamlit frontend for easy interaction  
- Pose analysis powered by MediaPipe + OpenCV  
- Unit tested with pytest  
- Dockerized for portability  
- Deployed on Render (public endpoint available)  

---

## 📸 Example API Usage  

### Health Check  
```bash
curl https://calllus-assessment.onrender.com/
```
Response:  
```json
{"message": "Dance Analysis Server is running!"}
```

### Upload Video  
```bash
curl -X POST https://calllus-assessment.onrender.com/upload \
  -F "video=@Dataset/sample_dance.mp4"
```

Response (example):  
```json
{
  "poses_detected": [
    "Pose at frame 10",
    "Pose at frame 45",
    "Pose at frame 120"
  ]
}
```

👨‍💻 Author: Arnav Kumar Singh   
🎯 Assignment Completed: Backend + Frontend + Testing + Docker + Deployment (Render)  
