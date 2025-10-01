import speech_recognition as sr
from gtts import gTTS
import os

def transcribe_audio(audio_path: str) -> str:
    """Convert speech to text using Google Speech Recognition"""
    try:
        recognizer = sr.Recognizer()
        
        # Load audio file
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            
        # Recognize speech
        text = recognizer.recognize_google(audio_data)
        return text
    
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Error with speech recognition service: {e}"
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return f"Error: {str(e)}"

def text_to_speech(text: str, output_path: str) -> bool:
    """Convert text to speech using Google TTS"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"Error generating speech: {e}")
        return False