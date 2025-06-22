from pydub import AudioSegment
import os
from pathlib import Path
import random
import re
from typing import Optional

FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
FFPROBE_PATH = "/opt/homebrew/bin/ffprobe" 
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffmpeg = FFMPEG_PATH
# AudioSegment.ffprobe = FFPROBE_PATH

os.environ['FFMPEG_BINARY'] = FFMPEG_PATH
os.environ['FFPROBE_BINARY'] = FFPROBE_PATH

class AudioProcessor:
    def __init__(self, music_dir: str = "background_music"):
        """Initialize the AudioProcessor with a directory for background music."""
        self.music_dir = Path(music_dir)
        self.music_dir.mkdir(exist_ok=True)
        print(f"Using ffmpeg at: {AudioSegment.converter}")
        # print(f"Using ffprobe at: {AudioSegment.ffprobe}")
        print(f"Environment FFMPEG_BINARY: {os.environ.get('FFMPEG_BINARY')}")
        print(f"Environment FFPROBE_BINARY: {os.environ.get('FFPROBE_BINARY')}")
        
        # Create subdirectories if they don't exist
        self.categories = ['chase', 'comedy', 'dramatic']
        for category in self.categories:
            (self.music_dir / category).mkdir(exist_ok=True)
            
    def _select_music_by_content(self, text: str) -> Optional[str]:
        """
        Select appropriate background music based on text content.
        
        Args:
            text: The narration text to analyze
            
        Returns:
            Path to selected music file or None if no music available
        """
        # Keywords for each category
        keywords = {
            'chase': ['chase', 'run', 'escape', 'catch', 'follow', 'rush', 'speed'],
            'comedy': ['funny', 'laugh', 'silly', 'joke', 'prank', 'amusing', 'ridiculous'],
            'dramatic': ['dramatic', 'serious', 'intense', 'emotional', 'suspense', 'mystery']
        }
        
        # Count keyword matches for each category
        scores = {category: 0 for category in self.categories}
        text_lower = text.lower()
        
        for category, words in keywords.items():
            for word in words:
                scores[category] += len(re.findall(r'\b' + word + r'\b', text_lower))
                
        # Select category with highest score, default to comedy if no matches
        selected_category = max(scores.items(), key=lambda x: x[1])[0] if any(scores.values()) else 'comedy'
        
        # Get available music files for the category
        music_files = list((self.music_dir / selected_category).glob("*.mp3"))
        if not music_files:
            # Fallback to any available music if selected category is empty
            music_files = []
            for category in self.categories:
                music_files.extend((self.music_dir / category).glob("*.mp3"))
                
        if not music_files:
            return None  # No music files available
            
        return str(random.choice(music_files))
        
    def mix_audio(self, narration_path: str, narration_text: str = "", output_path: Optional[str] = None, music_volume: float = -20) -> str:
        """
        Mix narration with background music.
        
        Args:
            narration_path: Path to the narration audio file
            narration_text: Text content of the narration for mood analysis
            output_path: Path for the output mixed audio file (optional)
            music_volume: Volume of background music in dB (default: -20)
            
        Returns:
            Path to the mixed audio file
        """
        # Load narration
        print(f"Loading narration from: {narration_path}")
        narration = AudioSegment.from_mp3(narration_path)
        
        # Select appropriate background music
        music_path = self._select_music_by_content(narration_text) if narration_text else None
        if not music_path:
            # If no text provided or no matching music found, try random selection
            music_files = []
            for category in self.categories:
                music_files.extend((self.music_dir / category).glob("*.mp3"))
            if not music_files:
                return narration_path  # Return original narration if no music available
            music_path = str(random.choice(music_files))
            
        # Load and prepare background music
        background_music = AudioSegment.from_mp3(music_path)
        
        # Loop music if it's shorter than narration
        while len(background_music) < len(narration):
            background_music = background_music + background_music
            
        # Trim music to match narration length
        background_music = background_music[:len(narration)]
        
        # Add fade in/out effects
        fade_duration = min(3000, len(background_music) // 2)  # 3 seconds or half duration
        background_music = background_music.fade_in(fade_duration).fade_out(fade_duration)
        
        # Adjust music volume and mix
        background_music = background_music + music_volume
        mixed_audio = narration.overlay(background_music)
        
        # Generate output path if not provided
        if output_path is None:
            narration_filename = Path(narration_path).stem
            output_path = str(Path(narration_path).parent / f"{narration_filename}_with_music.mp3")
            
        # Export mixed audio
        mixed_audio.export(output_path, 
        format="mp3", bitrate="320k",
        parameters=[
            '-codec:a', 'libmp3lame',
            '-q:a', '0', # Highest quality
            '-ar', '44100', # Sample rate
            '-ac', '2', # Stereo
            '-b:a', '192k' # Bitrate
            ])
        return output_path 