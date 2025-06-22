from enum import Enum
from typing import Optional
from text_to_speech_google import GoogleTTS
from text_to_speech_eleven import ElevenLabsTTS
from text_to_speech_hume import HumeTTS

class TTSProvider(Enum):
    GOOGLE = "google"
    ELEVEN_LABS = "eleven_labs"
    HUME = "hume"

class TTSFactory:
    """Factory class to create and manage different TTS providers"""
    
    @staticmethod
    def create_tts(provider: TTSProvider):
        """
        Create a TTS instance based on the specified provider
        
        Args:
            provider (TTSProvider): The TTS provider to use
            
        Returns:
            A TTS instance that implements text_to_speech method
        
        Raises:
            ValueError: If the provider is not supported
        """
        if provider == TTSProvider.GOOGLE:
            return GoogleTTS()
        elif provider == TTSProvider.ELEVEN_LABS:
            return ElevenLabsTTS()
        elif provider == TTSProvider.HUME:
            return HumeTTS()
        else:
            raise ValueError(f"Unsupported TTS provider: {provider}")

    @staticmethod
    def text_to_speech(
        text: str,
        provider: TTSProvider,
        output_dir: str = "audio_outputs",
        filename: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using the specified provider
        
        Args:
            text (str): The text to convert to speech
            provider (TTSProvider): The TTS provider to use
            output_dir (str): Directory to store the audio output
            filename (str, optional): Optional filename for the output file
            
        Returns:
            str: Path to the generated audio file
            
        Raises:
            ValueError: If the provider is not supported or if text is empty
        """
        if not text:
            raise ValueError("Text is empty")
            
        tts = TTSFactory.create_tts(provider)
        return tts.text_to_speech(text, output_dir, filename)

def get_recommended_provider(text: str) -> TTSProvider:
    """
    Get recommended TTS provider based on text characteristics
    
    Args:
        text (str): The input text
        
    Returns:
        TTSProvider: Recommended TTS provider
    """
    text_lower = text.lower()
    
    # Check text length
    if len(text) > 5000:
        return TTSProvider.GOOGLE  # Google handles long texts well
        
    # Check for technical content
    technical_keywords = ['feel', 'emotion', 'story', 'experience', 'journey', 'icecream', 'tom', 'jerry', 'code', 'function', 'algorithm', 'technical', 'documentation']
    if any(keyword in text_lower for keyword in technical_keywords):
        return TTSProvider.HUME  # Hume handles technical content well
        
    # Check for emotional/narrative content
    emotional_keywords = ['feel', 'emotion', 'story', 'experience', 'journey']
    if any(keyword in text_lower for keyword in emotional_keywords):
        return TTSProvider.ELEVEN_LABS  # Eleven Labs is good for emotional content
        
    # Default to Hume as it has good general-purpose quality
    return TTSProvider.HUME

# Example usage
if __name__ == "__main__":
    example_text = "This is a test of the text-to-speech system."
    
    # Use automatic provider selection
    recommended_provider = get_recommended_provider(example_text)
    print(f"Recommended provider: {recommended_provider.value}")
    
    try:
        # Convert text using recommended provider
        output_file = TTSFactory.text_to_speech(
            text=example_text,
            provider=recommended_provider
        )
        print(f"Audio generated successfully: {output_file}")
        
        # Or specify a provider manually
        output_file = TTSFactory.text_to_speech(
            text=example_text,
            provider=TTSProvider.HUME,
            filename="manual_provider_test.mp3"
        )
        print(f"Audio generated successfully: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}") 