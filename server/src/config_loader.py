import json
import logging
import os

# Determine the absolute path to the directory containing this file
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Default config path relative to this file's directory
_DEFAULT_CONFIG_PATH = os.path.join(_CURRENT_DIR, 'config.json')

def load_config(config_path=None):
    """Loads configuration from a JSON file.

    Args:
        config_path: Optional path to the config file.
                     If None, defaults to 'config.json' in the same
                     directory as this script.
    """
    if config_path is None:
        config_path = _DEFAULT_CONFIG_PATH

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            logging.debug(f"Configuration loaded successfully from: {config_path}")
            return config_data
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from configuration file {config_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred loading config {config_path}: {e}")
        raise 