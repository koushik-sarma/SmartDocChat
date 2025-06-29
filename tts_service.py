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
        Add SSML-like markers to enhance expression.
        Note: OpenAI TTS doesn't support full SSML, but we can optimize text structure.
        """
        # Clean up text formatting
        processed_text = text.replace("**", "").replace("*", "")
        
        # Add natural pauses for better flow
        processed_text = processed_text.replace(". ", "... ")
        processed_text = processed_text.replace("! ", "! ")
        processed_text = processed_text.replace("? ", "? ")
        
        # Handle lists and bullet points
        processed_text = processed_text.replace("• ", "First, ")
        processed_text = processed_text.replace("- ", "Next, ")
        
        # Add enthusiasm for positive content
        if emotion == "enthusiastic":
            processed_text = "Here's what I found! " + processed_text
        elif emotion == "explanatory":
            processed_text = "Let me explain this for you. " + processed_text
        
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