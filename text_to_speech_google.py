import os
from pathlib import Path
from gtts import gTTS
from typing import Optional
import uuid

class GoogleTTS:
    """Google Text-to-Speech implementation"""
    
    def text_to_speech(self, text: str, output_dir: str = "audio_outputs", filename: Optional[str] = None) -> str:
        """
        Convert text to speech using Google Text-to-Speech
        
        Args:
            text (str): The text to convert to speech
            output_dir (str): Directory to store the audio output
            filename (str, optional): Optional filename for the output file
            
        Returns:
            str: Path to the generated audio file
        """
        if not text:
            raise ValueError("Text is empty")

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create output filename
        if filename is None:
            filename = f"{uuid.uuid4()}_audio.mp3"
        output_file = output_path / filename
        
        # Generate audio using gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(str(output_file))
        
        return str(output_file)

if __name__ == "__main__":
    # Example usage
    input_file = "/Users/jianyuhou/Downloads/video_description.txt"
    try:
        output_file = text_to_speech(input_file)
        print(f"Audio file generated successfully: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}") 