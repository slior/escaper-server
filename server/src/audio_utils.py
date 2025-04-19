import os
import threading
import logging
from playsound import playsound, PlaysoundException
from .config_loader import load_config

# Load configuration specifically for audio settings
# Assuming config.json is in the root relative to where server.py is run
# Or adjust the path in load_config() if needed globally
CONFIG = load_config() 
AUDIO_BASE_PATH = CONFIG.get('audio_base_path', '/app/audio/') # Default if not in config

def play_audio_threaded(sound_file_name):
    """Plays an audio file in a separate thread."""
    def target():
        audio_path = os.path.join(AUDIO_BASE_PATH, sound_file_name)
        if not os.path.exists(audio_path):
            logging.error(f"Audio file not found: {audio_path}")
            return
        try:
            logging.info(f"Playing sound: {audio_path}")
            playsound(audio_path)
            logging.info(f"Finished playing: {sound_file_name}")
        except PlaysoundException as e:
            logging.error(f"Error playing sound {audio_path}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during audio playback {audio_path}: {e}")

    thread = threading.Thread(target=target)
    thread.daemon = True # Allow main program to exit even if thread is running
    thread.start() 