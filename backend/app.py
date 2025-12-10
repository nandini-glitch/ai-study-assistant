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
from utils.rag_handler import RAGSystem

load_dotenv()

app = Flask(__name__)

# CORS Configuration - Allow all origins for now (restrict in production)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

gemini_api_key = os.getenv('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    print("WARNING: GEMINI_API_KEY not found!")

study_materials = {
    'text_content': "",
    'image_analyses': [],
    'images': [],
    'uploaded_files': []
}
# Initialize RAG System
try:
    rag_system = RAGSystem()
    print("✓ RAG system initialized successfully")
except Exception as e:
    print(f"✗ Error initializing RAG: {e}")
    rag_system = None

@app.route('/')
def home():
    return jsonify({
        "message": "AI Study Assistant (Gemini 2.5 Flash)",
        "status": "active",
        "version": "1.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

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
        
        # Store in memory (for backward compatibility)
        study_materials['text_content'] += f"\n\n--- {file.filename} ---\n{text}"
        study_materials['uploaded_files'].append({
            'filename': file.filename,
            'filepath': filepath,
            'type': 'document'
        })
        
        # ADD TO RAG SYSTEM
        chunks_created = 0
        if rag_system:
            chunks_created = rag_system.add_document(text, file.filename)
        
        return jsonify({
            "success": True,
            "message": f"✓ '{file.filename}' uploaded and indexed!",
            "filename": file.filename,
            "text_length": len(text),
            "chunks_created": chunks_created,
            "rag_enabled": rag_system is not None
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
    use_rag = data.get('use_rag', True)  # Enable RAG by default
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    context = "You are a helpful AI study assistant.\n\n"
    sources = []
    
    # Use RAG if available and enabled
    if rag_system and use_rag:
        try:
            # Search for relevant chunks
            search_results = rag_system.search(question, n_results=5)
            
            if search_results['documents']:
                context += "=== RELEVANT STUDY MATERIALS (RAG) ===\n\n"
                
                for i, (doc, meta, dist) in enumerate(zip(
                    search_results['documents'],
                    search_results['metadatas'],
                    search_results.get('distances', [0]*len(search_results['documents']))
                )):
                    context += f"[Chunk {i+1} from {meta['filename']}]\n{doc}\n\n"
                    if meta['filename'] not in sources:
                        sources.append(meta['filename'])
            else:
                # Fallback to traditional method
                context += "=== STUDY MATERIALS (No RAG results) ===\n\n"
                if study_materials['text_content']:
                    context += "TEXT NOTES:\n" + study_materials['text_content'] + "\n\n"
        
        except Exception as e:
            print(f"RAG search error: {e}")
            # Fallback to traditional method
            if study_materials['text_content']:
                context += "TEXT NOTES:\n" + study_materials['text_content'] + "\n\n"
    else:
        # Traditional method (no RAG)
        context += "=== STUDY MATERIALS ===\n\n"
        if study_materials['text_content']:
            context += "TEXT NOTES:\n" + study_materials['text_content'] + "\n\n"
    
    # Add image analyses
    if study_materials['image_analyses']:
        context += "IMAGE ANALYSES:\n"
        for img in study_materials['image_analyses']:
            context += f"{img['filename']}: {img['analysis']}\n\n"
    
    if not study_materials['text_content'] and not study_materials['image_analyses']:
        context = "No study materials uploaded. Answer based on general knowledge if appropriate."
    
    context += f"\n=== QUESTION ===\n{question}\n\nProvide a clear, educational answer based on the materials above."
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(context)
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": response.text,
            "sources": sources,
            "rag_used": rag_system is not None and use_rag
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
    
    # Clear RAG system
    if rag_system:
        try:
            rag_system.clear_all()
        except Exception as e:
            print(f"Error clearing RAG: {e}")
    
    return jsonify({
        "success": True,
        "message": "All materials cleared (including RAG index)"
    })

#for rag status
@app.route('/rag/stats', methods=['GET'])
def get_rag_stats():
    """Get RAG system statistics"""
    if not rag_system:
        return jsonify({"error": "RAG system not initialized"}), 503
    
    try:
        stats = rag_system.get_stats()
        return jsonify({
            "success": True,
            "stats": stats,
            "rag_available": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PRODUCTION CONFIGURATION
if __name__ == '__main__':
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get('PORT', 5001))
    # debug=False for production
    app.run(debug=False, port=port, host='0.0.0.0')
