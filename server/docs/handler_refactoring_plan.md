# Revised Plan: Message Handler Refactoring

1.  **Define `ServerState` Class:**
    *   Create a new file `src/server_state.py`.
    *   Define a class `ServerState` in this file.
    *   This class will have attributes for the core server state components:
        *   `session_state: str`
        *   `station_status: dict`
        *   `config: dict`
        *   `logger: logging.Logger`
    *   The `__init__` method will accept these values and assign them. Consider adding basic type checks or validation if necessary.

2.  **Define `MessageHandler` Interface:**
    *   Create a new file `src/message_handler_interface.py`.
    *   Import the `ServerState` class.
    *   Define an abstract base class (using `abc.ABC`) or a `typing.Protocol` named `MessageHandler`.
    *   This interface will define the methods:
        *   `can_handle(self, topic: str, payload: dict, server_state: ServerState) -> bool`: Determines if the handler can process the given message. Receives topic, payload, and the *current* `ServerState` instance.
        *   `handle(self, topic: str, payload: dict, client, server_state: ServerState) -> ServerState`: Executes the handling logic. Receives the same arguments as `can_handle` plus the MQTT `client` instance.
            *   **Crucially:** This method **must** return a `ServerState` instance.
            *   If the handler modifies the state (e.g., changes session state, updates station status, reloads config), it **must** create and return a *new* `ServerState` instance containing the updated values. Unchanged state components should be copied from the input `server_state`.
            *   If the handler does *not* modify the state, it **must** return the original `server_state` instance it received. Handlers **must not** modify the input `server_state` object in place.

3.  **Refactor `control_handler.py`:**
    *   Import `MessageHandler` and `ServerState`.
    *   Create a class `ControlMessageHandler` that implements `MessageHandler`.
    *   Implement `can_handle` to return `True` if the `topic` matches `MQTT_TOPIC_SERVER_CONTROL`, using the input `server_state` if needed.
    *   Implement `handle`:
        *   It accepts `server_state: ServerState`.
        *   It performs the logic currently in `handle_control_message`.
        *   Based on the action, it calculates the `new_session_state`, `new_station_status`, and potentially `reloaded_config`.
        *   It **creates and returns a *new* `ServerState` instance** using these calculated values and the `logger` from the input `server_state`. If `reload_config` occurred, the *new* `config` is used; otherwise, the `config` from the input `server_state` is used.

4.  **Refactor `station_handler.py`:**
    *   Import `MessageHandler` and `ServerState`.
    *   Create a class `StationEventHandler` that implements `MessageHandler`.
    *   Implement `can_handle`:
        *   It accepts `server_state: ServerState`.
        *   Performs the topic structure check (currently in `server.py`).
        *   Checks if `server_state.session_state == SESSION_STATE_RUNNING`.
    *   Implement `handle`:
        *   It accepts `server_state: ServerState`.
        *   Encapsulates the logic currently in `handle_station_event`, accessing config, status, and logger via `server_state.config`, `server_state.station_status`, and `server_state.logger`.
        *   If the logic determines a station's status needs updating:
            *   Create a *copy* of `server_state.station_status`.
            *   Modify the *copy*.
            *   **Create and return a *new* `ServerState` instance** with the *copied and modified* `station_status`, and the original `session_state`, `config`, and `logger` from the input `server_state`.
        *   If no state change occurs (e.g., event condition not met, no status update needed), it **returns the original input `server_state` instance**.

5.  **Update `server.py`:**
    *   Import `ServerState`, `ControlMessageHandler`, and `StationEventHandler`.
    *   Remove direct imports of `handle_station_event` and `handle_control_message`.
    *   Create the list `message_handlers = [ControlMessageHandler(), StationEventHandler()]`.
    *   Modify the `on_message` function:
        *   After parsing the payload, create the initial `current_server_state = ServerState(session_state=SESSION_STATE, station_status=STATION_STATUS, config=CONFIG, logger=logging)`.
        *   Iterate through `message_handlers`.
        *   For each `handler`, call `handler.can_handle(topic, payload, current_server_state)`.
        *   If `can_handle` returns `True`:
            *   Call `next_server_state = handler.handle(topic, payload, client, current_server_state)`.
            *   **Crucially:** Update the global state variables *from the returned state*:
                *   `SESSION_STATE = next_server_state.session_state`
                *   `STATION_STATUS = next_server_state.station_status`
                *   `CONFIG = next_server_state.config`
            *   Set `message_handled = True` and `break` the loop.
        *   After the loop, if `not message_handled`, log the warning.
    *   Remove the now redundant `_handle_control_message_internal` and `_handle_station_event_internal` functions.

## Implementation Log

- Step 1: Defined `ServerState` class in `src/server_state.py`. (Pre-existing - 2024-07-26)
- Step 2: Defined `MessageHandler` interface in `src/message_handler_interface.py`. (Pre-existing - 2024-07-26)
- Step 3: Refactored `control_handler.py` into `ControlMessageHandler` class. Created `server/src/constants.py` and updated imports accordingly. Removed old `handle_control_message` function. (2024-07-26)
- Step 4: Refactored `station_handler.py` into `StationEventHandler` class implementing `MessageHandler`. Moved topic structure and session state checks into `can_handle`. Ensured state immutability in `handle` using `copy.deepcopy`. Added `MQTT_TOPIC_STATION_BASE` to `constants.py`. Removed old `handle_station_event` function. (2024-07-26)
- Step 5: Updated `server.py`. Imported handlers, `ServerState`, constants. Removed old handlers/helpers/local constants. Instantiated handlers. Modified `on_message` to use handler loop, create `ServerState`, update global state based on returned state. Updated `on_connect` subscriptions. (2024-07-26)
- Step 6: Updated unit tests in `server/tests/test_server_message_handling.py`. Refactored tests to mock `server.message_handlers` list instead of patching individual functions. Adjusted mock handler `handle` methods to return mock `ServerState` objects or the original state to simulate state changes. Updated assertions to check mock calls and final global state. Removed obsolete tests targeting old internal functions. (2024-07-26)
