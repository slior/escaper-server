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
    *   Open a terminal in the project root directory (`escape_room_server`).
    *   Run:
        ```bash
        docker-compose up -d mqtt_broker
        ```
    *   This starts the Mosquitto broker in the background.
    *   To view broker logs: `docker-compose logs -f mqtt_broker`

2.  **Start Python Server:**
    *   Open another terminal in the project root directory OR use the same one.
    *   **Activate the virtual environment** if it's not already active:
        ```bash
        source .venv/bin/activate
        ```
    *   Navigate to the `server` directory:
        ```bash
        cd server
        ```
    *   Run the server script **as a module**:
        ```bash
        python3 -m src.server
        ```
    *   The server will connect to `localhost:1883` and start listening. Logs will appear in the console and be written to the file specified in `src/config.json` (relative to the `src` directory).

## Stopping the Server

1.  **Stop Python Server:** Press `Ctrl+C` in the terminal where `python3 -m src.server` is running.
2.  **Stop MQTT Broker:**
    ```bash
    docker-compose down
    ```
    *(This stops and removes the `mqtt_broker` container)*

## Testing

### Manual Testing

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

### Unit Tests

The project includes unit tests for the server's message handling logic.

1.  **Open a terminal** in the project root directory (`escape_room_server`).
2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
3.  **Set the PYTHONPATH:** This tells Python where to find the `src` code when running tests from the root.
    *   Linux/macOS:
        ```bash
        export PYTHONPATH=$PYTHONPATH:./server
        ```
    *   Windows (Command Prompt):
        ```bash
        set PYTHONPATH=%PYTHONPATH%;./server
        ```
    *   Windows (PowerShell):
        ```bash
        $env:PYTHONPATH += ";./server"
        ```
    *   *Note: You need to set this variable in the terminal session where you run the tests.* 
4.  **Run the tests:**
    ```bash
    python3 -m unittest discover server/tests
    ```
    *   The test results will be printed to the console.
