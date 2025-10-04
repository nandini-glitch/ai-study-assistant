# 📚 AI Study Assistant

A multimodal web application using **Google Gemini 2.5 Flash** that helps students study by processing **text, images, and audio** to answer questions intelligently.

---

## ✨ Features

* 📄 Upload **PDF/TXT documents**
* 🖼 Analyze **images and diagrams**
* 🎤 Ask **voice questions** (native Gemini audio)
* 💬 **AI-powered Q&A**
* 🔊 **Text-to-speech** responses
* 📝 Generate **study summaries**

---

## 🛠 Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python (Flask)
* **AI:** Google Gemini 2.5 Flash (multimodal: text, images, audio)

---

## 📁 Project Structure

```bash
ai-study-assistant/
│── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env
│   ├── uploads/
│   └── utils/
│       ├── __init__.py
│       ├── document_processor.py
│       ├── image_analyzer.py
│       └── voice_handler.py
│
│── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
└── README.md
```

---

## 🚀 Setup Instructions

### Step 1: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy your key

---

### Step 2: Create Project

```bash
mkdir ai-study-assistant
cd ai-study-assistant
```

---

### Step 3: Setup Virtual Environment

```bash
# Create venv
python -m venv venv
```

Activate environment:

* **Windows**

```bash
venv\Scripts\activate
```

* **Mac/Linux**

```bash
source venv/bin/activate
```

---

### Step 4: Install Dependencies

```bash
cd backend
pip install flask flask-cors google-generativeai python-dotenv PyPDF2 Pillow gtts
pip freeze > requirements.txt
cd ..
```

---

### Step 5: Add API Key

Create a file `backend/.env` and add:

```bash
GEMINI_API_KEY=your_api_key_here
```

---

## 🔗 Cloning Instructions

```bash
git clone https://github.com/nandini-glitch/ai-study-assistant.git
cd ai-study-assistant
```

---

## ✅ Get to Working! 🚀

Run the backend and open the frontend in your browser to start using **AI Study Assistant**.
