# Configuration Hot-Reloading

This document describes the process for dynamically reloading the server's configuration (`config.json`) while it is running, triggered by a specific MQTT control message.

## Overview

The server supports reloading its configuration without requiring a restart. This is useful for applying changes to station behavior, MQTT settings (though broker changes still require a restart), or other parameters defined in `config.json` on-the-fly.

The reload is triggered by sending an MQTT message to the control topic:

*   **Topic:** `escaperoom/server/control/session`
*   **Payload:** `{"action": "reload_config"}`

## Detailed Flow

1.  **Message Reception:** The server receives an MQTT message on the `escaperoom/server/control/session` topic.
2.  **Control Handler Invocation:** The `on_message` function in `server.py` identifies the topic and passes the message payload to the `handle_control_message` function in `control_handler.py`.
3.  **Action Check:** `handle_control_message` checks if the `action` field in the payload is `reload_config`.
4.  **Session State Check:**
    *   It verifies if the current `SESSION_STATE` is `"RUNNING"`.
    *   **If not `RUNNING`:** A warning is logged stating that the reload command is ignored because the session must be active. The function returns the existing state and `None` for the configuration.
    *   **If `RUNNING`:** The process continues to the reload step.
5.  **Configuration Reload Attempt:**
    *   The `handle_control_message` function calls `load_config()` (from `config_loader.py`) to attempt reloading the configuration from `config.json`.
    *   This call is wrapped in a `try...except` block.
6.  **Reload Outcome:**
    *   **Success:** If `load_config()` successfully reads and parses `config.json`, it returns the new configuration dictionary.
        *   `handle_control_message` logs an info message: "Configuration successfully reloaded."
        *   It returns the current `SESSION_STATE`, current `STATION_STATUS`, and the *new configuration dictionary* to `on_message`.
    *   **Failure (File Not Found or JSON Error):** If `load_config()` encounters a `FileNotFoundError` (config file missing) or `json.JSONDecodeError` (invalid JSON format):
        *   `load_config` raises the exception.
        *   The `except` block in `handle_control_message` catches the specific exception.
        *   An error message is logged detailing the failure (e.g., "Failed to reload configuration: [Errno 2] No such file or directory: 'config.json'").
        *   The server *does not crash*. The function returns the current `SESSION_STATE`, current `STATION_STATUS`, and `None` for the configuration, indicating the reload failed and the existing configuration remains active.
    *   **Failure (Other Unexpected Error):** If any other unexpected exception occurs during the reload attempt, it's caught by a general `except Exception` block, an error is logged, and the function returns the current state and `None` for the configuration.
7.  **Global Configuration Update (in `server.py`):**
    *   Back in the `on_message` function within `server.py`.
    *   It receives the tuple `(new_session_state, new_station_status, reloaded_config)` from `handle_control_message`.
    *   It updates `SESSION_STATE` and `STATION_STATUS` as usual.
    *   It checks if the third element, `reloaded_config`, is *not* `None`.
    *   **If `reloaded_config` is a dictionary (reload was successful):**
        *   The global `CONFIG` variable (used throughout the server) is updated: `CONFIG = reloaded_config`.
        *   An info message is logged: "Server configuration has been reloaded."
    *   **If `reloaded_config` is `None` (reload failed or was skipped):**
        *   The global `CONFIG` variable remains unchanged.

```mermaid
sequenceDiagram
    participant Client
    participant Broker
    participant Server as Server (on_message)
    participant ControlHandler as control_handler.py
    participant ConfigLoader as config_loader.py
    participant State as Global State (SESSION_STATE, CONFIG)

    Client->>Broker: Publish (topic: .../control/session, payload: {"action":"reload_config"})
    Broker->>+Server: MQTT Message
    Server->>+ControlHandler: handle_control_message(payload, SESSION_STATE, STATION_STATUS)
    ControlHandler->>State: Read SESSION_STATE
    alt Session is RUNNING
        ControlHandler->>ControlHandler: Log "Attempting to reload..."
        ControlHandler->>+ConfigLoader: load_config()
        alt load_config() succeeds
            ConfigLoader-->>-ControlHandler: Return new_config_dict
            ControlHandler->>ControlHandler: Log "Configuration successfully reloaded."
            ControlHandler-->>-Server: Return (SESSION_STATE, STATION_STATUS, new_config_dict)
            Server->>State: Update global CONFIG = new_config_dict
            Server->>Server: Log "Server configuration has been reloaded."
        else load_config() fails (FileNotFound, JSONDecodeError)
            ConfigLoader-->>-ControlHandler: Raise Exception
            ControlHandler->>ControlHandler: Catch Exception
            ControlHandler->>ControlHandler: Log Error "Failed to reload configuration: ..."
            ControlHandler-->>-Server: Return (SESSION_STATE, STATION_STATUS, None)
            Server->>Server: Check if reloaded_config is None (it is)
            Server->>Server: No update to global CONFIG
        else load_config() fails (Other Exception)
            ConfigLoader-->>-ControlHandler: Raise Exception
            ControlHandler->>ControlHandler: Catch Exception
            ControlHandler->>ControlHandler: Log Error "An unexpected error occurred..."
            ControlHandler-->>-Server: Return (SESSION_STATE, STATION_STATUS, None)
            Server->>Server: Check if reloaded_config is None (it is)
            Server->>Server: No update to global CONFIG
        end
    else Session is NOT RUNNING
        ControlHandler->>ControlHandler: Log Warning "Ignoring reload_config command..."
        ControlHandler-->>-Server: Return (SESSION_STATE, STATION_STATUS, None)
        Server->>Server: Check if reloaded_config is None (it is)
        Server->>Server: No update to global CONFIG
    end
    Server-->>Broker: Ack (implicitly)

```

## Important Considerations

*   **Error Handling:** The reload mechanism is designed to be resilient. Errors during file reading or JSON parsing will be logged, but they will not stop the server. The server will continue operating with the last known valid configuration.
*   **Scope of Reload:** Only the parameters read from `config.json` are reloaded. For instance, changes to the MQTT broker address or port in `config.json` will be loaded into the `CONFIG` object but will *not* cause the MQTT client to automatically reconnect to a new broker. A server restart is required for such fundamental changes.
*   **State Requirement:** The reload only functions when the session is actively `RUNNING`. 