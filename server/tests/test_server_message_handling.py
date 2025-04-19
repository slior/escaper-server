import unittest
import json
from unittest.mock import patch, MagicMock, ANY

# Modules to test (adjust path based on PYTHONPATH or test runner setup)
from src import server
from src import control_handler
from src import station_handler

# Mock MQTT message class
class MockMQTTMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload.encode('utf-8') # Payloads are bytes

    def decode(self, encoding='utf-8'):
        # Add a decode method to mimic paho's message object if needed indirectly
        return self.payload.decode(encoding)

class TestServerMessageHandling(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        # Reset state for each test
        server.SESSION_STATE = server.SESSION_STATE_PENDING
        server.STATION_STATUS = {}
        server.CONFIG = { # Minimal config for testing
            'mqtt_broker': {'host': 'localhost', 'port': 1883},
            'stations': {
                'station_test': {
                    'sensors': [{'type': 'test_sensor', 'event_type': 'test_event'}]
                }
            }
        }
        self.mock_client = MagicMock()

    # --- Test Message Parsing ---

    def test_on_message_invalid_json(self):
        """Test that invalid JSON payload is handled gracefully."""
        msg = MockMQTTMessage("some/topic", "{not json")
        with self.assertLogs(level='ERROR') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Could not decode JSON payload" in record.getMessage() for record in log.records))

    def test_on_message_non_utf8(self):
        """Test that non-UTF-8 payload is handled."""
        # Simulate non-UTF-8 bytes (e.g., latin-1)
        msg = MockMQTTMessage("some/topic", "")
        msg.payload = b'\xff' # Invalid start byte for UTF-8
        with self.assertLogs(level='ERROR') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Could not decode UTF-8 payload" in record.getMessage() for record in log.records))


    # --- Test Control Message Handling ---

    @patch('src.server.handle_control_message')
    def test_control_start(self, mock_handle_control):
        """Test START control message."""
        # Configure the mock to return a new state
        mock_handle_control.return_value = (server.SESSION_STATE_RUNNING, {}, None)
        payload = json.dumps({"action": "start"})
        msg = MockMQTTMessage(server.MQTT_TOPIC_SERVER_CONTROL, payload)

        server.on_message(self.mock_client, None, msg)

        mock_handle_control.assert_called_once_with(json.loads(payload), server.SESSION_STATE_PENDING, {})
        self.assertEqual(server.SESSION_STATE, server.SESSION_STATE_RUNNING)

    @patch('src.server.handle_control_message')
    def test_control_stop(self, mock_handle_control):
        """Test STOP control message."""
        server.SESSION_STATE = server.SESSION_STATE_RUNNING # Start in running state
        mock_handle_control.return_value = (server.SESSION_STATE_STOPPED, {}, None)
        payload = json.dumps({"action": "stop"})
        msg = MockMQTTMessage(server.MQTT_TOPIC_SERVER_CONTROL, payload)

        server.on_message(self.mock_client, None, msg)

        mock_handle_control.assert_called_once_with(json.loads(payload), server.SESSION_STATE_RUNNING, {})
        self.assertEqual(server.SESSION_STATE, server.SESSION_STATE_STOPPED)

    @patch('src.server.handle_control_message')
    def test_control_reset(self, mock_handle_control):
        """Test RESET control message."""
        server.SESSION_STATE = server.SESSION_STATE_RUNNING
        server.STATION_STATUS = {"some_station": "done"}
        mock_handle_control.return_value = (server.SESSION_STATE_PENDING, {}, None)
        payload = json.dumps({"action": "reset"})
        msg = MockMQTTMessage(server.MQTT_TOPIC_SERVER_CONTROL, payload)

        server.on_message(self.mock_client, None, msg)

        mock_handle_control.assert_called_once_with(json.loads(payload), server.SESSION_STATE_RUNNING, {"some_station": "done"})
        self.assertEqual(server.SESSION_STATE, server.SESSION_STATE_PENDING)
        self.assertEqual(server.STATION_STATUS, {}) # Status should be reset by handler

    @patch('src.server.handle_control_message')
    def test_control_reload(self, mock_handle_control):
        """Test RELOAD control message."""
        original_config = server.CONFIG.copy()
        new_config = {"reloaded": True}
        mock_handle_control.return_value = (server.SESSION_STATE, server.STATION_STATUS, new_config)
        payload = json.dumps({"action": "reload"})
        msg = MockMQTTMessage(server.MQTT_TOPIC_SERVER_CONTROL, payload)

        with self.assertLogs(level='INFO') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("configuration has been reloaded" in record.getMessage() for record in log.records))

        mock_handle_control.assert_called_once()
        self.assertEqual(server.CONFIG, new_config)
        # Restore original config to not affect other tests
        server.CONFIG = original_config

    @patch('src.server.handle_control_message')
    def test_control_unknown_action(self, mock_handle_control):
        """Test unknown control action."""
        # Assume handler logs warning and returns unchanged state/config
        initial_state = server.SESSION_STATE
        initial_status = server.STATION_STATUS.copy()
        mock_handle_control.return_value = (initial_state, initial_status, None)
        payload = json.dumps({"action": "invalid_action"})
        msg = MockMQTTMessage(server.MQTT_TOPIC_SERVER_CONTROL, payload)

        server.on_message(self.mock_client, None, msg)

        mock_handle_control.assert_called_once()
        self.assertEqual(server.SESSION_STATE, initial_state)
        self.assertEqual(server.STATION_STATUS, initial_status)


    # --- Test Station Event Handling ---

    @patch('src.server.handle_station_event')
    def test_station_event_ignored_when_not_running(self, mock_handle_event):
        """Test station event is ignored if session is PENDING or STOPPED."""
        server.SESSION_STATE = server.SESSION_STATE_PENDING
        payload = json.dumps({"data": "value"})
        topic = "escaperoom/station/station_test/event/test_event"
        msg = MockMQTTMessage(topic, payload)

        with self.assertLogs(level='DEBUG') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any(f"Ignoring message from {topic}" in record.getMessage() for record in log.records))
        mock_handle_event.assert_not_called()

        server.SESSION_STATE = server.SESSION_STATE_STOPPED
        with self.assertLogs(level='DEBUG') as log:
             server.on_message(self.mock_client, None, msg)
             self.assertTrue(any(f"Ignoring message from {topic}" in record.getMessage() for record in log.records))
        mock_handle_event.assert_not_called()


    @patch('src.server.handle_station_event')
    def test_station_event_processed_when_running(self, mock_handle_event):
        """Test station event is processed if session is RUNNING."""
        server.SESSION_STATE = server.SESSION_STATE_RUNNING
        payload_dict = {"data": "value"}
        payload_json = json.dumps(payload_dict)
        topic = "escaperoom/station/station_test/event/test_event"
        msg = MockMQTTMessage(topic, payload_json)

        server.on_message(self.mock_client, None, msg)

        mock_handle_event.assert_called_once_with(
            topic,
            payload_dict,
            self.mock_client,
            server.CONFIG,
            server.STATION_STATUS,
            ANY # logger instance
        )


    @patch('src.server.handle_station_event')
    def test_station_event_invalid_topic(self, mock_handle_event):
        """Test station event with invalid topic format is ignored."""
        # This case might be implicitly handled by topic matching,
        # but we can test a non-matching station topic.
        server.SESSION_STATE = server.SESSION_STATE_RUNNING
        payload = json.dumps({"data": "value"})
        topic = "escaperoom/station/malformed" # Does not match expected pattern
        msg = MockMQTTMessage(topic, payload)

        with self.assertLogs(level='WARNING') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Received message on unhandled topic" in record.getMessage() for record in log.records))

        mock_handle_event.assert_not_called()

    # --- Test Routing ---

    @patch('src.server._handle_control_message_internal')
    @patch('src.server._handle_station_event_internal')
    def test_routing_control_topic(self, mock_handle_station, mock_handle_control):
        """Verify control topic calls control handler, not station handler."""
        payload = json.dumps({"action": "start"})
        msg = MockMQTTMessage(server.MQTT_TOPIC_SERVER_CONTROL, payload)
        server.on_message(self.mock_client, None, msg)
        mock_handle_control.assert_called_once()
        mock_handle_station.assert_not_called()

    @patch('src.server._handle_control_message_internal')
    @patch('src.server._handle_station_event_internal')
    def test_routing_station_topic(self, mock_handle_station, mock_handle_control):
        """Verify station topic calls station handler, not control handler."""
        server.SESSION_STATE = server.SESSION_STATE_RUNNING # Need running state
        payload = json.dumps({"data": "value"})
        topic = "escaperoom/station/station_test/event/test_event"
        msg = MockMQTTMessage(topic, payload)
        server.on_message(self.mock_client, None, msg)
        mock_handle_control.assert_not_called()
        mock_handle_station.assert_called_once()

    @patch('src.server._handle_control_message_internal')
    @patch('src.server._handle_station_event_internal')
    def test_routing_unhandled_topic(self, mock_handle_station, mock_handle_control):
        """Verify unhandled topic calls neither handler."""
        payload = json.dumps({"data": "value"})
        topic = "some/other/topic"
        msg = MockMQTTMessage(topic, payload)
        with self.assertLogs(level='WARNING') as log:
            server.on_message(self.mock_client, None, msg)
            self.assertTrue(any("Received message on unhandled topic" in record.getMessage() for record in log.records))
        mock_handle_control.assert_not_called()
        mock_handle_station.assert_not_called()


if __name__ == '__main__':
    unittest.main() 