import google.generativeai as genai
import os
from PIL import Image

def configure_gemini():
    """Configure Gemini API"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    genai.configure(api_key=api_key)

def analyze_image(image_path: str, query: str = "") -> str:
    """Analyze image using Gemini 2.5 Flash"""
    try:
        configure_gemini()
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = query if query else """Analyze this diagram/image in detail:
        1. All key information, labels, and text
        2. Main concepts and relationships
        3. Important visual elements
        4. Any data or measurements
        Provide a comprehensive description for students."""
        
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return f"Error: {str(e)}"