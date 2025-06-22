# BlindTube-mini 🎥 ➡️ 🎧

BlindTube is an innovative platform that transforms visual content into rich audio experiences, making movies, entertainment videos, and cartoons accessible to visually impaired individuals. By combining advanced AI technologies, we create immersive audiobook-style narratives from video content.

This project is conducted by [Jianyu Hou] (https://github.com/houjer23), [Simin Fan] (https://github.com/Olivia-fsm), and [Luoyi Zhang] (https://github.com/louisazz). It is built on from [BlindTube](https://github.com/Olivia-fsm/BlindTube)

## 🌟 Features

- Video to narrative conversion using Google's Gemini AI
- Emotional context analysis with Hume.ai
- High-quality voice synthesis using ElevenLabs
- Dynamic background music selection based on scene context
- Web interface for easy content management
- Support for various video formats

## 🚀 Getting Started

### Prerequisites

- Python
- API keys for:
  - Google Gemini AI
  - ElevenLabs
  - Hume.ai

### Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd BlindTube
```

2. Create and activate a virtual environment:
```bash
python3 -m venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
Create a `.env` file in the root directory with:
```
ELEVENLABS_API_KEY=your_elevenlabs_key
GOOGLE_API_KEY=your_google_key
HUME_API_KEY=your_hume_key
```

5. Initialize the database:
```bash
python manage.py migrate
```

6. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## 🎯 How It Works

1. **Video Processing**: 
   - Videos are processed and analyzed frame by frame
   - Key scenes and moments are identified
   - Visual content is converted into descriptive narratives

2. **AI Enhancement**:
   - Gemini AI transforms visual content into engaging stories
   - Hume.ai analyzes emotional context
   - ElevenLabs converts text to natural-sounding speech

3. **Audio Production**:
   - Dynamic background music selection
   - Professional-grade audio mixing
   - Seamless narrative flow

## 📁 Project Structure

```
BlindTube/
├── audio_processor.py         # Audio processing and mixing
├── background_music/         # Background music assets
├── descriptions/            # Django app for managing descriptions
├── text_to_speech_*.py     # Various TTS implementations
└── video_processing.py     # Video analysis and processing
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- Google Gemini AI for video understanding
- ElevenLabs and Hume.ai for Text-To-Speech
