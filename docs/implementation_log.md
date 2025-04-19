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