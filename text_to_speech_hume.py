import asyncio
import os
import re
import base64
import ssl
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from hume import HumeClient, AsyncHumeClient
from hume.tts import PostedUtterance
import uuid
import nltk
import aiohttp
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential
from tenacity import retry

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from pydub import AudioSegment

class HumeTTS:
    MAX_CHARS = 4800  # Setting slightly below 5000 for safety
    MAX_RETRIES = 3
    INITIAL_WAIT = 2  # Initial wait time in seconds
    MAX_WAIT = 10  # Maximum wait time in seconds
    TIMEOUT = 240  # Timeout in seconds

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("HUME_API_KEY")
        if not self.api_key:
            raise ValueError("Please set HUME_API_KEY environment variable")
        
        # Download nltk data for sentence tokenization
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
            except Exception as e:
                print(f"Warning: Could not download NLTK punkt data: {e}")
                print("Falling back to basic sentence splitting...")

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks that respect sentence boundaries and max character limit.
        
        Args:
            text (str): The input text to split
            
        Returns:
            List[str]: List of text chunks
        """
        # First, try to split into sentences using nltk
        try:
            sentences = nltk.sent_tokenize(text)
        except Exception:
            # Fallback to basic sentence splitting if nltk fails
            print("Using fallback sentence splitting...")
            # Split on common sentence endings
            text = text.replace('...', '…')  # Normalize ellipsis
            sentences = []
            current = ""
            
            # Split on sentence endings while preserving the punctuation
            for char in text:
                current += char
                if char in '.!?' and len(current.strip()) > 0:
                    sentences.append(current.strip())
                    current = ""
            
            if current.strip():
                sentences.append(current.strip())
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If the sentence alone is too long, split it by punctuation
            if len(sentence) > self.MAX_CHARS:
                sub_sentences = re.split(r'[,;:]', sentence)
                for sub_sentence in sub_sentences:
                    sub_sentence = sub_sentence.strip()
                    if len(sub_sentence) > self.MAX_CHARS:
                        # If still too long, split by word boundaries
                        words = sub_sentence.split()
                        temp_chunk = ""
                        for word in words:
                            if len(temp_chunk) + len(word) + 1 <= self.MAX_CHARS:
                                temp_chunk += " " + word if temp_chunk else word
                            else:
                                chunks.append(temp_chunk)
                                temp_chunk = word
                        if temp_chunk:
                            chunks.append(temp_chunk)
                    else:
                        if len(current_chunk) + len(sub_sentence) + 2 <= self.MAX_CHARS:
                            current_chunk += ". " + sub_sentence if current_chunk else sub_sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sub_sentence
            else:
                if len(current_chunk) + len(sentence) + 2 <= self.MAX_CHARS:
                    current_chunk += ". " + sentence if current_chunk else sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _select_voice_description(self, text: str) -> str:
        """
        Select an appropriate voice description based on text content.
        
        Args:
            text (str): The input text to analyze
            
        Returns:
            str: The selected voice description
        """
        # Convert to lowercase for easier matching
        text_lower = text.lower()
        
        # Voice descriptions for different content types
        VOICE_DESCRIPTIONS = {
            'story': "A warm and engaging storyteller with a gentle, soothing voice that brings stories to life",
            'comic': "A classic English voice actor narrating a comic with an intriguing, cute, lively voice",
            'action': "An energetic and dynamic voice actor with a powerful, commanding presence",
            'educational': "A clear, articulate professor with a patient and engaging teaching style",
            'nature': "A calm and contemplative naturalist with a sense of wonder in their voice",
            'news': "A professional news anchor with a clear, authoritative, and trustworthy voice",
            'children': "A friendly, enthusiastic voice with a playful and nurturing tone perfect for children",
            'technical': "A precise, knowledgeable expert with a clear and methodical speaking style",
            'emotional': "A sensitive and empathetic voice that conveys deep emotional understanding",
            'default': "A professional, clear voice with natural and engaging delivery"
        }
        
        # Keywords to match different content types
        content_patterns = {
            'story': r'\b(once|story|tale|adventure|chapter|novel)\b',
            'comic': r'\b(comic|superhero|pow|bang|zoom|hero|villain|tom|jerry)\b',
            'action': r'\b(fight|battle|explosion|chase|race|action|thrill)\b',
            'educational': r'\b(learn|study|explain|understand|concept|theory|lesson)\b',
            'nature': r'\b(nature|wildlife|forest|ocean|animal|plant|environment)\b',
            'news': r'\b(report|announce|breaking|news|update|recent|today)\b',
            'children': r'\b(kid|child|play|fun|magic|wonder|imagine)\b',
            'technical': r'\b(technical|system|process|method|algorithm|data|function)\b',
            'emotional': r'\b(feel|emotion|heart|love|sad|joy|hope)\b'
        }
        
        # Count matches for each content type
        matches = {
            content_type: len(re.findall(pattern, text_lower))
            for content_type, pattern in content_patterns.items()
        }
        
        # Select the content type with the most matches
        best_match = max(matches.items(), key=lambda x: x[1])
        
        # If no significant matches found (threshold of at least 1 match)
        if best_match[1] == 0:
            return VOICE_DESCRIPTIONS['default']
        
        return VOICE_DESCRIPTIONS[best_match[0]]

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=INITIAL_WAIT, max=MAX_WAIT),
        reraise=True
    )
    async def _generate_audio_with_retry(self, text: str, chunk_index: Optional[int] = None) -> bytes:
        """
        Generate audio from text using Hume AI's TTS API with retry logic
        
        Args:
            text (str): The text to convert to speech
            chunk_index (int, optional): The index of the current chunk for logging
            
        Returns:
            bytes: The audio data in bytes
        """
        client = AsyncHumeClient(api_key=self.api_key)
        
        try:
            # Select appropriate voice description based on content
            voice_description = self._select_voice_description(text)
            chunk_info = f" (chunk {chunk_index + 1})" if chunk_index is not None else ""
            print(f"Processing{chunk_info} with voice: {voice_description}")
            
            # Generate audio using TTS API with timeout
            result = await asyncio.wait_for(
                client.tts.synthesize_json(
                    utterances=[
                        PostedUtterance(
                            text=text,
                            description=voice_description
                        )
                    ]
                ),
                timeout=self.TIMEOUT
            )
            
            if not result or not result.generations or not result.generations[0].audio:
                raise RuntimeError("No audio generated")
                
            # The audio is returned as base64-encoded string
            return base64.b64decode(result.generations[0].audio)
            
        except asyncio.TimeoutError:
            error_msg = f"Request timed out{chunk_info}"
            print(f"{error_msg}. Retrying with increased timeout...")
            self.TIMEOUT += 30  # Increase timeout for next retry
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error during TTS generation{chunk_info}: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)

    async def _process_chunks(self, chunks: List[str], output_path: Path, output_file: Path) -> None:
        """
        Process text chunks and combine them into a single audio file
        
        Args:
            chunks (List[str]): List of text chunks to process
            output_path (Path): Directory for output files
            output_file (Path): Final output file path
        """
        combined_audio = None
        
        for i, chunk in enumerate(chunks):
            try:
                print(f"Processing chunk {i+1}/{len(chunks)}")
                audio_data = await self._generate_audio_with_retry(chunk, i)
                
                # Save temporary file
                temp_file = output_path / f"temp_{i}.mp3"
                with open(temp_file, 'wb') as f:
                    f.write(audio_data)
                
                # Load audio segment
                audio_segment = AudioSegment.from_mp3(temp_file)
                
                # Add to combined audio
                if combined_audio is None:
                    combined_audio = audio_segment
                else:
                    # Add a small pause between chunks
                    combined_audio += AudioSegment.silent(duration=500) + audio_segment
                
                # Clean up temp file
                os.remove(temp_file)
                
            except Exception as e:
                print(f"Error processing chunk {i+1}: {str(e)}")
                # Clean up any temporary files
                temp_files = list(output_path.glob("temp_*.mp3"))
                for temp_file in temp_files:
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                raise

        # Export combined audio
        if combined_audio is not None:
            combined_audio.export(output_file, format="mp3")
        else:
            raise RuntimeError("Failed to generate combined audio")

    def text_to_speech(self, text: str, output_dir: str = "audio_outputs", filename: str | None = None) -> str:
        """
        Convert text to speech using Hume AI Text to Speech API
        
        Args:
            text (str): The text to convert to speech
            output_dir (str): Directory to store the audio output
            filename (str): Optional filename for the output file
            
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
        
        # Split text into chunks if needed
        chunks = self._split_text_into_chunks(text)
        
        if len(chunks) == 1:
            # If only one chunk, generate audio directly
            audio_data = asyncio.run(self._generate_audio_with_retry(chunks[0]))
            with open(output_file, 'wb') as f:
                f.write(audio_data)
        else:
            # If multiple chunks, generate audio for each and concatenate
            print(f"Text split into {len(chunks)} chunks")
            asyncio.run(self._process_chunks(chunks, output_path, output_file))
        
        return str(output_file)

if __name__ == "__main__":
    # Example usage
    input_file = "video_description.txt"
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read().strip()
        
        tts = HumeTTS()
        output_file = tts.text_to_speech(text_content)
        print(f"Audio file generated successfully: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
