import paho.mqtt.client as mqtt
import json
import logging
import os
import threading
import time
from playsound import playsound, PlaysoundException

# --- Import Configuration Loading ---
from src.config_loader import load_config

# --- Configuration Loading ---
CONFIG = load_config()

# --- Logging Setup ---
LOG_FILE = CONFIG.get('log_file', '/app/logs/server.log')
LOG_DIR = os.path.dirname(LOG_FILE)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Log to console as well
    ]
)

# --- State Management (In-Memory) ---
SESSION_STATE = "PENDING" # Possible states: PENDING, RUNNING, STOPPED
STATION_STATUS = {} # e.g., {"station_5": {"completed": false}, "station_door": {"completed": false}}

# --- Audio Playback ---
AUDIO_BASE_PATH = CONFIG.get('audio_base_path', '/app/audio/')

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

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        # Subscribe to topics upon successful connection
        client.subscribe("escaperoom/station/+/event/+")
        client.subscribe("escaperoom/server/control/session")
        logging.info("Subscribed to: escaperoom/station/+/event/+ and escaperoom/server/control/session")
    else:
        logging.error(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"Disconnected from MQTT Broker with code: {rc}")
    if rc != 0:
        logging.info("Attempting to reconnect...")
        # Note: The Paho library handles reconnection attempts automatically.

def on_message(client, userdata, msg):
    global SESSION_STATE, STATION_STATUS
    topic = msg.topic
    try:
        payload_str = msg.payload.decode("utf-8")
        logging.info(f"Received message: {topic} - {payload_str}")
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON payload from topic {topic}: {payload_str}")
        return
    except UnicodeDecodeError:
        logging.error(f"Could not decode UTF-8 payload from topic {topic}")
        return
    except Exception as e:
        logging.error(f"Error processing message from {topic}: {e}")
        return

    # --- Handle Control Messages ---
    if topic == "escaperoom/server/control/session":
        action = payload.get("action")
        if action == "start":
            if SESSION_STATE != "RUNNING":
                SESSION_STATE = "RUNNING"
                STATION_STATUS = {} # Reset station status on new session start
                logging.info("Escape Room Session STARTED")
                # Optionally play a session start sound
                # play_audio_threaded("session_start.wav")
            else:
                logging.warning("Received start command, but session is already RUNNING")
        elif action == "stop":
            SESSION_STATE = "STOPPED"
            logging.info("Escape Room Session STOPPED")
            # Optionally play a session end sound
            # play_audio_threaded("session_end.wav")
        elif action == "reset":
            SESSION_STATE = "PENDING"
            STATION_STATUS = {} 
            logging.info("Escape Room Session RESET to PENDING state")
        else:
            logging.warning(f"Unknown control action received: {action}")
        return

    # --- Handle Station Event Messages ---
    if SESSION_STATE != "RUNNING":
        logging.debug(f"Ignoring message from {topic} because session state is {SESSION_STATE}")
        return

    # Parse topic: escaperoom/station/<station_id>/event/<event_type>
    try:
        parts = topic.split('/')
        if len(parts) == 5 and parts[0] == 'escaperoom' and parts[1] == 'station' and parts[3] == 'event':
            station_id = parts[2]
            event_type = parts[4]
        else:
            logging.warning(f"Received message on unexpected topic format: {topic}")
            return
    except IndexError:
        logging.warning(f"Could not parse topic: {topic}")
        return

    # --- Hardcoded Logic based on Config ---
    station_config = CONFIG.get("station_configs", {}).get(station_id)
    if not station_config:
        logging.debug(f"No configuration found for station_id: {station_id}")
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
                            logging.info(f"Beacon proximity triggered for {station_id}/{sensor_id}. Range {range_val} <= {threshold}")
                            play_audio_threaded(sound_file)
                            # Mark station as completed (example)
                            # STATION_STATUS[station_id] = {"completed": True}
                    except (ValueError, TypeError) as e:
                         logging.error(f"Invalid range/threshold value for {station_id}/{sensor_id}: {e}")
                else:
                    logging.warning(f"Incomplete configuration or payload for beacon_proximity check on {station_id}/{sensor_id}")

            # Example Logic 2: Door Status
            elif event_type == "door_status":
                status = payload.get("status")
                trigger_val = sensor_config.get("trigger_value")
                sound_file = sensor_config.get("sound_on_trigger")

                if status is not None and trigger_val is not None and sound_file:
                     if str(status).upper() == str(trigger_val).upper():
                            logging.info(f"Door status triggered for {station_id}/{sensor_id}. Status {status} == {trigger_val}")
                            play_audio_threaded(sound_file)
                            # Mark station as completed (example)
                            # STATION_STATUS[station_id] = {"completed": True}
                else:
                    logging.warning(f"Incomplete configuration or payload for door_status check on {station_id}/{sensor_id}")
            
            # Add more elif blocks here for other event types and logic
            else:
                logging.debug(f"No specific logic defined for event type: {event_type} on {station_id}/{sensor_id}")


# --- MQTT Client Setup ---
def create_mqtt_client():
    broker_host = CONFIG['mqtt_broker']['host']
    broker_port = CONFIG['mqtt_broker']['port']
    client_id = f"escape-room-server-{os.getpid()}"
    
    client = mqtt.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Optional: Add username/password authentication if your broker requires it
    # client.username_pw_set(username="your_username", password="your_password")

    logging.info(f"Attempting to connect to MQTT broker at {broker_host}:{broker_port}")
    try:
        client.connect(broker_host, broker_port, 60) # 60-second keepalive
    except Exception as e:
        logging.error(f"MQTT connection failed: {e}")
        # The loop_start/loop_forever will handle retries

    return client

# --- Main Execution ---
if __name__ == "__main__":
    logging.info("Starting Escape Room Server...")
    client = create_mqtt_client()

    # Start the MQTT network loop in a separate thread
    # loop_start() is non-blocking and handles reconnections automatically.
    client.loop_start()

    logging.info("Server running. Waiting for MQTT messages...")
    # Keep the main thread alive
    try:
        while True:
            # You could add periodic tasks here if needed
            # e.g., check session timeout, save state periodically (future)
            time.sleep(1) 
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    finally:
        client.loop_stop() # Stop the network loop
        client.disconnect()
        logging.info("MQTT client disconnected. Server stopped.") 