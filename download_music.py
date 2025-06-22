#!/usr/bin/env python3
import os
import requests
from pathlib import Path
import urllib.parse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url: str, output_path: str) -> bool:
    """
    Download a file from URL and save it to output_path.
    Returns True if successful, False otherwise.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False

def setup_music_directories():
    """Create music category directories if they don't exist."""
    base_dir = Path("background_music")
    categories = ['chase', 'comedy', 'dramatic']
    
    for category in categories:
        (base_dir / category).mkdir(parents=True, exist_ok=True)
    
    return base_dir

def main():
    base_dir = setup_music_directories()
    
    # List of royalty-free music tracks to download
    tracks = [
        # Comedy/Light-hearted tracks (Tom and Jerry style)
        {
            'name': 'monkeys_spinning_monkeys.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Monkeys%20Spinning%20Monkeys.mp3',
            'category': 'comedy',
            'attribution': 'Monkeys Spinning Monkeys by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        {
            'name': 'circus_tent.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Circus%20Tent.mp3',
            'category': 'comedy',
            'attribution': 'Circus Tent by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        {
            'name': 'sneaky_snitch.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sneaky%20Snitch.mp3',
            'category': 'comedy',
            'attribution': 'Sneaky Snitch by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        
        # Chase/Action tracks (Fast-paced cartoon style)
        {
            'name': 'chase.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Chase.mp3',
            'category': 'chase',
            'attribution': 'Chase by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        {
            'name': 'merry_go.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Merry%20Go.mp3',
            'category': 'chase',
            'attribution': 'Merry Go by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        {
            'name': 'cartoon_battle.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cartoon%20Battle.mp3',
            'category': 'chase',
            'attribution': 'Cartoon Battle by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        
        # Dramatic/Suspense tracks (For tense moments)
        {
            'name': 'sneaky_adventure.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sneaky%20Adventure.mp3',
            'category': 'dramatic',
            'attribution': 'Sneaky Adventure by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        {
            'name': 'hidden_agenda.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Hidden%20Agenda.mp3',
            'category': 'dramatic',
            'attribution': 'Hidden Agenda by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        },
        {
            'name': 'spy_glass.mp3',
            'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Spy%20Glass.mp3',
            'category': 'dramatic',
            'attribution': 'Spy Glass by Kevin MacLeod (incompetech.com) - Licensed under Creative Commons: By Attribution 3.0'
        }
    ]
    
    # Download tracks
    for track in tracks:
        output_path = base_dir / track['category'] / track['name']
        
        if output_path.exists():
            logger.info(f"Track {track['name']} already exists, skipping...")
            continue
            
        logger.info(f"Downloading {track['name']}...")
        if download_file(track['url'], str(output_path)):
            logger.info(f"Successfully downloaded {track['name']}")
        else:
            logger.error(f"Failed to download {track['name']}")
            
    # Create attribution file
    attribution_path = base_dir / "ATTRIBUTION.md"
    with open(attribution_path, "w") as f:
        f.write("# Music Attribution\n\n")
        f.write("This directory contains the following royalty-free music tracks:\n\n")
        
        for track in tracks:
            f.write(f"## {track['name']}\n")
            f.write(f"Category: {track['category']}\n")
            f.write(f"Attribution: {track['attribution']}\n\n")

if __name__ == "__main__":
    main() 