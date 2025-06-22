import os
from pathlib import Path
from typing import Optional
import uuid
from elevenlabs import generate, save, set_api_key
import requests

class ElevenLabsTTS:
    """Eleven Labs Text-to-Speech implementation"""
    
    def __init__(self):
        # Load API key from environment
        api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not api_key:
            raise ValueError("Please set ELEVEN_LABS_API_KEY environment variable")
        set_api_key(api_key)
        self.api_key = api_key
    
    def text_to_speech(self, text: str, output_dir: str = "audio_outputs", filename: Optional[str] = None) -> str:
        """
        Convert text from a file to speech using ElevenLabs Text to Speech API
        
        Args:
            input_file_path (str): Path to the input text file
            output_dir (str): Directory to store the audio output
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # ElevenLabs Text to Speech API endpoint
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Default voice ID
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        # Make the API request
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        # Create output filename
        if filename is None:
            filename = f"{uuid.uuid4()}_audio.mp3"
        output_file = output_path / filename
        
        # Save the audio file
        with open(str(output_file), 'wb') as f:
            f.write(response.content)
        
        return str(output_file)
    # def text_to_speech(self, text: str, output_dir: str = "audio_outputs", filename: Optional[str] = None) -> str:
    #     """
    #     Convert text to speech using Eleven Labs Text-to-Speech
        
    #     Args:
    #         text (str): The text to convert to speech
    #         output_dir (str): Directory to store the audio output
    #         filename (str, optional): Optional filename for the output file
            
    #     Returns:
    #         str: Path to the generated audio file
    #     """
    #     if not text:
    #         raise ValueError("Text is empty")

    #     # Create output directory if it doesn't exist
    #     output_path = Path(output_dir)
    #     output_path.mkdir(exist_ok=True)
        
    #     # Create output filename
    #     if filename is None:
    #         filename = f"{uuid.uuid4()}_audio.mp3"
    #     output_file = output_path / filename
        
    #     # Generate audio using Eleven Labs
    #     audio = generate(
    #         text=text,
    #         voice="Josh",  # Using a default voice, can be made configurable
    #         model="eleven_monolingual_v1"
    #     )
        
    #     # Save the audio file
    #     save(audio, str(output_file))
        
    #     return str(output_file)

# if __name__ == "__main__":
#     # Example usage
#     input_file = "/Users/jianyuhou/Downloads/video_description.txt"
#     try:
#         output_file = text_to_speech(input_file)
#         print(f"Audio file generated successfully: {output_file}")
#     except Exception as e:
#         print(f"Error: {str(e)}")
