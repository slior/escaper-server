#ifndef ER_MQTT
#define ER_MQTT

#include <ArduinoMqttClient.h>

#if defined(ARDUINO_ARCH_ESP8266)
#include <ESP8266WiFi.h>
#elif defined(ESP32)
#include <WiFi.h>
#else
#error Architecture unrecognized by this code.
#endif

/* Constants */
#define MQTT_PORT (uint16_t)1883
#define MQTT_USER "marzuk"
#define MQTT_PASSWORD "lalaland"
#define MQTT_CONNECT_INTERVAL 5000

// To connect with SSL/TLS:
// 1) Change WiFiClient to WiFiSSLClient.
// 2) Change port value from 1883 to 8883.
// 3) Change broker value to a server with a known SSL/TLS root certificate
//    flashed in the WiFi module.

// WiFiClient wifiClient;
// MqttClient mqttClient(wifiClient);

class Mqtt
{
private:
  static WiFiClient wifiClient;
  static MqttClient mqttClient;
  static const char *brokerIp;
  static bool connected;

public:
  static void setup(const char *_brokerIp);

  static bool isConnected();

  static void connect();

  static void send(const char *topic, const char *message);

  static void send(const char *topic, int message);
};

#endif