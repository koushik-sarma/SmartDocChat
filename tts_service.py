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
        """Get list of available voices with language options."""
        return [
            {
                "id": "alloy_english", 
                "name": "Alloy (English)", 
                "description": "Balanced and clear American English",
                "voice": "alloy",
                "language": "english"
            },
            {
                "id": "nova_indian", 
                "name": "Nova (Indian English)", 
                "description": "Energetic and bright with Indian accent",
                "voice": "nova",
                "language": "indian_english"
            },
            {
                "id": "shimmer_tenglish", 
                "name": "Shimmer (Tenglish)", 
                "description": "Telugu-English mix, gentle and soothing",
                "voice": "shimmer",
                "language": "tenglish"
            },
            {
                "id": "echo_hindi", 
                "name": "Echo (Hindi-English)", 
                "description": "Warm and friendly Hindi-English mix",
                "voice": "echo",
                "language": "hindi_english"
            },
            {
                "id": "fable_tamil", 
                "name": "Fable (Tamil-English)", 
                "description": "Expressive Tamil-English storytelling",
                "voice": "fable",
                "language": "tamil_english"
            },
            {
                "id": "onyx_formal", 
                "name": "Onyx (Formal English)", 
                "description": "Deep and authoritative formal English",
                "voice": "onyx",
                "language": "formal_english"
            }
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
                               emotion: str = "neutral", language: str = "english") -> bytes:
        """
        Create expressive speech by preprocessing text for better expression.
        """
        try:
            # Add expression markers based on content and language
            processed_text = self._add_expression_markers(text, emotion, language)
            
            # Generate speech with processed text
            audio_data = self.text_to_speech(processed_text, voice)
            return audio_data
            
        except Exception as e:
            logger.error(f"Error creating expressive speech: {e}")
            raise
    
    def _add_expression_markers(self, text: str, emotion: str = "neutral", language: str = "english") -> str:
        """
        Add expression markers optimized for Indian English and Telugu-speaking teens.
        Makes speech clearer and more culturally appropriate.
        """
        # Clean up text formatting
        processed_text = text.replace("**", "").replace("*", "")
        
        # Language-specific processing
        if language == "tenglish":
            # Telugu-English mixed replacements
            word_replacements = {
                "good": "baagundu",
                "yes": "avunu", 
                "no": "ledu",
                "understand": "ardham ayindi",
                "learn": "nerchukondi",
                "study": "chaduvukondi",
                "great": "chala baagundu",
                "nice": "manchidi",
                "API": "A-P-I api",
                "PDF": "P-D-F file",
                "database": "data-base lo",
                "function": "function chesthe"
            }
            # Add Telugu-style encouraging phrases
            if emotion == "enthusiastic":
                processed_text = f"Waah! {processed_text} Chala baagundu!"
                
        elif language == "indian_english":
            # Indian English specific replacements
            word_replacements = {
                "utilize": "use",
                "demonstrate": "show", 
                "subsequently": "then",
                "furthermore": "also",
                "therefore": "so",
                "however": "but",
                "awesome": "fantastic",
                "cool": "nice",
                "API": "A-P-I",
                "PDF": "P-D-F document",
                "algorithm": "algo-rhythm",
                "schedule": "shed-yule"
            }
            if emotion == "enthusiastic":
                processed_text = f"Very good! {processed_text} Keep it up!"
                
        else:
            # Standard English replacements
            word_replacements = {
                "utilize": "use",
                "demonstrate": "show",
                "subsequently": "then", 
                "furthermore": "also",
                "therefore": "so",
                "however": "but",
                "nevertheless": "still",
                "approximately": "about",
                "API": "A-P-I",
                "PDF": "P-D-F",
                "URL": "U-R-L",
                "SQL": "S-Q-L"
            }
            if emotion == "enthusiastic":
                processed_text = "Great question! " + processed_text
        
        # Apply word replacements
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
        
        return processed_text

# Simple synchronous wrapper for Flask usage
class SimpleTTSWrapper:
    def __init__(self):
        self.tts_service = TTSService()
    
    def text_to_speech_sync(self, text: str, voice: str = "alloy") -> bytes:
        """Synchronous TTS conversion."""
        return self.tts_service.text_to_speech(text, voice)
    
    def create_expressive_speech_sync(self, text: str, voice: str = "nova", 
                                    emotion: str = "neutral", language: str = "english") -> bytes:
        """Synchronous expressive TTS with language support."""
        return self.tts_service.create_expressive_speech(text, voice, emotion, language)
    
    def get_available_voices(self) -> list:
        """Get available voices."""
        return self.tts_service.get_available_voices()
    
    def save_audio_to_file(self, audio_data: bytes, filename: Optional[str] = None) -> str:
        """Save audio to file."""
        return self.tts_service.save_audio_to_file(audio_data, filename)