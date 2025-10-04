# ai-study-assistant
A multimodal web application using Google Gemini 2.5 Flash that helps students study by
processing text, images, and audio to answer questions intelligently.

✨ Features

📄 Upload PDF/TXT documents
🖼 Analyze images and diagrams
🎤 Voice questions (native Gemini audio)
💬 AI-powered Q&A
🔊 Text-to-speech responses
📝 Generate study summaries

🛠 Tech Stack
Frontend: HTML, CSS, JavaScript
Backend: Python (Flask)
AI: Google Gemini 2.5 Flash (multimodal: text, images, audio)

📁 Project Structure
ai-study-assistant/
│
├── backend/
│ ├── app.py
│ ├── requirements.txt
│ ├──.env
│ ├── uploads/
│ └── utils/
│ ├-__init__.py
│ ├── document_processor.py
│ └── image_analyzer.py
| ---voice_handler.py
│
├── frontend/
│ ├── index.html
│ ├── style.css
│ └── script.js
│
└── README.md

🚀 Setup Instructions
Step 1: Get Gemini API Key
1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy your key
   
Step 2: Create Project
mkdir ai-study-assistant
cd ai-study-assistant

Step 3: Virtual Environment
python -m venv venv
# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

Step 4: Install Dependencies
cd backend
pip install flask flask-cors google-generativeai python-dotenv PyPDF2 Pillow gtts
pip freeze > requirements.txt
cd ..

Step 5: Add API Key
Edit backend/.env:
GEMINI_API_KEY=your_api_key_here

##Cloning instructions:

git clone https://github.com/nandini-glitch/ai-study-assistant.git

Get to working!!

