"""
pip install opencv-python google-generativeai yt-dlp pydub
python manage.py runserver
"""

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from .models import AudioDescription
from .serializers import AudioDescriptionSerializer
from django.http import JsonResponse, FileResponse
import os
from pathlib import Path
import tempfile
from video_processing import VideoProcessor
from django.conf import settings
import uuid
import mimetypes
import logging
import time
from gtts import gTTS
import yt_dlp
from audio_processor import AudioProcessor
from text_to_speech_hume import HumeTTS
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from text_to_speech_factory import TTSFactory, TTSProvider, get_recommended_provider

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize AudioProcessor and HumeTTS
audio_processor = AudioProcessor()
hume_tts = HumeTTS()

# Create your views here.

class AudioDescriptionViewSet(viewsets.ModelViewSet):
    queryset = AudioDescription.objects.all()
    serializer_class = AudioDescriptionSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def user_descriptions(self, request):
        user_id = request.query_params.get('user_id', None)
        if user_id:
            descriptions = AudioDescription.objects.filter(user_id=user_id)
            serializer = self.get_serializer(descriptions, many=True)
            return Response(serializer.data)
        return Response({'error': 'user_id parameter is required'}, status=400)

def is_valid_video_file(file):
    """Check if the file is a valid video file."""
    valid_types = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo']
    file_type = mimetypes.guess_type(file.name)[0]
    logger.debug(f"File type detected: {file_type}")
    return file_type in valid_types

def save_uploaded_file(file, directory='videos'):
    """Save an uploaded file to a permanent location."""
    start_time = time.time()
    logger.debug(f"Starting file upload: {file.name}")
    
    # Create directory if it doesn't exist
    upload_dir = os.path.join(settings.MEDIA_ROOT, directory)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    ext = os.path.splitext(file.name)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    file_size = 0
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
            file_size += len(chunk)
    
    duration = time.time() - start_time
    logger.debug(f"File saved: {filepath}")
    logger.debug(f"Upload completed in {duration:.2f} seconds")
    logger.debug(f"File size: {file_size / (1024*1024):.2f} MB")
    
    return filepath

