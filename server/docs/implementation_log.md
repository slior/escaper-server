# Implementation Log

This document summarizes the key changes and troubleshooting steps taken during the setup and debugging of the Escape Room MQTT Server.

## Initial Setup & Issues

The initial setup involved running both the MQTT broker (Mosquitto) and the Python server application within Docker containers using `docker-compose`. Several issues were encountered:

### 1. MQTT Connection Refused

*   **Symptom:** The Python server container failed to connect to the `mqtt_broker` container, logging `MQTT connection failed: [Errno 111] Connection refused`. Connecting via an external client (MQTT Explorer) to `localhost:1883` also failed.
*   **Cause:** The `eclipse-mosquitto:2.0` Docker image used defaults to "local only mode" if no configuration file explicitly defines a listener. This prevents connections from other containers or the host.
*   **Fix:**
    *   Created a `mosquitto.conf` file in the project root with the following content to allow anonymous connections on the standard port:
        ```conf
        listener 1883
        allow_anonymous true
        ```
    *   Updated `docker-compose.yml` to mount this configuration file into the `mqtt_broker` container:
        ```yaml
        services:
          mqtt_broker:
            # ... other settings
            volumes:
              # ... other volumes
              - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
        ```

### 2. Audio File Not Found

*   **Symptom:** When triggering an event that should play sound, the server logged `ERROR - Audio file not found: /mnt/c/tmp/audio/nearby_alert.wav`.
*   **Cause:** The `src/config.json` initially had `"audio_base_path"` set to the Windows/WSL host path (`/mnt/c/tmp/audio/`). However, the Python script inside the container needed the path *within* the container (`/app/audio/`), as defined by the volume mount in `docker-compose.yml`.
*   **Initial Fix Attempt:** Changed `"audio_base_path"` in `config.json` to `"/app/audio/"`.
*   **User Constraint & Final Fix:** The user could not easily place files into the WSL project's `./src/audio` directory. To accommodate this, the fix involved:
    *   Keeping `"audio_base_path"` as `"/app/audio/"` in `config.json`.
    *   Modifying the `docker-compose.yml` volume mount for the `escape_room_server` service to directly map the Windows path (visible via WSL) to the container path:
        ```yaml
        services:
          escape_room_server:
            # ... other settings
            volumes:
              # ... other volumes
              - /mnt/c/tmp/audio:/app/audio # Map audio files from Windows path
        ```

### 3. Log File Permission Denied

*   **Symptom:** When starting the Python server directly in WSL, it failed with `PermissionError: [Errno 13] Permission denied: '/home/lior/dev/escape_room_server/logs/server.log'`.
*   **Cause:** The `logs` directory and/or `server.log` file (located at the project root) were owned by `root:root`, likely due to being created by Docker volume mounts in previous runs. The server script running as the user `lior` did not have permission to write to these files/directory.
*   **Fix:** Changed the ownership of the `logs` directory and its contents back to the user `lior` using the command from the project root:
    ```bash
    sudo chown -R lior:lior logs
    ```

## Current Setup

*   **MQTT Broker:** Runs as a Docker container managed by `docker-compose`.
*   **Python Server:** Runs directly in the WSL environment using a Python virtual environment.
*   **Audio Files:** Located on the Windows host (e.g., `C:\tmp\audio`) and accessed by the Python script via the WSL path (`/mnt/c/tmp/audio`).
*   **Logging:** Log file is created in the `logs` directory at the project root on the host filesystem. 

## Unit Testing Plan

To ensure the reliability of the server's message handling logic, unit tests will be implemented.

*   **Objective:** Verify the correct processing of MQTT control messages and station event messages by the `on_message` function and its helpers in `src/server.py`, based on the logic documented in `message_handling.md`.
*   **Framework:** Python's built-in `unittest` module and `unittest.mock` for mocking dependencies.
*   **Directory Structure:** Tests will reside in a dedicated directory:
    ```
    server/
    ├── src/
    ├── docs/
    └── tests/
        ├── __init__.py
        └── test_server_message_handling.py
    ```
*   **Running Tests:**
    1.  Navigate to the project root (`escape_room_server`).
    2.  Set the `PYTHONPATH` environment variable to include the `server` directory:
        *   Linux/macOS: `export PYTHONPATH=$PYTHONPATH:./server`
        *   Windows (CMD): `set PYTHONPATH=%PYTHONPATH%;./server`
        *   Windows (PS): `$env:PYTHONPATH += ";./server"`
    3.  Run the tests using: `python -m unittest discover server/tests`
*   **Key Areas to Test (`server/tests/test_server_message_handling.py`):**
    *   **Message Parsing:** Valid JSON, invalid JSON, non-UTF-8 payload.
    *   **Control Messages (`_handle_control_message_internal` via `on_message`):**
        *   `start` action (initial and subsequent).
        *   `stop` action.
        *   `reset` action.
        *   `reload` config action.
        *   Unknown actions.
        *   Verify state changes (`SESSION_STATE`, `STATION_STATUS`) and calls to `handle_control_message`.
    *   **Station Events (`_handle_station_event_internal` via `on_message`):**
        *   Events ignored when session is not "RUNNING".
        *   Valid events call `handle_station_event` with correct arguments.
        *   Events with invalid topic format.
    *   **`on_message` Routing:** Ensure correct internal handler (`_handle_control_message_internal` or `_handle_station_event_internal`) is called based on the topic. Test unhandled topics.
    *   **Mocking:** External dependencies (MQTT client, `handle_station_event`, `handle_control_message`, `play_audio_threaded`, config loading, logging) will be mocked using `unittest.mock.patch`. Global state (`SESSION_STATE`, `STATION_STATUS`, `CONFIG`) will be managed or patched within tests. 