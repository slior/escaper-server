from typing import Protocol, Dict, Any
import logging
import paho.mqtt.client as mqtt # Import for type hinting client

# Import ServerState using relative import
from .server_state import ServerState

class MessageHandler(Protocol):
    """
    Defines the interface for message handlers.

    Each handler is responsible for determining if it can process a given 
    MQTT message and then performing the necessary actions, returning an updated
    server state if modifications were made.
    """

    def can_handle(self, topic: str, payload: Dict[str, Any], server_state: ServerState) -> bool:
        """
        Determines if this handler can process the given message.

        Args:
            topic (str): The MQTT topic the message was received on.
            payload (Dict[str, Any]): The decoded JSON payload of the message.
            server_state (ServerState): The current state of the server.

        Returns:
            bool: True if the handler can process this message, False otherwise.
        """
        ...

    def handle(self, topic: str, payload: Dict[str, Any], client: mqtt.Client, server_state: ServerState) -> ServerState:
        """
        Processes the message and updates the server state if necessary.

        Args:
            topic (str): The MQTT topic the message was received on.
            payload (Dict[str, Any]): The decoded JSON payload of the message.
            client (mqtt.Client): The MQTT client instance (for publishing responses, etc.).
            server_state (ServerState): The current state of the server.

        Returns:
            ServerState: The potentially updated server state. If the handler modifies
                       the state (e.g., session state, station status, config), 
                       it MUST return a *new* ServerState instance. If no changes
                       are made, it MUST return the original `server_state` instance.
                       Handlers MUST NOT modify the input `server_state` object in place.
        """
        ... 