import pyttsx3
import threading
import logging
from typing import Optional
import os
import tempfile
from gtts import gTTS
import pygame
import io

class TTSService:
    """
    Text-to-Speech service that can use both pyttsx3 (offline) and gTTS (online)
    """
    
    def __init__(self, engine_type: str = 'pyttsx3', language: str = 'en'):
        self.engine_type = engine_type
        self.language = language
        self.is_speaking = False
        
        if engine_type == 'pyttsx3':
            self._init_pyttsx3()
        elif engine_type == 'gtts':
            self._init_gtts()
        else:
            raise ValueError("Engine type must be 'pyttsx3' or 'gtts'")
        
        logging.info(f"TTS Service initialized with {engine_type} engine")
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine (offline TTS)"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to set a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use the first available voice
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
            
        except Exception as e:
            logging.error(f"Failed to initialize pyttsx3: {e}")
            raise
    
    def _init_gtts(self):
        """Initialize gTTS (Google Text-to-Speech - requires internet)"""
        try:
            pygame.mixer.init()
            self.engine = None  # gTTS doesn't need persistent engine
        except Exception as e:
            logging.error(f"Failed to initialize pygame for gTTS: {e}")
            raise
    
    def speak(self, text: str, async_mode: bool = True) -> bool:
        """
        Convert text to speech
        
        Args:
            text: Text to convert to speech
            async_mode: If True, speak in background thread
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not text or text.strip() == "":
            return False
        
        if self.is_speaking:
            logging.info("TTS is already speaking, skipping...")
            return False
        
        try:
            if async_mode:
                threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()
                return True
            else:
                return self._speak_sync(text)
        except Exception as e:
            logging.error(f"Error in speak method: {e}")
            return False
    
    def _speak_sync(self, text: str) -> bool:
        """Synchronous speech method"""
        self.is_speaking = True
        
        try:
            if self.engine_type == 'pyttsx3':
                return self._speak_pyttsx3(text)
            elif self.engine_type == 'gtts':
                return self._speak_gtts(text)
        except Exception as e:
            logging.error(f"Error during speech synthesis: {e}")
            return False
        finally:
            self.is_speaking = False
    
    def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3 engine"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logging.error(f"pyttsx3 speech error: {e}")
            return False
    
    def _speak_gtts(self, text: str) -> bool:
        """Speak using Google Text-to-Speech"""
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=self.language, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                # Play the audio file
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                # Clean up
                os.unlink(tmp_file.name)
                
            return True
        except Exception as e:
            logging.error(f"gTTS speech error: {e}")
            return False
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            if self.engine_type == 'pyttsx3' and hasattr(self, 'engine'):
                self.engine.stop()
            elif self.engine_type == 'gtts':
                pygame.mixer.music.stop()
            
            self.is_speaking = False
        except Exception as e:
            logging.error(f"Error stopping speech: {e}")
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute) - only works with pyttsx3"""
        if self.engine_type == 'pyttsx3' and hasattr(self, 'engine'):
            try:
                self.engine.setProperty('rate', rate)
            except Exception as e:
                logging.error(f"Error setting speech rate: {e}")
    
    def set_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0) - only works with pyttsx3"""
        if self.engine_type == 'pyttsx3' and hasattr(self, 'engine'):
            try:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            except Exception as e:
                logging.error(f"Error setting speech volume: {e}")
    
    def get_voices(self) -> list:
        """Get available voices - only works with pyttsx3"""
        if self.engine_type == 'pyttsx3' and hasattr(self, 'engine'):
            try:
                voices = self.engine.getProperty('voices')
                return [{'id': voice.id, 'name': voice.name} for voice in voices]
            except Exception as e:
                logging.error(f"Error getting voices: {e}")
                return []
        return []
    
    def set_voice(self, voice_id: str):
        """Set voice by ID - only works with pyttsx3"""
        if self.engine_type == 'pyttsx3' and hasattr(self, 'engine'):
            try:
                self.engine.setProperty('voice', voice_id)
            except Exception as e:
                logging.error(f"Error setting voice: {e}")


class GestureToSpeechManager:
    """
    Manages the conversion from recognized gestures to speech
    """
    
    def __init__(self, tts_service: TTSService):
        self.tts_service = tts_service
        self.accumulated_text = ""
        self.last_gesture = ""
        self.gesture_sentences = {
            'Hello': "Hello there!",
            'Thank you': "Thank you very much!",
            'Please': "Please help me.",
            'Sorry': "I'm sorry.",
            'Yes': "Yes, that's correct.",
            'No': "No, that's not right."
        }
        
    def add_gesture(self, gesture: str) -> str:
        """
        Add a recognized gesture and return the accumulated text
        
        Args:
            gesture: The recognized gesture
            
        Returns:
            str: The accumulated text
        """
        if not gesture or gesture == self.last_gesture:
            return self.accumulated_text
        
        self.last_gesture = gesture
        
        # Handle special phrases
        if gesture in self.gesture_sentences:
            text_to_add = self.gesture_sentences[gesture]
            self.tts_service.speak(text_to_add)
            self.accumulated_text += text_to_add + " "
        else:
            # Handle individual letters
            self.accumulated_text += gesture + " "
            
            # Speak individual letters immediately
            if len(gesture) == 1:  # Single letter
                self.tts_service.speak(gesture)
        
        return self.accumulated_text.strip()
    
    def speak_accumulated_text(self):
        """Speak all accumulated text"""
        if self.accumulated_text.strip():
            self.tts_service.speak(self.accumulated_text.strip())
    
    def clear_text(self):
        """Clear accumulated text"""
        self.accumulated_text = ""
        self.last_gesture = ""
    
    def get_text(self) -> str:
        """Get current accumulated text"""
        return self.accumulated_text.strip()