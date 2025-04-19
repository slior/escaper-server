import logging

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
        tuple: A tuple containing the updated session_state (str) and 
               updated station_status (dict).
    """
    action = payload.get("action")
    new_session_state = current_session_state
    new_station_status = current_station_status.copy() # Work on a copy

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
    else:
        logging.warning(f"Unknown control action received: {action}")

    return new_session_state, new_station_status 