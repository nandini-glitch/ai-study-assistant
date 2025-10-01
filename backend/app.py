from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from gtts import gTTS
import tempfile

from utils.document_processor import extract_text_from_pdf, extract_text_from_txt
from utils.image_analyzer import analyze_image

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

gemini_api_key = os.getenv('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

study_materials = {
    'text_content': "",
    'image_analyses': [],
    'images': [],
    'uploaded_files': []
}

@app.route('/')
def home():
    return jsonify({
        "message": "AI Study Assistant (Gemini 2.5 Flash)",
        "status": "active"
    })

@app.route('/upload/document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        elif filename.lower().endswith('.txt'):
            text = extract_text_from_txt(filepath)
        else:
            os.remove(filepath)
            return jsonify({"error": "Use PDF or TXT"}), 400
        
        if not text:
            os.remove(filepath)
            return jsonify({"error": "No text extracted"}), 400
        
        study_materials['text_content'] += f"\n\n--- {file.filename} ---\n{text}"
        study_materials['uploaded_files'].append({
            'filename': file.filename,
            'filepath': filepath,
            'type': 'document'
        })
        
        return jsonify({
            "success": True,
            "message": f"✓ '{file.filename}' uploaded!",
            "filename": file.filename,
            "text_length": len(text)
        })
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500

@app.route('/upload/image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        analysis = analyze_image(filepath)
        
        study_materials['image_analyses'].append({
            'filename': file.filename,
            'analysis': analysis
        })
        study_materials['images'].append(filepath)
        study_materials['uploaded_files'].append({
            'filename': file.filename,
            'filepath': filepath,
            'type': 'image'
        })
        
        return jsonify({
            "success": True,
            "message": f"✓ '{file.filename}' analyzed!",
            "filename": file.filename,
            "analysis": analysis
        })
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500

@app.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Transcribe audio using Gemini 2.5 Flash native audio support"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Upload audio file to Gemini
        audio_file = genai.upload_file(filepath)
        
        # Use Gemini 2.5 Flash for transcription
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([
            "Transcribe this audio exactly as spoken. Only provide the transcription, no additional text.",
            audio_file
        ])
        
        transcription = response.text.strip()
        
        return jsonify({
            "success": True,
            "message": "✓ Audio transcribed!",
            "transcription": transcription,
            "filename": file.filename
        })
    except Exception as e:
        return jsonify({"error": f"Transcription error: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    context = "You are a helpful AI study assistant.\n\n=== STUDY MATERIALS ===\n\n"
    
    if study_materials['text_content']:
        context += "TEXT NOTES:\n" + study_materials['text_content'] + "\n\n"
    
    if study_materials['image_analyses']:
        context += "IMAGE ANALYSES:\n"
        for img in study_materials['image_analyses']:
            context += f"{img['filename']}: {img['analysis']}\n\n"
    
    if not study_materials['text_content'] and not study_materials['image_analyses']:
        context = "No study materials uploaded. Answer based on general knowledge if appropriate."
    
    context += f"\n=== QUESTION ===\n{question}\n\nProvide a clear, educational answer."
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(context)
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/speak', methods=['POST'])
def speak():
    """Convert text to speech"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    temp_file = os.path.join(tempfile.gettempdir(), f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
    
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_file)
        return send_file(temp_file, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/summary', methods=['POST'])
def generate_summary():
    if not study_materials['text_content'] and not study_materials['image_analyses']:
        return jsonify({"error": "No materials uploaded yet"}), 400
    
    content = "Provide a comprehensive summary with key points and takeaways:\n\n"
    
    if study_materials['text_content']:
        content += "=== TEXT ===\n" + study_materials['text_content'] + "\n\n"
    
    if study_materials['image_analyses']:
        content += "=== IMAGES ===\n"
        for img in study_materials['image_analyses']:
            content += f"{img['filename']}: {img['analysis']}\n\n"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(content)
        
        return jsonify({
            "success": True,
            "summary": response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_materials():
    study_materials['text_content'] = ""
    study_materials['image_analyses'] = []
    
    for img_path in study_materials['images']:
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Error removing {img_path}: {e}")
    
    study_materials['images'] = []
    
    for file_info in study_materials['uploaded_files']:
        filepath = file_info['filepath']
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing {filepath}: {e}")
    
    study_materials['uploaded_files'] = []
    
    return jsonify({
        "success": True,
        "message": "All materials cleared"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')