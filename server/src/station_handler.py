import json
import logging

# --- Import Audio Utils ---
# Use relative import because station_handler is part of the 'src' package
try:
    from .audio_utils import play_audio_threaded
except ImportError:
    # Fallback or error handling if audio_utils is not found
    logging.exception("Failed to import play_audio_threaded from .audio_utils. Check relative path and file existence.")
    # Define a dummy function or re-raise the error depending on desired behavior
    def play_audio_threaded(sound_file):
        logging.warning(f"Audio playback skipped for {sound_file} (audio_utils import failed).")


def handle_station_event(topic, payload, client, config, station_status, logger):
    """
    Handles incoming MQTT messages for specific station events.

    Args:
        topic (str): The MQTT topic the message was received on.
        payload (dict): The decoded JSON payload of the message.
        client: The MQTT client instance (unused currently, but passed for future use).
        config (dict): The loaded server configuration.
        station_status (dict): The dictionary tracking station statuses.
        logger: The logging instance.
    """
    # Parse topic: escaperoom/station/<station_id>/event/<event_type>
    try:
        parts = topic.split('/')
        if len(parts) == 5 and parts[0] == 'escaperoom' and parts[1] == 'station' and parts[3] == 'event':
            station_id = parts[2]
            event_type = parts[4]
        else:
            logger.warning(f"Received message on unexpected topic format: {topic}")
            return
    except IndexError:
        logger.warning(f"Could not parse topic: {topic}")
        return

    # --- Hardcoded Logic based on Config ---
    station_config = config.get("station_configs", {}).get(station_id)
    if not station_config:
        logger.debug(f"No configuration found for station_id: {station_id}")
        return

    for sensor_id, sensor_config in station_config.items():
        # Check if the event type matches the sensor's configured event type
        if sensor_config.get("event_type") == event_type:

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
                            # Mark station as completed (example)
                            # station_status[station_id] = {"completed": True} # Note: Modifies passed dict
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
                            # Mark station as completed (example)
                            # station_status[station_id] = {"completed": True} # Note: Modifies passed dict
                else:
                    logger.warning(f"Incomplete configuration or payload for door_status check on {station_id}/{sensor_id}")

            # Add more elif blocks here for other event types and logic
            else:
                logger.debug(f"No specific logic defined for event type: {event_type} on {station_id}/{sensor_id}")

            # If we found a matching sensor and processed it, we might want to break
            # or continue depending on whether multiple sensors can react to the same event.
            # Current logic continues the loop. 