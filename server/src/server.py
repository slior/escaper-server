import paho.mqtt.client as mqtt
import json
import logging
import os
import threading
import time


# --- Import Configuration Loading ---
from .config_loader import load_config
# --- Import Logging Setup ---
from .logging_utils import setup_logging
# --- Import Audio Utils ---
from .audio_utils import play_audio_threaded
# --- Import Station Handler ---
from .station_handler import handle_station_event
# --- Import Control Handler ---
from .control_handler import handle_control_message

# --- Constants ---
# Session States
SESSION_STATE_PENDING = "PENDING"
SESSION_STATE_RUNNING = "RUNNING"
SESSION_STATE_STOPPED = "STOPPED"

# MQTT Topics
MQTT_TOPIC_STATION_EVENTS = "escaperoom/station/+/event/+"
MQTT_TOPIC_SERVER_CONTROL = "escaperoom/server/control/session"

# MQTT Configuration
MQTT_CLIENT_ID_PREFIX = "escape-room-server-"
MQTT_KEEPALIVE_SECONDS = 60

# Other Constants
MAIN_LOOP_SLEEP_SECONDS = 1
DEFAULT_LOG_FILE = '/app/logs/server.log' # used if not in config

# --- Configuration Loading ---
CONFIG = load_config()

# --- Logging Setup ---
LOG_FILE = CONFIG.get('log_file', DEFAULT_LOG_FILE)
setup_logging(LOG_FILE)

# --- State Management (In-Memory) ---
SESSION_STATE = SESSION_STATE_PENDING # Initial state
STATION_STATUS = {} # e.g., {"station_5": {"completed": false}, "station_door": {"completed": false}}

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        # Subscribe to topics upon successful connection
        client.subscribe(MQTT_TOPIC_STATION_EVENTS)
        client.subscribe(MQTT_TOPIC_SERVER_CONTROL)
        logging.info(f"Subscribed to: {MQTT_TOPIC_STATION_EVENTS} and {MQTT_TOPIC_SERVER_CONTROL}")
    else:
        logging.error(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"Disconnected from MQTT Broker with code: {rc}")
    if rc != 0:
        logging.info("Attempting to reconnect...")
        # Note: The Paho library handles reconnection attempts automatically.

def _parse_message_payload(msg):
    """Attempts to decode and parse the message payload."""
    topic = msg.topic
    try:
        payload_str = msg.payload.decode("utf-8")
        logging.info(f"Received message: {topic} - {payload_str}")
        payload = json.loads(payload_str)
        return payload, payload_str
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON payload from topic {topic}: {payload_str}")
        return None, None
    except UnicodeDecodeError:
        logging.error(f"Could not decode UTF-8 payload from topic {topic}")
        return None, None
    except Exception as e:
        logging.error(f"Error processing message from {topic}: {e}")
        return None, None

def _handle_control_message_internal(payload):
    """Handles incoming control messages."""
    global SESSION_STATE, STATION_STATUS, CONFIG
    new_session_state, new_station_status, reloaded_config = handle_control_message(payload, SESSION_STATE, STATION_STATUS)
    SESSION_STATE = new_session_state
    STATION_STATUS = new_station_status
    if reloaded_config is not None:
        CONFIG = reloaded_config # Update the global configuration
        logging.info("Server configuration has been reloaded.")

def _handle_station_event_internal(topic, payload, client):
    """Handles incoming station event messages if the session is running."""
    if SESSION_STATE != SESSION_STATE_RUNNING:
        logging.debug(f"Ignoring message from {topic} because session state is {SESSION_STATE}")
        return
    handle_station_event(topic, payload, client, CONFIG, STATION_STATUS, logging)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload, _ = _parse_message_payload(msg)
    if payload is None:
        return # Error already logged in _parse_message_payload

    # --- Handle Control Messages FIRST ---
    if topic == MQTT_TOPIC_SERVER_CONTROL:
        _handle_control_message_internal(payload)
        return # Stop processing after handling a control message

    # --- Handle Station Event Messages ---
    # Check if the topic looks like a valid station event
    topic_parts = topic.split('/')
    # Expected structure: escaperoom/station/<station_id>/event/<event_type>
    # Check: starts with prefix, has enough parts, and 'event' is in the right place
    is_station_event_topic = (
        topic.startswith("escaperoom/station/") and
        len(topic_parts) >= 5 and
        topic_parts[3] == "event"
    )

    if is_station_event_topic:
         _handle_station_event_internal(topic, payload, client)
    else:
        # This catches topics that didn't match control and don't look like valid station events
        # (e.g., "escaperoom/station/malformed", "other/topic")
        logging.warning(f"Received message on unhandled topic: {topic}")


# --- MQTT Client Setup ---
def create_mqtt_client():
    broker_host = CONFIG['mqtt_broker']['host']
    broker_port = CONFIG['mqtt_broker']['port']
    client_id = f"{MQTT_CLIENT_ID_PREFIX}{os.getpid()}"

    client = mqtt.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Optional: Add username/password authentication if your broker requires it
    # client.username_pw_set(username="your_username", password="your_password")

    logging.info(f"Attempting to connect to MQTT broker at {broker_host}:{broker_port}")
    try:
        client.connect(broker_host, broker_port, MQTT_KEEPALIVE_SECONDS)
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
            
            time.sleep(MAIN_LOOP_SLEEP_SECONDS) 
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    finally:
        client.loop_stop() # Stop the network loop
        client.disconnect()
        logging.info("MQTT client disconnected. Server stopped.") 