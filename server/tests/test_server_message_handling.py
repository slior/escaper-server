import unittest
import json
from unittest.mock import patch, MagicMock, ANY
import logging # Import logging for assertLogs

# Modules to test
from src import server
from src.server_state import ServerState # Import ServerState
from src.constants import ( # Import constants used in tests/setup
    SESSION_STATE_PENDING, SESSION_STATE_RUNNING, SESSION_STATE_STOPPED,
    MQTT_TOPIC_SERVER_CONTROL, MQTT_TOPIC_STATION_BASE
)


# Mock MQTT message class
class MockMQTTMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        # Ensure payload is bytes for the test, matching paho-mqtt
        if isinstance(payload, str):
            self.payload = payload.encode('utf-8')
        else:
            self.payload = payload # Allow pre-encoded bytes

    # No need for decode method here, server._parse_message_payload handles it


class TestServerMessageHandling(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        # Reset state for each test
        server.SESSION_STATE = SESSION_STATE_PENDING
        server.STATION_STATUS = {}
        # Use imported constants for setup clarity
        server.CONFIG = {
            'mqtt_broker': {'host': 'localhost', 'port': 1883},
            'log_file': 'test_server.log', # Example log file
            'station_configs': { # Use station_configs key as used in handler
                'station_test': {
                    'sensor_A': {'event_type': 'test_event'} # Example sensor config
                }
            }
        }
        self.mock_client = MagicMock()
        # Disable logging propagation during tests to avoid clutter
        # logging.disable(logging.CRITICAL)

        # Prepare mock handlers for patching server.message_handlers
        self.mock_control_handler = MagicMock(name="MockControlHandler")
        self.mock_station_handler = MagicMock(name="MockStationHandler")
        # It's often cleaner to patch within each test method
        # self.message_handlers_patch = patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler])
        # self.message_handlers_patch.start()


    def tearDown(self):
        """Clean up after test methods."""
        # If patching was done in setUp, stop it here
        # self.message_handlers_patch.stop()
        # Re-enable logging
        # logging.disable(logging.NOTSET)
        pass # No explicit teardown needed if patching is per-test


    # --- Test Message Parsing ---

    def test_on_message_invalid_json(self):
        """Test that invalid JSON payload is handled gracefully."""
        msg = MockMQTTMessage("some/topic", "{not json")
        # Patch handlers to avoid side effects during parsing test
        with patch('src.server.message_handlers', []), self.assertLogs(level='ERROR') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Could not decode JSON payload" in record.getMessage() for record in log.records))

    def test_on_message_non_utf8(self):
        """Test that non-UTF-8 payload is handled."""
        msg = MockMQTTMessage("some/topic", b'\xff') # Invalid UTF-8 start byte
        with patch('src.server.message_handlers', []), self.assertLogs(level='ERROR') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Could not decode UTF-8 payload" in record.getMessage() for record in log.records))


    # --- Test Control Message Handling ---

    def test_control_start(self):
        """Test START control message triggers control handler and updates state."""
        # Expected resulting state
        expected_state = SESSION_STATE_RUNNING
        expected_status = {} # Start resets status
        expected_config = server.CONFIG # Config unchanged by start

        # Mock the returned ServerState from the handler
        mock_returned_state = MagicMock(spec=ServerState)
        mock_returned_state.session_state = expected_state
        mock_returned_state.station_status = expected_status
        mock_returned_state.config = expected_config

        # Configure mocks for this test
        self.mock_control_handler.can_handle.return_value = True
        self.mock_control_handler.handle.return_value = mock_returned_state
        self.mock_station_handler.can_handle.return_value = False

        payload = json.dumps({"action": "start"})
        msg = MockMQTTMessage(MQTT_TOPIC_SERVER_CONTROL, payload)

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]):
            server.on_message(self.mock_client, None, msg)

        # Assertions
        self.mock_control_handler.can_handle.assert_called_once_with(MQTT_TOPIC_SERVER_CONTROL, json.loads(payload), ANY)
        self.mock_control_handler.handle.assert_called_once_with(MQTT_TOPIC_SERVER_CONTROL, json.loads(payload), self.mock_client, ANY)
        # Assert that the ServerState passed to handle had the initial state
        call_args, _ = self.mock_control_handler.handle.call_args
        passed_state = call_args[3]
        self.assertIsInstance(passed_state, ServerState)
        self.assertEqual(passed_state.session_state, SESSION_STATE_PENDING)

        self.mock_station_handler.can_handle.assert_not_called() # Should break loop after control handler
        self.mock_station_handler.handle.assert_not_called()

        self.assertEqual(server.SESSION_STATE, expected_state)
        self.assertEqual(server.STATION_STATUS, expected_status)
        self.assertEqual(server.CONFIG, expected_config)


    def test_control_stop(self):
        """Test STOP control message."""
        server.SESSION_STATE = SESSION_STATE_RUNNING # Start in running state
        expected_state = SESSION_STATE_STOPPED
        expected_status = {} # Stop clears status
        expected_config = server.CONFIG

        mock_returned_state = MagicMock(spec=ServerState)
        mock_returned_state.session_state = expected_state
        mock_returned_state.station_status = expected_status
        mock_returned_state.config = expected_config

        self.mock_control_handler.can_handle.return_value = True
        self.mock_control_handler.handle.return_value = mock_returned_state
        self.mock_station_handler.can_handle.return_value = False

        payload = json.dumps({"action": "stop"})
        msg = MockMQTTMessage(MQTT_TOPIC_SERVER_CONTROL, payload)

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]):
            server.on_message(self.mock_client, None, msg)

        self.mock_control_handler.handle.assert_called_once()
        # Assert that the ServerState passed to handle had the RUNNING state
        call_args, _ = self.mock_control_handler.handle.call_args
        passed_state = call_args[3]
        self.assertEqual(passed_state.session_state, SESSION_STATE_RUNNING)

        self.assertEqual(server.SESSION_STATE, expected_state)
        self.assertEqual(server.STATION_STATUS, expected_status)


    def test_control_reset(self):
        """Test RESET control message."""
        server.SESSION_STATE = SESSION_STATE_RUNNING
        server.STATION_STATUS = {"some_station": "done"}
        expected_state = SESSION_STATE_PENDING
        expected_status = {} # Reset clears status
        expected_config = server.CONFIG

        mock_returned_state = MagicMock(spec=ServerState)
        mock_returned_state.session_state = expected_state
        mock_returned_state.station_status = expected_status
        mock_returned_state.config = expected_config

        self.mock_control_handler.can_handle.return_value = True
        self.mock_control_handler.handle.return_value = mock_returned_state
        self.mock_station_handler.can_handle.return_value = False

        payload = json.dumps({"action": "reset"})
        msg = MockMQTTMessage(MQTT_TOPIC_SERVER_CONTROL, payload)

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]):
            server.on_message(self.mock_client, None, msg)

        self.mock_control_handler.handle.assert_called_once()
        call_args, _ = self.mock_control_handler.handle.call_args
        passed_state = call_args[3]
        self.assertEqual(passed_state.session_state, SESSION_STATE_RUNNING)
        self.assertEqual(passed_state.station_status, {"some_station": "done"})

        self.assertEqual(server.SESSION_STATE, expected_state)
        self.assertEqual(server.STATION_STATUS, expected_status)

    def test_control_reload(self):
        """Test RELOAD control message updates config."""
        server.SESSION_STATE = SESSION_STATE_RUNNING # Reload only happens when running
        initial_config = server.CONFIG.copy()
        initial_state = server.SESSION_STATE
        initial_status = server.STATION_STATUS.copy()
        new_config_dict = {"reloaded": True, "mqtt_broker": initial_config['mqtt_broker']} # Simulate reloaded config

        # Mock handler returns state with NEW config
        mock_returned_state = MagicMock(spec=ServerState)
        mock_returned_state.session_state = initial_state # State/Status unchanged by reload itself
        mock_returned_state.station_status = initial_status
        mock_returned_state.config = new_config_dict

        self.mock_control_handler.can_handle.return_value = True
        self.mock_control_handler.handle.return_value = mock_returned_state
        self.mock_station_handler.can_handle.return_value = False

        payload = json.dumps({"action": "reload_config"}) # Use correct action name
        msg = MockMQTTMessage(MQTT_TOPIC_SERVER_CONTROL, payload)

        # No specific log message for reload in on_message now, check handler log if needed
        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]):
             server.on_message(self.mock_client, None, msg)

        self.mock_control_handler.handle.assert_called_once()
        self.assertEqual(server.CONFIG, new_config_dict) # Check global config updated
        self.assertEqual(server.SESSION_STATE, initial_state) # Check state unchanged
        self.assertEqual(server.STATION_STATUS, initial_status) # Check status unchanged

        # Restore original config to not affect other tests
        server.CONFIG = initial_config

    def test_control_unknown_action_no_state_change(self):
        """Test unknown control action results in no state change."""
        initial_state = server.SESSION_STATE
        initial_status = server.STATION_STATUS.copy()
        initial_config = server.CONFIG.copy()

        # Configure mock handler to return the *original* state object
        # Use side_effect to access the state passed into handle
        def return_original_state(topic, payload, client, state):
            # Optionally add checks here: self.assertEqual(state.session_state, initial_state)
            return state # Return the exact object passed in

        self.mock_control_handler.can_handle.return_value = True
        self.mock_control_handler.handle.side_effect = return_original_state
        self.mock_station_handler.can_handle.return_value = False

        payload = json.dumps({"action": "invalid_action"})
        msg = MockMQTTMessage(MQTT_TOPIC_SERVER_CONTROL, payload)

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]), self.assertLogs(level='DEBUG') as log: # Check for debug log indicating no change
             server.on_message(self.mock_client, None, msg)
             self.assertTrue(any("processed message but did not change state" in rec.getMessage() for rec in log.records))


        self.mock_control_handler.handle.assert_called_once()
        self.assertEqual(server.SESSION_STATE, initial_state) # State should be unchanged
        self.assertEqual(server.STATION_STATUS, initial_status) # Status should be unchanged
        self.assertEqual(server.CONFIG, initial_config) # Config should be unchanged


    # --- Test Station Event Handling ---

    def test_station_event_ignored_when_not_running(self):
        """Test station event is ignored if session is PENDING or STOPPED (via can_handle)."""
        server.SESSION_STATE = SESSION_STATE_PENDING
        payload = json.dumps({"data": "value"})
        topic = f"{MQTT_TOPIC_STATION_BASE}station_test/event/test_event"
        msg = MockMQTTMessage(topic, payload)

        # can_handle should return False because state is PENDING
        self.mock_control_handler.can_handle.return_value = False
        self.mock_station_handler.can_handle.return_value = False # Real handler's can_handle checks state

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]), self.assertLogs(level='WARNING') as log: # Should log "unhandled"
            server.on_message(self.mock_client, None, msg)
            # Check if the unhandled message log appears
            self.assertTrue(any("Received message on unhandled topic" in rec.getMessage() for rec in log.records))

        self.mock_station_handler.can_handle.assert_called_once() # can_handle IS called
        self.mock_station_handler.handle.assert_not_called() # handle is NOT called


        server.SESSION_STATE = SESSION_STATE_STOPPED
        self.mock_station_handler.can_handle.reset_mock() # Reset mock for second part

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]), self.assertLogs(level='WARNING') as log:
             server.on_message(self.mock_client, None, msg)
             self.assertTrue(any("Received message on unhandled topic" in rec.getMessage() for rec in log.records))

        self.mock_station_handler.can_handle.assert_called_once()
        self.mock_station_handler.handle.assert_not_called()


    def test_station_event_processed_when_running(self):
        """Test station event is processed if session is RUNNING."""
        server.SESSION_STATE = SESSION_STATE_RUNNING
        initial_status = server.STATION_STATUS.copy()
        payload_dict = {"data": "station_update"}
        payload_json = json.dumps(payload_dict)
        topic = f"{MQTT_TOPIC_STATION_BASE}station_test/event/test_event"
        msg = MockMQTTMessage(topic, payload_json)

        # Simulate state change from station handler
        expected_status = {"station_test": "updated"}
        mock_returned_state = MagicMock(spec=ServerState)
        mock_returned_state.session_state = server.SESSION_STATE # Unchanged by station event
        mock_returned_state.station_status = expected_status
        mock_returned_state.config = server.CONFIG # Unchanged by station event

        self.mock_control_handler.can_handle.return_value = False
        self.mock_station_handler.can_handle.return_value = True
        self.mock_station_handler.handle.return_value = mock_returned_state

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]):
            server.on_message(self.mock_client, None, msg)

        self.mock_control_handler.can_handle.assert_called_once()
        self.mock_control_handler.handle.assert_not_called()
        self.mock_station_handler.can_handle.assert_called_once_with(topic, payload_dict, ANY)
        self.mock_station_handler.handle.assert_called_once_with(topic, payload_dict, self.mock_client, ANY)

        call_args, _ = self.mock_station_handler.handle.call_args
        passed_state = call_args[3]
        self.assertEqual(passed_state.session_state, SESSION_STATE_RUNNING)
        self.assertEqual(passed_state.station_status, initial_status)

        self.assertEqual(server.STATION_STATUS, expected_status) # Verify global state updated


    def test_station_event_invalid_topic_structure(self):
        """Test station event with invalid topic format is ignored (via can_handle)."""
        server.SESSION_STATE = SESSION_STATE_RUNNING
        payload = json.dumps({"data": "value"})
        # Topic is missing '/event/' part
        topic = f"{MQTT_TOPIC_STATION_BASE}station_test/some_action"
        msg = MockMQTTMessage(topic, payload)

        # Configure mocks - neither should handle this topic structure
        self.mock_control_handler.can_handle.return_value = False
        self.mock_station_handler.can_handle.return_value = False # Real can_handle checks structure

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]), self.assertLogs(level='WARNING') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Received message on unhandled topic" in record.getMessage() for record in log.records))

        self.mock_control_handler.can_handle.assert_called_once()
        self.mock_station_handler.can_handle.assert_called_once()
        self.mock_control_handler.handle.assert_not_called()
        self.mock_station_handler.handle.assert_not_called()

    def test_unhandled_topic(self):
        """Test that a topic not handled by any handler is logged."""
        server.SESSION_STATE = SESSION_STATE_RUNNING
        payload = json.dumps({"data": "value"})
        topic = "some/other/topic"
        msg = MockMQTTMessage(topic, payload)

        # Configure mocks - neither can_handle returns True
        self.mock_control_handler.can_handle.return_value = False
        self.mock_station_handler.can_handle.return_value = False

        with patch('src.server.message_handlers', [self.mock_control_handler, self.mock_station_handler]), self.assertLogs(level='WARNING') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Received message on unhandled topic" in record.getMessage() for record in log.records))

        self.mock_control_handler.can_handle.assert_called_once()
        self.mock_station_handler.can_handle.assert_called_once()
        self.mock_control_handler.handle.assert_not_called()
        self.mock_station_handler.handle.assert_not_called()


    # Remove old routing tests as they mocked internal functions


if __name__ == '__main__':
    unittest.main() 