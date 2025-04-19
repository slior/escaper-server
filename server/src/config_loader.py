import json
import logging

def load_config(config_path='config.json'):
    """Loads configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise # Re-raise the exception
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from configuration file: {config_path}")
        raise # Re-raise the exception 