@api_view(['POST'])
def process_video(request):
    """
    Process a video file to generate description.
    Expects a video file in the request.
    """
    processing_start = time.time()
    logger.debug("Starting video processing request")
    
    if 'video' not in request.FILES:
        logger.error("No video file provided in request")
        return Response({
            'error': 'No video file provided',
            'status': 'error',
            'stage': 'validation'
        }, status=status.HTTP_400_BAD_REQUEST)

    video_file = request.FILES['video']
    logger.debug(f"Received video file: {video_file.name} (size: {video_file.size / (1024*1024):.2f} MB)")
    
    # Validate video file
    if not is_valid_video_file(video_file):
        logger.error(f"Invalid video format: {video_file.name}")
        return Response({
            'error': 'Invalid video file format. Please upload MP4, AVI, MOV, or similar video files.',
            'status': 'error',
            'stage': 'validation'
        }, status=status.HTTP_400_BAD_REQUEST)

    processing_status = {
        'status': 'processing',
        'stage': 'upload',
        'progress': 0,
        'start_time': processing_start
    }
    
    try:
        # Save video file permanently
        logger.debug("Saving video file")
        video_path = save_uploaded_file(video_file)
        processing_status['stage'] = 'video_saved'
        processing_status['progress'] = 20
        logger.debug(f"Video saved to: {video_path}")
        
        # Initialize video processor with API key from settings
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            logger.error("Google API key not found in settings")
            return Response({
                'error': 'Google API key not configured',
                'status': 'error',
                'stage': 'api_initialization'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        logger.debug("Initializing video processor")
        processor = VideoProcessor(api_key=api_key)
        processing_status['stage'] = 'extracting_frames'
        processing_status['progress'] = 30

        # Extract frames and generate description
        logger.debug("Extracting frames from video")
        frames = processor.extract_frames(video_path, frame_interval=10)
        if not frames:
            logger.error("Failed to extract frames from video")
            return Response({
                'error': 'Failed to extract frames from video',
                'status': 'error',
                'stage': 'frame_extraction'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.debug(f"Extracted {len(frames)} frames")
        processing_status['stage'] = 'generating_description'
        processing_status['progress'] = 50

        logger.debug("Generating description using Gemini")
        description_text = processor.generate_description(frames)
        if not description_text:
            logger.error("Failed to generate description")
            return Response({
                'error': 'Failed to generate description',
                'status': 'error',
                'stage': 'description_generation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.debug(f"Generated description (length: {len(description_text)} chars)")
        processing_status['stage'] = 'saving_to_database'
        processing_status['progress'] = 90

        # Store the description in the database
        logger.debug("Saving description to database")
        description = AudioDescription.objects.create(
            input_text=video_file.name,
            input_type='video',
            description_text=description_text,
            description_length='medium',  # Default to medium length
            user_id=request.data.get('user_id', 'anonymous')
        )
        logger.debug(f"Description saved with ID: {description.id}")

        processing_duration = time.time() - processing_start
        logger.debug(f"Video processing completed in {processing_duration:.2f} seconds")

        return Response({
            'status': 'success',
            'description': description_text,
            'description_id': description.id,
            'video_path': os.path.relpath(video_path, settings.MEDIA_ROOT),
            'processing_time': processing_duration,
            'frames_processed': len(frames),
            'description_length': len(description_text),
            'stages_completed': [
                'upload',
                'frame_extraction',
                'description_generation',
                'database_storage'
            ]
        })

    except Exception as e:
        logger.error(f"Error during video processing: {str(e)}", exc_info=True)
        return Response({
            'error': f'Error processing video: {str(e)}',
            'status': 'error',
            'stage': processing_status['stage'],
            'progress': processing_status['progress'],
            'processing_time': time.time() - processing_start
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def process_youtube(request):
    """
    Process a YouTube URL to generate description.
    Expects a YouTube URL in the request body.
    Downloads the video in 240p resolution using yt-dlp.
    """
    youtube_url = request.data.get('youtube_url')
    if not youtube_url:
        return Response({'error': 'No YouTube URL provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create videos directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(upload_dir, filename)

        def my_hook(d):
            if d['status'] == 'downloading':
                logger.debug(f"Downloading: {d.get('_percent_str', '0%')} of {d.get('_total_bytes_str', 'unknown size')}")
            elif d['status'] == 'finished':
                logger.debug('Download complete')

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'worst',  # Always select the lowest quality available
            'outtmpl': output_path,
            'progress_hooks': [my_hook],
            'verbose': True,
            'no_warnings': False,
            'extract_flat': False,
            'quiet': False,
        }

        # Download the video
        logger.debug(f"Starting download of YouTube video: {youtube_url}")
        logger.debug(f"Using options: {ydl_opts}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # First, try to extract video information
                info = ydl.extract_info(youtube_url, download=False)
                
                # Get video title
                video_title = info.get('title', 'Untitled Video')
                logger.debug(f"Video title: {video_title}")
                
                # Log available formats
                logger.debug("Available formats:")
                formats = sorted(info['formats'], key=lambda x: (x.get('width', 0) or 0) * (x.get('height', 0) or 0))
                for f in formats:
                    logger.debug(f"Format: {f.get('format_id', 'N/A')} - "
                               f"Width: {f.get('width', 'N/A')}px - "
                               f"Height: {f.get('height', 'N/A')}px - "
                               f"Extension: {f.get('ext', 'N/A')} - "
                               f"Filesize: {f.get('filesize', 'N/A')}")
                
                # Then download
                logger.debug("Starting download with lowest quality format...")
                ydl.download([youtube_url])
                
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"Download error: {str(e)}")
                return Response({
                    'error': f'Failed to download video: {str(e)}',
                    'status': 'error',
                    'available_formats': [f"{f.get('format_id', 'N/A')} - {f.get('width', 'N/A')}x{f.get('height', 'N/A')}" for f in formats]
                }, status=status.HTTP_400_BAD_REQUEST)

        if not os.path.exists(output_path):
            return Response({
                'error': 'Failed to download video - file not created',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.debug(f"Video downloaded successfully to: {output_path}")

        # Initialize video processor
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return Response({
                'error': 'Google API key not configured',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        processor = VideoProcessor(api_key=api_key)

        # Extract frames and generate description
        frames = processor.extract_frames(output_path, frame_interval=10)
        if not frames:
            return Response({
                'error': 'Failed to extract frames from video',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        description_text = processor.generate_description(frames)
        if not description_text:
            return Response({
                'error': 'Failed to generate description',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Store the description in the database using the video title
        description = AudioDescription.objects.create(
            input_text=video_title,  # Use video title instead of URL
            input_type='youtube',
            description_text=description_text,
            description_length='medium',
            user_id=request.data.get('user_id', 'anonymous')
        )

        return Response({
            'status': 'success',
            'title': video_title,  # Include title in response
            'description': description_text,
            'description_id': description.id,
            'video_path': os.path.relpath(output_path, settings.MEDIA_ROOT),
            'description_length': len(description_text)
        })

    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}", exc_info=True)
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_audio(request, filename):
    """
    Serve the generated audio file.
    """
    audio_path = os.path.join('audio_outputs', filename)
    if os.path.exists(audio_path):
        return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg')
    return Response({'error': 'Audio file not found'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@require_http_methods(["POST"])
def generate_audio(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        description_id = data.get('description_id')
        tts_provider = data.get('tts_provider', None)

        if not text:
            return JsonResponse({'error': 'Text is required'}, status=400)

        # Get recommended provider if not specified
        if tts_provider is None:
            provider = get_recommended_provider(text)
        else:
            try:
                provider = TTSProvider(tts_provider.lower())
            except ValueError:
                return JsonResponse({'error': f'Invalid TTS provider: {tts_provider}'}, status=400)

        # Generate unique filename based on description_id if provided
        filename = f"{description_id}_audio.mp3" if description_id else f"{uuid.uuid4()}_audio.mp3"

        # Generate audio file
        try:
            narration_path = TTSFactory.text_to_speech(
                text=text,
                provider=provider,
                filename=filename
            )
            
            # Mix narration with background music
            mixed_audio_path = audio_processor.mix_audio(
                narration_path=narration_path,
                narration_text=text  # Pass the text for mood analysis
            )
            
            # Get the relative path for storage in the database
            mixed_filename = os.path.basename(mixed_audio_path)
            
        except Exception as e:
            return JsonResponse({'error': f'Audio generation failed: {str(e)}'}, status=500)

        # Update or create AudioDescription if description_id is provided
        if description_id:
            try:
                audio_desc = AudioDescription.objects.get(id=description_id)
                audio_desc.audio_url = mixed_filename
                audio_desc.save()
            except AudioDescription.DoesNotExist:
                return JsonResponse({'error': 'Description not found'}, status=404)

        # Return the audio file path
        return JsonResponse({
            'audio_url': mixed_filename,
            'provider_used': provider.value
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def serve_audio(request, filename):
    """
    Serve audio files from the audio_outputs directory
    """
    try:
        # Construct the full path to the audio file
        audio_dir = os.path.join(settings.BASE_DIR, 'audio_outputs')
        file_path = os.path.join(audio_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'Audio file not found'}, status=404)
        
        # Return the file
        return FileResponse(open(file_path, 'rb'), content_type='audio/mpeg')
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
