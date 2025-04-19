import logging
import json # Import json for potential error handling

# --- Import Configuration Loading ---
from config_loader import load_config

# --- Import Audio Utils (Optional, if needed for control actions in the future) ---
# from audio_utils import play_audio_threaded

def handle_control_message(payload, current_session_state, current_station_status):
    """
    Handles incoming MQTT messages for server control actions.

    Args:
        payload (dict): The decoded JSON payload of the message.
        current_session_state (str): The current session state.
        current_station_status (dict): The current station status dictionary.

    Returns:
        tuple: A tuple containing the updated session_state (str),
               updated station_status (dict), and potentially the
               reloaded configuration (dict or None).
    """
    action = payload.get("action")
    new_session_state = current_session_state
    new_station_status = current_station_status.copy() # Work on a copy
    reloaded_config = None # Default to no config change

    if action == "start":
        if current_session_state != "RUNNING":
            new_session_state = "RUNNING"
            new_station_status = {} # Reset station status on new session start
            logging.info("Escape Room Session STARTED")
            # Optionally play a session start sound
            # play_audio_threaded("session_start.wav")
        else:
            logging.warning("Received start command, but session is already RUNNING")
    elif action == "stop":
        new_session_state = "STOPPED"
        logging.info("Escape Room Session STOPPED")
        # Optionally play a session end sound
        # play_audio_threaded("session_end.wav")
    elif action == "reset":
        new_session_state = "PENDING"
        new_station_status = {}
        logging.info("Escape Room Session RESET to PENDING state")
    elif action == "reload_config":
        if current_session_state == "RUNNING":
            logging.info("Received reload_config command. Attempting to reload configuration...")
            try:
                # Assuming default config path for now, could be parameterized
                reloaded_config = load_config()
                logging.info("Configuration successfully reloaded.")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                # Log the error, but don't crash the server
                logging.error(f"Failed to reload configuration: {e}")
                # reloaded_config remains None
            except Exception as e:
                logging.error(f"An unexpected error occurred during configuration reload: {e}")
                # reloaded_config remains None
        else:
            logging.warning(f"Ignoring reload_config command because session state is {current_session_state} (must be RUNNING)")
    else:
        logging.warning(f"Unknown control action received: {action}")

    return new_session_state, new_station_status, reloaded_config # Return the potentially reloaded config 