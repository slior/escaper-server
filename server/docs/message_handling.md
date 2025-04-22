# MQTT Message Handling Logic (`on_message`)

This document describes the logic implemented within the `on_message` callback function in `src/server.py`, which orchestrates the processing of incoming MQTT messages using a handler-based approach.

## Overview

The `on_message` function serves as the entry point for MQTT messages. Instead of containing all the logic itself, it delegates processing to a list of specialized `MessageHandler` objects. The primary handlers are:

1.  **`ControlMessageHandler`:** Handles messages sent to the `escaperoom/server/control/session` topic (defined in `constants.py` as `MQTT_TOPIC_SERVER_CONTROL`) to manage the overall escape room session state (start, stop, reset).
2.  **`StationEventHandler`:** Handles messages originating from individual stations, published to topics matching the pattern `escaperoom/station/<station_id>/event/<event_type>` (base defined in `constants.py` as `MQTT_TOPIC_STATION_BASE`). These messages trigger actions based on station configurations and the current session state.

The system uses a `ServerState` object to encapsulate the current state (`session_state`, `station_status`, `config`, `logger`) and pass it immutably to handlers. Handlers return a potentially *new* `ServerState` object if changes occurred.

## Detailed Flow

1.  **Message Reception:** An MQTT message arrives from the broker.
2.  **Payload Decoding:**
    *   The `on_message` function calls `_parse_message_payload` to decode the message payload from bytes to UTF-8 and then parse it as JSON.
    *   If either step fails, an error is logged by the helper, and `on_message` returns, stopping processing for that message.
3.  **State Encapsulation:**
    *   An immutable `ServerState` object (`current_server_state`) is created, capturing the current global `SESSION_STATE`, `STATION_STATUS`, `CONFIG`, and the shared `logging` instance.
4.  **Handler Iteration:**
    *   `on_message` iterates through a predefined list of `message_handlers` (e.g., `[ControlMessageHandler(), StationEventHandler()]`).
    *   For each `handler`:
        *   **`can_handle(topic, payload, current_server_state)`:** The handler's `can_handle` method is called. This method checks if the handler is designed to process the message based on the `topic`, `payload`, and potentially the `current_server_state`. For example, `StationEventHandler` checks if the topic structure matches and if the `current_server_state.session_state` is "RUNNING".
        *   **If `can_handle` returns `True`:**
            *   **`handle(topic, payload, client, current_server_state)`:** The handler's `handle` method is invoked. This method contains the specific logic for processing the message (e.g., updating session state for control messages, checking sensor triggers for station events). It receives the `client` instance for potential MQTT publishing and the `current_server_state`.
            *   **State Update:** The `handle` method **must** return a `ServerState` object (`next_server_state`).
                *   If the handler modified the state (e.g., changed session state, updated station status), it creates and returns a *new* `ServerState` instance with the updated values.
                *   If the handler did *not* modify the state, it returns the *original* `current_server_state` object it received.
            *   `on_message` compares the returned `next_server_state` with the original `current_server_state` by object identity (`is not`).
            *   **If the state object changed:** The global variables (`SESSION_STATE`, `STATION_STATUS`, `CONFIG`) are updated with the values from the `next_server_state` object.
            *   The loop is terminated (`break`) as the message has been handled.
        *   **Error Handling:** A `try...except` block surrounds the calls to `can_handle` and `handle` to catch and log exceptions occurring within a handler.
5.  **Unhandled Messages:** If the loop completes without any handler returning `True` from `can_handle`, a warning is logged indicating an unhandled topic or message.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Broker
    participant Server as Server (on_message)
    participant State as Global State (Vars)
    participant Handlers as Handler List
    participant Handler as Specific Handler (e.g., ControlMessageHandler)
    participant ServerStateObj as ServerState (Object)
    participant Audio as Audio Player

    Broker->>+Server: MQTT Message (topic, payload)
    Server->>Server: Decode payload (UTF-8, JSON)
    alt Payload Error
        Server->>Server: Log Error
        Server-->>Broker: Ack (implicitly)
    else Valid Payload
        Server->>State: Read Globals (SESSION_STATE, STATION_STATUS, CONFIG)
        Server->>ServerStateObj: Create current_server_state
        Server->>Handlers: Iterate through message_handlers
        loop For each handler in list
            Server->>Handler: Call can_handle(topic, payload, current_server_state)
            alt can_handle returns True
                Server->>Server: Log "Message will be handled by..."
                Server->>Handler: Call handle(topic, payload, client, current_server_state)
                Handler->>Handler: Execute specific logic (e.g., check action, check sensors)
                opt State Modification Needed
                    Handler->>ServerStateObj: Create next_server_state (with changes)
                else No State Modification
                    Handler-->>Server: Return original current_server_state
                end
                Handler-->>Server: Return next_server_state
                Server->>Server: Compare current_server_state is next_server_state
                alt State Object Changed (is not)
                    Server->>State: Update Globals from next_server_state
                else State Object Unchanged (is)
                     Server->>Server: Log "Handler processed but did not change state"
                end
                Server->>Handlers: break loop
            else can_handle returns False
                Server->>Handlers: Continue loop
            end
        end
        alt Message not handled after loop
             Server->>Server: Log "Unhandled topic"
        end
        Server-->>Broker: Ack (implicitly)
    end

```

## State Management

*   **Global Variables (`SESSION_STATE`, `STATION_STATUS`, `CONFIG`):** These modules-level variables in `server.py` still hold the authoritative current state of the server.
*   **`ServerState` Class (`src/server_state.py`):** An immutable data class used to pass a consistent snapshot of the server's state (`session_state`, `station_status`, `config`, `logger`) to message handlers.
*   **Immutability Pattern:** Handlers receive the `ServerState` object but **must not** modify it directly. If a handler needs to change the state, it **must** create and return a *new* `ServerState` instance containing the modified values. `on_message` then updates the global variables based on this returned object *only if* it's a different object than the one passed in. This promotes clearer state transitions and simplifies testing.
*   **Handler Responsibility:** Each handler is responsible for its specific domain of state modification (e.g., `ControlMessageHandler` modifies `session_state` and `station_status` based on control actions; `StationEventHandler` might modify `station_status` based on events, though this is not fully implemented in the example). Handlers access necessary configuration and current state via the `ServerState` object passed to their `can_handle` and `handle` methods.
*   **Logging:** The `logging` instance is also passed within the `ServerState` object, allowing handlers to log messages consistently. 