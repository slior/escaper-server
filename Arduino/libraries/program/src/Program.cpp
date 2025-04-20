
#include "Program.h"
#include "UseWifi.h"
#include "Blinker.h"
#include "MQTT.h"

void Program::setup()
{

  Blinker::setup(LED_BUILTIN);

  /////////////////
  // 1. Set serial port. make sure arduino ide is set to the same baud rate
  Serial.begin(115200);
  LOOP(Serial, )
  DELAY(2500)

  Serial.println("\nSetup ...");

  /////////////////
  // 2. pre loop: wifi connection setup
  WifiScanner::addWifiConfig(WifiConfig("Hemi25", "25%isreva", "192.168.68.68"));
  WifiConnect::setup();
  /////////////////
  // 2. pre loop: wifi connection setup
  LOOP_EVERY(WifiScanner::hasSSID(), WifiScanner::scanForSSID(), WIFI_SCAN_INTERVAL)
  WifiConnect::connect(WifiScanner::getConfig());
  LOOP_EVERY(WifiConnect::isConnected(), WifiConnect::status(), WIFI_CONNECT_INTERVAL)

  /////////////////
  // 3. pre loop: Connect to mqtt broker

  Mqtt::setup(WifiScanner::getConfig().mqttServer);
  LOOP_EVERY(Mqtt::isConnected(), Mqtt::connect(), MQTT_CONNECT_INTERVAL)

  Blinker::slow();
  Serial.println("Generic Setup done!");
}

void Program::loop()
{
  Blinker::loop();
  delay(1); // allow events on 8266
}
