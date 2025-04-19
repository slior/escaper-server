import json
import logging

def load_config(config_path='config.json'):
    """Loads configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        exit(1) # Consider raising an exception instead of exiting
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from configuration file: {config_path}")
        exit(1) # Consider raising an exception instead of exiting 