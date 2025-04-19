import logging
import sys
import os

def setup_logging(log_file_path):
    """Configures logging more robustly, adding handlers directly."""
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            print(f"Created log directory: {log_dir}") # Use print for setup messages
        except OSError as e:
            print(f"Error creating log directory {log_dir}: {e}")
            # Logging to file might fail.

    # Define formatter
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set minimum level for the logger

    # --- File Handler ---
    # Check if a file handler already exists to avoid duplicates
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_file_path) for h in root_logger.handlers):
        try:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(log_formatter)
            file_handler.setLevel(logging.INFO) # Handler level can be different
            root_logger.addHandler(file_handler)
        except Exception as e:
             print(f"Error setting up file logging for {log_file_path}: {e}")
    else:
        print(f"File handler for {log_file_path} already configured.")

    # --- Console (Stream) Handler ---
    # Check if a stream handler already exists
    if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout) # Explicitly use stdout
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
    else:
        print("Console handler already configured.")

    # Prevent root logger from propagating to parent loggers if any exist (less likely here)
    # root_logger.propagate = False

    # Check handlers after setup
    handler_types = [type(h).__name__ for h in root_logger.handlers]
    logging.info(f"Logging configured. Log level: INFO. Handlers: {handler_types}. Log file: {log_file_path}")

# Example of how setup_logging might be called in server.py:
# LOG_FILE = CONFIG.get('log_file', DEFAULT_LOG_FILE)
# setup_logging(LOG_FILE) 