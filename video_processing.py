import cv2
import base64
import os
from typing import List, Optional
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import sys
from django.conf import settings

class VideoProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the VideoProcessor with Gemini client."""
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google API key is required")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        
    def extract_frames(self, video_path: str, frame_interval: int = 5) -> List[str]:
        """
        Extract frames from a video file and convert them to base64.
        
        Args:
            video_path: Path to the video file
            frame_interval: Interval between frames to extract (default: 5)
            
        Returns:
            List of base64 encoded frames
        """
        video = cv2.VideoCapture(video_path)
        base64_frames = []
        frame_count = 0
        
        while video.isOpened():
            success, frame = video.read()
            if not success:
                break
                
            # Only keep frames at the specified interval
            if frame_count % frame_interval == 0:
                _, buffer = cv2.imencode(".jpg", frame)
                base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
            
            frame_count += 1
            
        video.release()
        return base64_frames
    
    def generate_description(self, frames: List[str]) -> str:
        """
        Generate a description of the video using Gemini Vision.
        
        Args:
            frames: List of base64 encoded frames
            
        Returns:
            Generated description text
        """
        # Convert base64 frames to image parts
        image_parts = []
        for frame in frames:
            image_parts.append({
                "mime_type": "image/jpeg",
                "data": frame
            })
        
        # Create the prompt
        # prompt = """These are frames from a video that I want to upload. 
        # Generate only one compelling description that I can upload along with the 
        # video. Description should describe every detail in the video. This will 
        # be narrated for people who can not see as a story, so it should be very 
        # interesting and engaging. This should be like a book. Start right into the 
        # story. You can descript the scence like a book, but do not anything like The 
        # scene opens on that makes it not like the story."""
        prompt = """These are frames from a video that I want to upload. 
        Generate only one lively andcompelling text script that I can upload along with the 
        video. The script should describe every detail in the video. This will 
        be narrated for people who can not see as a lively story and radio drama, so it should be very 
        interesting and engaging. Start right into the story. You can describ the scene like a book, but do not anything like The 
        scene opens on that makes it not like the story. Do not be too long or too short."""
        #You can add soound effects 
        #and wrap around with [], like [gunshot], [applause], [clapping], [explosion], 
        #[swallows], [gulps] ...
        
        # Generate content using Gemini
        response = self.model.generate_content(
            contents=[prompt] + image_parts,
            generation_config={
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 10000,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        return response.text

def main():
    """Example usage of the VideoProcessor class."""
    if len(sys.argv) != 2:
        print("Usage: python video_processing.py <video_path>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        sys.exit(1)
        
    # Initialize the processor
    processor = VideoProcessor()
    
    # Extract frames
    print("Extracting frames...")
    frames = processor.extract_frames(video_path, 120) # modify based on the video length
    print(f"Extracted {len(frames)} frames")
    
    # Generate description
    print("\nGenerating description...")
    description = processor.generate_description(frames)
    print("\nDescription:")
    print(description)
    
    # Save the results to a text file
    output_dir = os.path.dirname(video_path)
    output_path = os.path.join(output_dir, "video_description.txt")
    with open(output_path, "w") as f:
        f.write(description)
    print(f"\nDescription saved to {output_path}")

if __name__ == "__main__":
    main()
