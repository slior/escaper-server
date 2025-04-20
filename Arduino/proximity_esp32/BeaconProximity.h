#ifndef BEACON_PROX
#define BEACON_PROX

#include "Arduino.h"
#include <Reading.h>

#include <Elapsed.h>
#include <ArduinoBLE.h>

#define BLE_SCAN_INTERVAL 500
#define BLE_RSSI_INTERVAL 500

/** Xiaomi **/
//const char*  beaconAddress = "ff:ff:11:1d:20:d8";

/** Toya **/
//const char*  beaconAddress = "dc:23:50:40:8f:7c";
/** Smart tag **/
//const char* beaconAddress = "ff:b1:ea:60:6b:12";  //Address changes!
//const char* beaconService = "fd44";


/** HeadPhones **/

const char* beaconAddress = "7d:63:9b:45:86:76";  //Address changes!
const char* beaconService = "febe";


class BeaconProximity : public Reading<int> {
  BLEDevice* beacon = NULL;
  Elapsed timeToScan = Elapsed(BLE_SCAN_INTERVAL);
  bool connected = false;
public:
  bool begin() {
    Serial.println("[BLE] starting");

    if (!BLE.begin()) {
      Serial.println("[BLE] begin failed!");
      return false;
    }

    Serial.println("[BLE] started");
    return true;
  }

  void scanAll() {
    Serial.print("[BLE] scanning ... ");
    BLE.scan();
    Serial.println("done");
  }

  void scanSpecific() {
    Serial.print("[BLE] scan specific ...");
    BLE.scanForAddress(beaconAddress);
    Serial.println("done");
  }

  void printInfo(BLEDevice dev, bool minimal = true) {
    Serial.printf("[dev] %s [%d]dBm ", dev.address().c_str(), dev.rssi());
    if (!minimal) {
      // print the local name, if present
      if (dev.hasLocalName()) {
        Serial.print(dev.localName());
        Serial.print(" ");
      }

      // print the advertised service UUIDs, if present
      if (dev.hasAdvertisedServiceUuid()) {
        Serial.print("Services: ");
        for (int i = 0; i < dev.advertisedServiceUuidCount(); i++) {
          Serial.print(dev.advertisedServiceUuid(i));
          Serial.print(",");
        }
      }
    }
    Serial.println();
  }

  bool hasService0(BLEDevice dev, String service) {
    return (dev.hasAdvertisedServiceUuid() && dev.advertisedServiceUuidCount() > 0 && service.equals(dev.advertisedServiceUuid(0)));
  }

  void loop() {
    if (timeToScan) {
      scanAll();
    }
    BLEDevice dev = BLE.available();
    if (dev) {

      //printInfo(dev, false);
      //const char* a = dev.address().c_str();
      //if (!strcmp(beaconAddress, a)) {
      if (hasService0(dev, beaconService)) {
        //Serial.println("[BLE] Found!!!!!!!!");
        int r = -1 * dev.rssi();
        Serial.print(".......................................................................");
        Serial.println(r);
        update(r);
        printInfo(dev);
        /*
        beacon = &dev;
        if (beacon->connect()) {
          Serial.println("[BLE] Connected");
          connected = true;
          timeToScan.setInterval(BLE_RSSI_INTERVAL);
        } else {
          Serial.println("[BLE] Failed to connect!");
          return;
        }
        */
      }
    }
  }
};

#endif