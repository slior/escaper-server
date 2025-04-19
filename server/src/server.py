import paho.mqtt.client as mqtt
import json
import logging
import os
import threading
import time


# --- Import Configuration Loading ---
from config_loader import load_config
# --- Import Logging Setup ---
from logging_utils import setup_logging
# --- Import Audio Utils ---
from audio_utils import play_audio_threaded
# --- Import Station Handler ---
from station_handler import handle_station_event
# --- Import Control Handler ---
from control_handler import handle_control_message

# --- Configuration Loading ---
CONFIG = load_config()

# --- Logging Setup ---
# Define default log file path (used if not in config)
DEFAULT_LOG_FILE = '/app/logs/server.log'
LOG_FILE = CONFIG.get('log_file', DEFAULT_LOG_FILE)
setup_logging(LOG_FILE)

# --- State Management (In-Memory) ---
SESSION_STATE = "PENDING" # Possible states: PENDING, RUNNING, STOPPED
STATION_STATUS = {} # e.g., {"station_5": {"completed": false}, "station_door": {"completed": false}}

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
        global CONFIG # Allow modification of the global CONFIG
        new_session_state, new_station_status, reloaded_config = handle_control_message(payload, SESSION_STATE, STATION_STATUS)
        SESSION_STATE = new_session_state
        STATION_STATUS = new_station_status
        if reloaded_config is not None:
            CONFIG = reloaded_config # Update the global configuration
            logging.info("Server configuration has been reloaded.")
        return # Stop processing after handling a control message

    # --- Handle Station Event Messages ---
    if SESSION_STATE != "RUNNING":
        logging.debug(f"Ignoring message from {topic} because session state is {SESSION_STATE}")
        return

    handle_station_event(topic, payload, client, CONFIG, STATION_STATUS, logging)


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