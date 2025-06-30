import logging
import os
from typing import Optional
import tempfile
from openai import OpenAI

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        """Initialize TTS service with OpenAI."""
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.openai_api_key)
        
        self.available_voices = [
            "alloy",    # Neutral, balanced
            "echo",     # Male, clear
            "fable",    # British accent
            "onyx",     # Deep male
            "nova",     # Female, warm
            "shimmer"   # Female, bright
        ]
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """
        Convert text to speech using OpenAI TTS.
        Returns audio data as bytes.
        """
        try:
            if voice not in self.available_voices:
                logger.warning(f"Voice '{voice}' not available, using 'alloy'")
                voice = "alloy"
            
            # Generate speech using OpenAI TTS
            response = self.client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {e}")
            raise
    
    def get_available_voices(self) -> list:
        """Get list of available voices with descriptions."""
        return [
            {"id": "alloy", "name": "Alloy", "description": "Neutral, balanced tone"},
            {"id": "echo", "name": "Echo", "description": "Male, clear voice"},
            {"id": "fable", "name": "Fable", "description": "British accent"},
            {"id": "onyx", "name": "Onyx", "description": "Deep male voice"},
            {"id": "nova", "name": "Nova", "description": "Female, warm tone"},
            {"id": "shimmer", "name": "Shimmer", "description": "Female, bright tone"}
        ]
    
    def save_audio_to_file(self, audio_data: bytes, filename: Optional[str] = None) -> str:
        """
        Save audio data to a temporary file.
        Returns the file path.
        """
        try:
            if not filename:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp3',
                    prefix='tts_audio_'
                )
                filename = temp_file.name
                temp_file.close()
            
            # Write audio data to file
            with open(filename, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            raise
    
    def create_expressive_speech(self, text: str, voice: str = "nova", 
                               emotion: str = "neutral") -> bytes:
        """
        Create expressive speech by preprocessing text for better expression.
        """
        try:
            # Add expression markers based on content
            processed_text = self._add_expression_markers(text, emotion)
            
            # Generate speech with processed text
            audio_data = self.text_to_speech(processed_text, voice)
            return audio_data
            
        except Exception as e:
            logger.error(f"Error creating expressive speech: {e}")
            raise
    
    def _add_expression_markers(self, text: str, emotion: str = "neutral") -> str:
        """
        Add expression markers optimized for Indian English and Telugu-speaking teens.
        Makes speech clearer and more culturally appropriate.
        """
        # Clean up text formatting
        processed_text = text.replace("**", "").replace("*", "")
        
        # Replace complex words with simpler Indian English alternatives
        word_replacements = {
            "utilize": "use",
            "demonstrate": "show",
            "subsequently": "then",
            "furthermore": "also",
            "therefore": "so",
            "however": "but",
            "nevertheless": "still",
            "approximately": "about",
            "specifically": "clearly",
            "particularly": "especially"
        }
        
        for complex_word, simple_word in word_replacements.items():
            processed_text = processed_text.replace(complex_word, simple_word)
            processed_text = processed_text.replace(complex_word.capitalize(), simple_word.capitalize())
        
        # Add natural pauses for better comprehension
        processed_text = processed_text.replace(". ", ". ")
        processed_text = processed_text.replace("! ", "! ")
        processed_text = processed_text.replace("? ", "? ")
        processed_text = processed_text.replace(", ", ", ")
        
        # Handle lists with clear enumeration
        processed_text = processed_text.replace("• ", "First point, ")
        processed_text = processed_text.replace("- ", "Next point, ")
        
        # Add friendly introductions suitable for Indian students
        if emotion == "enthusiastic":
            processed_text = "Great question! " + processed_text
        elif emotion == "explanatory":
            processed_text = "Let me help you understand this clearly. " + processed_text
        
        # Add familiar expressions for better connection with Telugu students
        familiar_replacements = {
            "Let me explain": "Let me tell you",
            "As you can see": "You can see that",
            "It is important to note": "Remember that",
            "In conclusion": "So, to sum up",
            "For example": "For instance",
            "In other words": "That means"
        }
        
        for formal_phrase, familiar_phrase in familiar_replacements.items():
            processed_text = processed_text.replace(formal_phrase, familiar_phrase)
        
        # Add pronunciation helpers for technical terms
        tech_pronunciations = {
            "PDF": "P D F",
            "API": "A P I",
            "URL": "U R L",
            "HTTP": "H T T P",
            "HTML": "H T M L",
            "CSS": "C S S"
        }
        
        for term, pronunciation in tech_pronunciations.items():
            processed_text = processed_text.replace(term, pronunciation)
        
        # Add educational context markers for better learning
        educational_keywords = ['learn', 'study', 'understand', 'remember', 'important', 'concept', 'definition']
        if any(word in processed_text.lower() for word in educational_keywords):
            processed_text = "Pay attention. " + processed_text
        
        # Slow down technical explanations for better comprehension
        if any(word in processed_text.lower() for word in ['algorithm', 'database', 'programming', 'technology']):
            processed_text = "Now, let me explain this step by step. " + processed_text
        
        # Add encouraging phrases for Telugu students
        if len(processed_text) > 200:  # For longer explanations
            processed_text = processed_text + " I hope this helps you understand better."
        
        return processed_text

# Simple synchronous wrapper for Flask usage
class SimpleTTSWrapper:
    def __init__(self):
        self.tts_service = TTSService()
    
    def text_to_speech_sync(self, text: str, voice: str = "alloy") -> bytes:
        """Synchronous TTS conversion."""
        return self.tts_service.text_to_speech(text, voice)
    
    def create_expressive_speech_sync(self, text: str, voice: str = "nova", 
                                    emotion: str = "neutral") -> bytes:
        """Synchronous expressive TTS."""
        return self.tts_service.create_expressive_speech(text, voice, emotion)
    
    def get_available_voices(self) -> list:
        """Get available voices."""
        return self.tts_service.get_available_voices()
    
    def save_audio_to_file(self, audio_data: bytes, filename: Optional[str] = None) -> str:
        """Save audio to file."""
        return self.tts_service.save_audio_to_file(audio_data, filename)