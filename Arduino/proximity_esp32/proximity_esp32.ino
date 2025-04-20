#include <Program.h>
#include "BeaconProximity.h"
#include <MQTT.h>



BeaconProximity proximity = BeaconProximity();

void setup() {
  Program::setup();

  // ------------------ init BLE
  LOOP_EVERY(proximity.begin(), , 2000)

  Serial.println("Setup done!");
}
void loop() {
  Program::loop();
  proximity.loop();
  if (proximity.available()) {
    Mqtt::send("mp/01", proximity.get());
  }
}
