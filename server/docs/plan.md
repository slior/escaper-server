# Implementation Plan

This document summarizes the plan for implementing the Escape Room Server based on the agreed specifications.

1.  **Setup:**
    *   Utilize Docker and `docker-compose` to manage the environment.
    *   Include two services:
        *   `mqtt_broker`: Running the standard `eclipse-mosquitto` image.
        *   `escape_room_server`: A custom Python application built via a `Dockerfile`.

2.  **MQTT Communication:**
    *   **Broker:** Hosted by the `mqtt_broker` service within Docker.
    *   **Topics:**
        *   Incoming Events: `escaperoom/station/<station_id>/event/<event_type>`
        *   Server Control: `escaperoom/server/control/session`
    *   **Message Format:** JSON.

3.  **Audio Playback:**
    *   Handled locally by the Python server application running inside its Docker container.
    *   Use the `playsound` Python library.
    *   Audio files will be included within the `escape_room_server` Docker image (mounted via a volume for easy updates).
    *   Audio playback logic will be modular and executed in separate threads to avoid blocking.

4.  **Logic Implementation:**
    *   Core control flow (e.g., "IF event X THEN action Y") will be **hardcoded** within the main Python script (`server.py`).
    *   Specific parameters (thresholds, station IDs, sensor names, audio filenames) will be externalized into a `config.json` file.

5.  **Configuration:**
    *   A `config.json` file will store configurable parameters like MQTT broker details, audio paths, log file paths, and station/sensor-specific settings (e.g., thresholds, sounds).

6.  **State Management:**
    *   Session state (e.g., `PENDING`, `RUNNING`) and station completion status will be maintained **in memory** within the Python application.
    *   State will be lost upon server restart for this initial version.
    *   Code structure will anticipate potential future file-based state persistence.
    *   Session start/stop triggered via MQTT messages to `escaperoom/server/control/session`.

7.  **Runtime & Operation:**
    *   Target environment: Docker on Unix-like systems (including WSL).
    *   The server will be runnable via `docker-compose`.
    *   Logging will be directed to both standard output (console) and a dedicated log file within the container (mounted via a volume).

8.  **Directory Structure:**
    *   A `src/` directory will contain the Python server code (`server.py`), `Dockerfile`, `requirements.txt`, `config.json`, and an `audio/` subdirectory.
    *   A `logs/` directory will be mapped for log files.
    *   `docker-compose.yml` and `README.md` will reside in the project root. 