import paho.mqtt.client as mqtt
import json
import logging
import os
# import threading
import time


from .config_loader import load_config
from .logging_utils import setup_logging
from .server_state import ServerState
from .control_handler import ControlMessageHandler
from .station_handler import StationEventHandler
from .constants import ( # Import necessary constants
    SESSION_STATE_PENDING,
    MQTT_TOPIC_SERVER_CONTROL, MQTT_TOPIC_STATION_BASE
)



# MQTT Configuration
MQTT_CLIENT_ID_PREFIX = "escape-room-server-"
MQTT_KEEPALIVE_SECONDS = 60

# Other Constants
MAIN_LOOP_SLEEP_SECONDS = 1
DEFAULT_LOG_FILE = '/app/logs/server.log' # used if not in config

CONFIG = load_config()

# --- Logging Setup ---
LOG_FILE = CONFIG.get('log_file', DEFAULT_LOG_FILE)
setup_logging(LOG_FILE)
# Ensure setup_logging configures the root logger used by logging.info etc.
# Or get a specific logger: logger = logging.getLogger(__name__)

# --- State Management (In-Memory) ---
SESSION_STATE = SESSION_STATE_PENDING # Initial state
STATION_STATUS = {} # e.g., {"station_5": {"completed": false}, "station_door": {"completed": false}}

# --- Instantiate Handlers ---
# Placed here so they are globally accessible if needed, or before on_message
message_handlers = [ControlMessageHandler(), StationEventHandler()]

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        # Subscribe to topics upon successful connection
        client.subscribe(MQTT_TOPIC_SERVER_CONTROL)
        station_wildcard_topic = f"{MQTT_TOPIC_STATION_BASE}+/event/+" # Matches escaperoom/station/<id>/event/<type>
        client.subscribe(station_wildcard_topic)
        logging.info(f"Subscribed to: {MQTT_TOPIC_SERVER_CONTROL} and {station_wildcard_topic}")
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

def on_message(client, userdata, msg):
    # Make state variables accessible for update
    global SESSION_STATE, STATION_STATUS, CONFIG

    logging.debug(f"Received message: {msg.topic} - {msg.payload}")
    topic = msg.topic
    payload, payload_str = _parse_message_payload(msg) # Keep payload_str for logging if needed
    if payload is None:
        logging.debug(f"Ignoring message on topic {topic} due to parsing error.")
        return # Error already logged in _parse_message_payload

    # Create current state object
    # Pass the logging module, assuming setup_logging configured the root logger
    current_server_state = ServerState(
        session_state=SESSION_STATE,
        station_status=STATION_STATUS,
        config=CONFIG,
        logger=logging # Pass the configured logging module/logger
    )

    message_handled = False
    for handler in message_handlers:
        try: # Add try-except around handler calls for robustness
            if handler.can_handle(topic, payload, current_server_state):
                logging.debug(f"Message on topic '{topic}' will be handled by {type(handler).__name__}")
                # Handle the message and get the potentially updated state
                next_server_state = handler.handle(topic, payload, client, current_server_state)

                # Check if the state object reference changed. If so, update globals.
                # This relies on handlers returning the *original* object if no changes occurred.
                if next_server_state is not current_server_state:
                    logging.debug(f"State updated by {type(handler).__name__}. Updating global state.")
                    SESSION_STATE = next_server_state.session_state
                    STATION_STATUS = next_server_state.station_status
                    CONFIG = next_server_state.config # Update global config if handler changed it
                else:
                    logging.debug(f"Handler {type(handler).__name__} processed message but did not change state.")


                message_handled = True
                break # Stop after the first handler processes the message
        except Exception as e:
            logging.exception(f"Error during handling message on topic {topic} by {type(handler).__name__}: {e}")
            # Decide if we should continue trying other handlers or stop. Stopping for now.
            message_handled = True # Mark as handled to prevent "unhandled" log, error logged instead
            break


    # Log if no handler processed the message
    if not message_handled:
        logging.warning(f"Received message on unhandled topic: {topic} or no handler found - Payload: {payload_str}")


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