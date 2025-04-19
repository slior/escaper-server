import logging
import os

def setup_logging(log_file_path):
    """Configures logging based on the provided file path."""
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            print(f"Created log directory: {log_dir}") # Use print for setup messages
        except OSError as e:
            print(f"Error creating log directory {log_dir}: {e}")
            # Fallback or exit? For now, logging might fail to write to file.

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path), # Log to file
            logging.StreamHandler()          # Log to console
        ]
    )
    logging.info(f"Logging configured. Log file: {log_file_path}") 