import copy # Import copy for deep copying station_status
from typing import Dict, Any 
import paho.mqtt.client as mqtt 

from .message_handler_interface import MessageHandler
from .server_state import ServerState
from .constants import SESSION_STATE_RUNNING, MQTT_TOPIC_STATION_BASE

# --- Import Audio Utils ---
# Use relative import because station_handler is part of the 'src' package
from .audio_utils import play_audio_threaded

EVENT_TOPIC_SEGMENT = 'event'
EVENT_TOPIC_SEGMENT_LENGTH = 5
EVENT_TOPIC_SEGMENT_INDEX = 3
EVENT_TOPIC_STATION_INDEX = 2
EVENT_TOPIC_BASE = 'escaperoom/station'
EVENT_TOPIC_EVENT_TYPE_INDEX = 4

class StationEventHandler(MessageHandler):
    """Handles events originating from individual stations."""

    def can_handle(self, topic: str, payload: Dict[str, Any], server_state: ServerState) -> bool:
        """Checks if the message is a valid station event and the session is running."""
        
        # Check 1: Session must be running
        if server_state.session_state != SESSION_STATE_RUNNING:
            # Log why it can't be handled (optional, but helpful for debugging)
            server_state.logger.debug(f"Ignoring station event from {topic}: Session not RUNNING (state={server_state.session_state})")
            return False

        # Check 2: Topic structure must match station event pattern
        # Expected: escaperoom/station/<station_id>/event/<event_type>
        if not topic.startswith(MQTT_TOPIC_STATION_BASE):
            return False
        
        parts = topic.split('/')
        
        is_valid_structure = ( # Check length and that 'event' keyword is present
            len(parts) == EVENT_TOPIC_SEGMENT_LENGTH and 
            parts[EVENT_TOPIC_SEGMENT_INDEX] == EVENT_TOPIC_SEGMENT
            # parts[0] and parts[1] are covered by startswith check
        )

        return is_valid_structure

    def handle(self, topic: str, payload: Dict[str, Any], client: mqtt.Client, server_state: ServerState) -> ServerState:
        """Processes the station event based on configuration and payload."""
        
        logger = server_state.logger # Use logger from state
        config = server_state.config
        original_station_status = server_state.station_status
        state_changed = False

        # Parse topic (already validated structure in can_handle)
        try:
            parts = topic.split('/')
            station_id = parts[EVENT_TOPIC_STATION_INDEX]
            event_type = parts[EVENT_TOPIC_EVENT_TYPE_INDEX]
        except IndexError: # Should not happen if can_handle is correct, but belt-and-suspenders
            logger.error(f"Could not parse already validated topic: {topic}")
            return server_state # Return original state on error

        # --- Logic moved from old handle_station_event ---
        station_config = config.get("station_configs", {}).get(station_id)
        if not station_config:
            logger.debug(f"No configuration found for station_id: {station_id}")
            return server_state # No config, no state change

        # Create a copy to modify if needed
        # Use deepcopy if status contains nested mutable structures
        # If status is simple dict of primitives, a shallow copy (.copy()) is fine
        # Assuming shallow might be okay, but deepcopy is safer without knowing the exact structure.
        new_station_status = copy.deepcopy(original_station_status)

        for sensor_id, sensor_config in station_config.items():
            if sensor_config.get("event_type") == event_type: ## TODO: this should be refactored as well. Should have different logic for different event types.
                # Example Logic 1: Beacon Proximity
                if event_type == "beacon_proximity":
                    range_val = payload.get("range")
                    threshold = sensor_config.get("range_threshold")
                    sound_file = sensor_config.get("sound_on_trigger")

                    if range_val is not None and threshold is not None and sound_file:
                        try:
                            if float(range_val) <= float(threshold):
                                logger.info(f"Beacon proximity triggered for {station_id}/{sensor_id}. Range {range_val} <= {threshold}")
                                play_audio_threaded(sound_file)
                                # Update the status copy
                                if new_station_status.get(station_id) != {"completed": True}: # Example update logic
                                    logger.info(f"Updating status for station {station_id} to completed.")
                                    new_station_status[station_id] = {"completed": True}
                                    state_changed = True
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid range/threshold value for {station_id}/{sensor_id}: {e}")
                    else:
                        logger.warning(f"Incomplete configuration or payload for beacon_proximity check on {station_id}/{sensor_id}")

                # Example Logic 2: Door Status
                elif event_type == "door_status":
                    status = payload.get("status")
                    trigger_val = sensor_config.get("trigger_value")
                    sound_file = sensor_config.get("sound_on_trigger")

                    if status is not None and trigger_val is not None and sound_file:
                        if str(status).upper() == str(trigger_val).upper():
                                logger.info(f"Door status triggered for {station_id}/{sensor_id}. Status {status} == {trigger_val}")
                                play_audio_threaded(sound_file)
                                # Update the status copy
                                if new_station_status.get(station_id) != {"completed": True}: # Example update logic
                                    logger.info(f"Updating status for station {station_id} to completed.")
                                    new_station_status[station_id] = {"completed": True} 
                                    state_changed = True
                    else:
                        logger.warning(f"Incomplete configuration or payload for door_status check on {station_id}/{sensor_id}")

                # Add more elif blocks here for other event types and logic
                else:
                    logger.debug(f"No specific logic defined for event type: {event_type} on {station_id}/{sensor_id}")
                
                # Decide whether to break or continue if a sensor was processed
                # break # Example: Stop after first matching sensor

        # --- Return State ---
        if state_changed:
            logger.debug(f"Station event '{event_type}' for {station_id} resulted in state change. Creating new ServerState.")
            return ServerState(
                session_state=server_state.session_state, # Session state unchanged by station events
                station_status=new_station_status, # Return the modified copy
                config=server_state.config, # Config unchanged by station events
                logger=server_state.logger
            )
        else:
            logger.debug(f"Station event '{event_type}' for {station_id} did not result in state change. Returning original ServerState.")
            return server_state # Return the original state if no changes occurred
