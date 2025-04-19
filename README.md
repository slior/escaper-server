# Escape Room MQTT Server

This project provides a simple MQTT-based server application designed to manage events and trigger actions (like playing sounds) for an escape room setup.

## Features

*   Listens for events from escape room stations via MQTT.
*   Manages the overall escape room session state (PENDING, RUNNING, STOPPED).
*   Triggers local audio playback based on configurable rules.
*   Uses Docker Compose to run the MQTT broker.
*   The server script runs directly on the host (designed for WSL/Linux).
*   Logs events to both console and a file.

## Prerequisites

*   **WSL (Windows Subsystem for Linux):** Recommended setup environment on Windows.
*   **Docker:** For running the MQTT Broker. ([Install Docker](https://docs.docker.com/get-docker/))
*   **Docker Compose:** Included with Docker Desktop. ([Install Docker Compose](https://docs.docker.com/compose/install/))
*   **Python 3:** (e.g., 3.10 or later) installed within WSL.
*   **Git:** For cloning the repository.
*   **System Packages (WSL/Debian/Ubuntu):** Required for audio playback.
    ```bash
    sudo apt update && sudo apt install -y python3-gi gir1.2-gstreamer-1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-tools python3-pip python3-venv
    ```

## Directory Structure

```
.
├── docs/
│   ├── spec.md           # Original requirements specification
│   └── plan.md           # Implementation plan summary
├── src/
│   ├── server.py         # Main Python server application
│   ├── config.json       # Configuration file for the server
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # (Optional: For reference or future containerization)
├── logs/                 # Directory for log files (created automatically by script)
├── .venv/                # Python virtual environment directory
├── docker-compose.yml    # Docker Compose configuration (for MQTT broker)
├── mosquitto.conf        # Configuration for MQTT broker
└── README.md             # This file
```

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd escape_room_server
    ```

2.  **Place Audio Files:**
    *   Create a directory accessible from your WSL environment to store your audio files (e.g., .wav, .mp3).
    *   **Example (on Windows):** Create `C:\tmp\audio`.
    *   Place your audio files (e.g., `nearby_alert.wav`, `door_open_sound.wav`) in this directory.

3.  **Configure Server:**
    *   Open `src/config.json`.
    *   Ensure `mqtt_broker.host` is set to `"localhost"` (or `"127.0.0.1"`).
    *   Set `audio_base_path` to the **WSL path** of the directory containing your audio files. **Important:** Use the Linux path as seen by WSL (e.g., `/mnt/c/tmp/audio/` for `C:\tmp\audio`).
    *   Verify `log_file` is set to a relative path like `"../logs/server.log"`.
    *   Update `station_configs` to match your specific stations, sensors, event types, conditions, and the corresponding audio filenames (must match the filenames in your audio directory).

4.  **Create Python Virtual Environment:**
    *   In the project root directory (`escape_room_server`) within your WSL terminal:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
        *(Your terminal prompt should now show `(.venv)`)*

5.  **Install Python Dependencies:**
    *   While the virtual environment is active:
        ```bash
        pip install -r src/requirements.txt
        ```

6.  **Prepare Log Directory:**
    *   Ensure the user running the script has permission to create/write to the log directory specified in `config.json`.
    *   If `log_file` is `../logs/server.log`, run from the project root:
        ```bash
        mkdir -p logs
        sudo chown -R $(whoami):$(whoami) logs
        ```

## Running the Server

1.  **Start MQTT Broker:**
    *   Open a terminal in the project root directory (where `docker-compose.yml` is located).
    *   Run:
        ```bash
        docker-compose up -d mqtt_broker
        ```
    *   This starts only the Mosquitto broker in the background.
    *   To view broker logs: `docker-compose logs -f mqtt_broker`

2.  **Start Python Server:**
    *   Open another terminal in the project root directory OR use the same one.
    *   **Activate the virtual environment** if it's not already active:
        ```bash
        source .venv/bin/activate
        ```
    *   Navigate to the source directory:
        ```bash
        cd src
        ```
    *   Run the server script:
        ```bash
        python server.py
        ```
    *   The server will connect to `localhost:1883` and start listening. Logs will appear in the console and be written to the file specified in `config.json`.

## Stopping the Server

1.  **Stop Python Server:** Press `Ctrl+C` in the terminal where `python server.py` is running.
2.  **Stop MQTT Broker:**
    ```bash
    docker-compose down
    ```
    *(This stops and removes the `mqtt_broker` container)*

## Testing

You can test the server by sending MQTT messages using an MQTT client (like `mosquitto_pub` command-line tool installed in WSL or a GUI client like MQTT Explorer connected to `localhost:1883`).

**1. Start the Session:**

*   Publish a message to start the session:
    ```bash
    mosquitto_pub -h localhost -p 1883 -t "escaperoom/server/control/session" -m '{"action": "start"}'
    ```
*   Check the Python server's terminal logs; you should see "Escape Room Session STARTED".

**2. Trigger an Event (Example: Beacon Proximity):**

*   Assuming `config.json` has the `station_5` beacon example and `nearby_alert.wav` exists in your audio directory:
    ```bash
    # This message should trigger the sound if range <= 5
    mosquitto_pub -h localhost -p 1883 -t "escaperoom/station/station_5/event/beacon_proximity" -m '{"sensor": "beacon_proximity_1", "range": 3}'

    # This message should NOT trigger the sound
    mosquitto_pub -h localhost -p 1883 -t "escaperoom/station/station_5/event/beacon_proximity" -m '{"sensor": "beacon_proximity_1", "range": 8}'
    ```
*   Check the Python server logs for messages indicating the trigger and audio playback (you should hear the sound via your host audio).

**3. Trigger another Event (Example: Door Open):**

*   Assuming `config.json` has the `station_door` example and `door_open_sound.wav` exists:
    ```bash
    # This message should trigger the sound if trigger_value is "OPEN"
    mosquitto_pub -h localhost -p 1883 -t "escaperoom/station/station_door/event/door_status" -m '{"sensor": "main_door_switch", "status": "OPEN"}'

    # This message should NOT trigger the sound
    mosquitto_pub -h localhost -p 1883 -t "escaperoom/station/station_door/event/door_status" -m '{"sensor": "main_door_switch", "status": "CLOSED"}'
    ```
*   Check the server logs.

**4. Stop the Session:**

*   Publish a message to stop the session:
    ```bash
    mosquitto_pub -h localhost -p 1883 -t "escaperoom/server/control/session" -m '{"action": "stop"}'
    ```
*   Check the server logs for the "Escape Room Session STOPPED" message.

## Adding New Logic

To add logic for new event types or stations:

1.  **Update `config.json`:** Add new entries under `station_configs` for the new station or sensor, specifying its `event_type`, necessary parameters (like thresholds or trigger values), and the `sound_on_trigger` filename (ensure the audio file exists in your designated audio directory).
2.  **Modify `src/server.py`:**
    *   In the `on_message` function, find the `# --- Hardcoded Logic based on Config ---` section.
    *   Add a new `elif event_type == "your_new_event_type":` block.
    *   Inside this block, add Python code to handle the new event type.
    *   Remember that `play_audio_threaded(sound_file)` expects just the filename, and it will be joined with the `audio_base_path` from `config.json`.

Restart the Python server script (`Ctrl+C`, then `python server.py`) after making changes to `server.py` or `config.json`. 