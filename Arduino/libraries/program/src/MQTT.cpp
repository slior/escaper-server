
#include "MQTT.h"

// Initialize static members
WiFiClient Mqtt::wifiClient = WiFiClient();
MqttClient Mqtt::mqttClient = MqttClient(wifiClient);
const char *Mqtt::brokerIp;
bool Mqtt::connected = false;

void Mqtt::setup(const char *_brokerIp)
{
  brokerIp = _brokerIp;
  Serial.printf("[MQTT] broker: %s \n", brokerIp);
}

bool Mqtt::isConnected()
{
  return connected;
}

void Mqtt::connect()
{
  Serial.println("[MQTT] Attempting to connect");
  mqttClient.setUsernamePassword(MQTT_USER, MQTT_PASSWORD);
  if (!mqttClient.connect(brokerIp, MQTT_PORT))
  {
    Serial.print("[MQTT] connection failed! Error code = ");
    Serial.println(mqttClient.connectError());
  }
  else
  {
    Serial.println("[MQTT] Connected");
    connected = true;
  }
}

void Mqtt::send(const char *topic, const char *message)
{
  mqttClient.beginMessage(topic);
  mqttClient.print(message);
  mqttClient.endMessage();
  Serial.printf("[MQTT] Sent %s %s\n", topic, message);
}

void Mqtt::send(const char *topic, int message)
{
  mqttClient.beginMessage(topic);
  mqttClient.print(message);
  mqttClient.endMessage();
  Serial.printf("[MQTT] Sent int %s %d\n", topic, message);
}
