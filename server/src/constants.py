# Shared constants for the server application
import logging

# --- MQTT Topics ---
MQTT_TOPIC_SERVER_CONTROL = "escaperoom/server/control"
MQTT_TOPIC_STATION_BASE = "escaperoom/station/"

# --- Control Actions ---
ACTION_START = "start"
ACTION_STOP = "stop"
ACTION_RESET = "reset"
ACTION_RELOAD_CONFIG = "reload_config"

# --- Session States ---
SESSION_STATE_RUNNING = "RUNNING"
SESSION_STATE_STOPPED = "STOPPED"
SESSION_STATE_PENDING = "PENDING"

# --- Station Event Types (Placeholder - Define actual events as needed) ---
# Example: EVENT_TYPE_PUZZLE_SOLVED = "puzzle_solved"
# Example: EVENT_TYPE_STATUS_UPDATE = "status_update"

# --- Logging Configuration (Example) ---
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

