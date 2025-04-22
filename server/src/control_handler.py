import logging
import json # Import json for potential error handling
from typing import Dict, Any, Optional, Tuple 
import paho.mqtt.client as mqtt 

from .config_loader import load_config
from .constants import (
    ACTION_START, ACTION_STOP, ACTION_RESET, ACTION_RELOAD_CONFIG,
    SESSION_STATE_RUNNING, SESSION_STATE_STOPPED, SESSION_STATE_PENDING,
    MQTT_TOPIC_SERVER_CONTROL
)


from .message_handler_interface import MessageHandler
from .server_state import ServerState

# --- Helper Functions ---

def _handle_start(current_session_state: str, current_station_status: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Handles the 'start' action."""
    if current_session_state != SESSION_STATE_RUNNING:
        new_session_state = SESSION_STATE_RUNNING
        new_station_status = {} # Reset station status on new session start
        logging.info("Escape Room Session STARTED")
        # Optionally play a session start sound
        # play_audio_threaded("session_start.wav")
    else:
        logging.warning("Received start command, but session is already RUNNING")
        new_session_state = current_session_state
        new_station_status = current_station_status # No change if already running
    return new_session_state, new_station_status

def _handle_stop() -> Tuple[str, Dict[str, Any]]:
    """Handles the 'stop' action."""
    logging.info("Escape Room Session STOPPED")
    return SESSION_STATE_STOPPED, {}

def _handle_reset() -> Tuple[str, Dict[str, Any]]:
    """Handles the 'reset' action."""
    logging.info("Escape Room Session RESET to PENDING state")
    return SESSION_STATE_PENDING, {}

def _handle_reload_config(current_session_state: str) -> Optional[Dict[str, Any]]:
    """Handles the 'reload_config' action."""
    reloaded_config = None
    if current_session_state == SESSION_STATE_RUNNING:
        logging.info("Received reload_config command. Attempting to reload configuration...")
        try:
            # Assuming default config path for now, could be parameterized
            reloaded_config = load_config()
            logging.info("Configuration successfully reloaded.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to reload configuration: {e}") # Log the error, but don't crash the server
            # reloaded_config remains None
        except Exception as e:
            logging.error(f"An unexpected error occurred during configuration reload: {e}")
            # reloaded_config remains None
    else:
        logging.warning(f"Ignoring reload_config command because session state is {current_session_state} (must be RUNNING)")
    return reloaded_config


# --- New Message Handler Class ---

class ControlMessageHandler(MessageHandler):
    """Handles control messages directed to the server."""

    def can_handle(self, topic: str, payload: Dict[str, Any], server_state: ServerState) -> bool:
        """Checks if the message is on the server control topic."""
        return topic == MQTT_TOPIC_SERVER_CONTROL

    def handle(self, topic: str, payload: Dict[str, Any], client: mqtt.Client, server_state: ServerState) -> ServerState:
        """Handles the control action specified in the payload."""
        action = payload.get("action")
        original_state = server_state # Keep reference for comparison/logging/immutability check

        # Start with values from the current state
        new_session_state = server_state.session_state
        new_station_status = server_state.station_status
        new_config = server_state.config
        state_changed = False # Flag to track if a new state object is needed

        if action == ACTION_START:
            calculated_session_state, calculated_station_status = _handle_start(server_state.session_state, server_state.station_status)
            if calculated_session_state != new_session_state or calculated_station_status != new_station_status:
                new_session_state = calculated_session_state
                new_station_status = calculated_station_status
                state_changed = True
        elif action == ACTION_STOP:
            calculated_session_state, calculated_station_status = _handle_stop()
            if calculated_session_state != new_session_state or calculated_station_status != new_station_status:
                new_session_state = calculated_session_state
                new_station_status = calculated_station_status
                state_changed = True
        elif action == ACTION_RESET:
            calculated_session_state, calculated_station_status = _handle_reset()
            if calculated_session_state != new_session_state or calculated_station_status != new_station_status:
                new_session_state = calculated_session_state
                new_station_status = calculated_station_status
                state_changed = True
        elif action == ACTION_RELOAD_CONFIG:
            reloaded_config_result = _handle_reload_config(server_state.session_state)
            
            if reloaded_config_result is not None and reloaded_config_result is not new_config:
                new_config = reloaded_config_result
                state_changed = True
            # Session state and station status remain unchanged for reload_config
        else:
            server_state.logger.warning(f"Unknown control action received: {action}")
            # No state change for unknown actions
            return original_state

        # Create and return a new state instance ONLY if something changed
        if state_changed:
            server_state.logger.debug(f"Control action '{action}' resulted in state change. Creating new ServerState.")
            return ServerState(
                session_state=new_session_state,
                station_status=new_station_status,
                config=new_config,
                logger=server_state.logger # Reuse the logger from the original state
            )
        else:
            server_state.logger.debug(f"Control action '{action}' did not result in state change. Returning original ServerState.")
            return original_state

