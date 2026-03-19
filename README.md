# 🤖 DeepFake AI Studio

An AI-powered Face Swap web application built with
Python, Flask and OpenCV featuring a Neonic Day/Night UI.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 🖼️ **Image Face Swap** — Swap faces between two images
- 🎥 **Video Face Swap** — Swap faces frame by frame in videos
- 🔍 **Face Detection** — Detect and locate faces with bounding boxes
- 🌙 **Day / Night Theme** — Toggle between dark neonic and light mode
- 🎨 **Drag and Drop Upload** — Easy file uploading
- ⚡ **Real-time Progress Bar** — Live processing status
- 📱 **Responsive UI** — Works on mobile and desktop

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10, Flask 3.0 |
| Frontend | HTML5, CSS3, JavaScript |
| AI Engine | OpenCV, Poisson Seamless Cloning |
| Face Detection | Haar Cascade Classifier |
| Styling | Neonic CSS, Orbitron Font |
| API | Flask REST API |

---

## 📁 Project Structure
```
deepfake-ai/
├── app.py                 ← Flask server + REST API
├── deepfake_engine.py     ← AI core engine
├── requirements.txt       ← Python dependencies
├── templates/
│   └── index.html         ← Main UI page
└── static/
    ├── css/
    │   └── style.css      ← Neonic theme styles
    └── js/
        └── app.js         ← Frontend logic
```

---

## 🚀 How to Run Locally

### Step 1 — Clone the repository
```bash
git clone https://github.com/Debasish-Nayak-556/deepfake-ai.git
cd deepfake-ai
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the server
```bash
python app.py
```

### Step 5 — Open in browser
```
http://localhost:5000
```

---

## 📸 How to Use

### Image Face Swap
```
1. Click "Image Swap" tab
2. Upload SOURCE face photo (face donor)
3. Upload TARGET photo (face recipient)
4. Adjust Blend Strength slider
5. Toggle Enhance ON/OFF
6. Click ⚡ EXECUTE SWAP
7. Download result ⬇
```

### Video Face Swap
```
1. Click "Video Swap" tab
2. Upload SOURCE face photo
3. Upload TARGET video (MP4/AVI/MOV)
4. Set Frame Skip and Max Frames
5. Click ⚡ PROCESS VIDEO
6. Download result ⬇
```

### Face Detection
```
1. Click "Detect" tab
2. Upload any photo
3. Click ◎ SCAN FOR FACES
4. View face count and bounding boxes
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/health | Server health check |
| POST | /api/swap/image | Image face swap |
| POST | /api/swap/video | Video face swap |
| POST | /api/detect | Face detection |

---

## ⚙️ Requirements
```
Python 3.10+
flask
flask-cors
opencv-python
numpy
Pillow
onnxruntime
werkzeug
requests
tqdm
```

---

## 🖥️ Screenshots

> Dark Neonic Theme with Image Swap Interface

---

## ⚠️ Disclaimer
```
This project is for EDUCATIONAL PURPOSES ONLY.
Do not use this software to create misleading
or harmful content. Always get consent before
using someone's likeness.
```

---

## 👨‍💻 Author

Made with ❤️ by **Debasish Nayak**

[![GitHub](https://img.shields.io/badge/GitHub-Debasish-Nayak-556-black)](https://github.com/Debasish-Nayak-556)

---

## ⭐ Support

If you found this project helpful please give it a ⭐ Star on GitHub!
```

---

## ✅ STEP 3 — Save as README.md
```
1. Click File → Save As
2. Navigate to → D:\Deepfake -AI
3. Change "Save as type" → All Files (*.*)
4. File name → type exactly:  README.md
5. Click Save
