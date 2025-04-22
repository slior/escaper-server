import logging
from typing import Dict, Any

class ServerState:
    """
    Represents the immutable state of the server at a specific point in time.

    Attributes:
        session_state (str): The current state of the escape room session 
                             (e.g., PENDING, RUNNING, STOPPED).
        station_status (Dict[str, Any]): A dictionary tracking the status of 
                                        each station. The structure depends on
                                        station implementation.
        config (Dict[str, Any]): The currently loaded server configuration 
                                 dictionary.
        logger (logging.Logger): The logger instance used by the server.
    """
    def __init__(self, 
                 session_state: str, 
                 station_status: Dict[str, Any], 
                 config: Dict[str, Any], 
                 logger: logging.Logger):
        """
        Initializes a new ServerState instance.

        Args:
            session_state (str): The session state.
            station_status (Dict[str, Any]): The station status dictionary.
            config (Dict[str, Any]): The server configuration dictionary.
            logger (logging.Logger): The logger instance.
        """
        self.session_state = session_state
        self.station_status = station_status
        self.config = config
        self.logger = logger

    # Consider adding methods for creating modified copies if needed, 
    # promoting immutability, e.g.:
    # def with_session_state(self, new_state: str) -> 'ServerState':
    #     return ServerState(new_state, self.station_status, self.config, self.logger)
    # etc. 
    # For now, handlers will create new instances directly as per the plan. 