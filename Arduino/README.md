# Embedded devices code
This folder contains the code for all embedded devices.
It contains a shared library called program for managing the device life cycle, connecting to Wifi and MQTT server, and hosts shared utilities.

## Folder structure
-- Arduino
------ libraries : place for 3rd party libraries and our own program library.
------ all other directories: each directory is a project that should be deployed to a single embedded device. Currently it includes a couple of POC device implementations.

## Boards

Currently using 2 different boards for testing:

#### Esp32-s3-devkitc-1 knockout 
| Att                  |                                                                                            |
|----------------------|--------------------------------------------------------------------------------------------|
| Board name           | Esp32-s3-devkitc-1                                                                         |
| Chip                 | ESP32-s3                                                                                   |
| **Arduino IDE name** | ESP32S3 dev Module                                                                         |
| Note                 | GPIO pinout is not 100% compatible with the official module documentation                  |
| Note                 | Serial works only when connected to one of the USB connection (the one far from the 5v in) |


#### Esp8266 esp-12f d1 mini WeMos knockout

| Att                  |                                 |
|----------------------|---------------------------------|
| Board name           | Esp8266 esp-12f d1 mini         |
| Chip                 | ESP-8266ex                      |
| **Arduino IDE name** | LOLIN(WEMOS) D1 mini (clone)    |
| Note                 | may require a driver on windows |


I have other boards, and may order even different modules.
While these boards are similar, they do have different capabilities. 
The available GPIO numbers differ, and changing the board will cause a re-build of the project.
For these reasons, each project is intendant to run on a specific board type

## Arduino IDE

The coded uses the Arduino paradigm of a single "setup" function followed by a running "loop" function, using the Arduino library and 3rd party libraries.
It is currently built using the Arduino IDE to write,compile,and deploy code, even though it's shit:

1. Our own library code can't be edited. Using VSCode for that, but it is not ideal. 
2. Libraries and boards need to manually be installed.
3. No way to bind a library with a specific device type, this is done manually. In practice, changing a board type may change the code.

TODO: Explore using symlinks instead of libraries directory.
TODO: Explore using the Arduino-CLI tool

# Setting up Arduino IDE

## One time setup 
1. Arduino IDE file>prefs
1.1 Set sketchbook location to `{root}/Arduino`
1.2 Add additional boards ... `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
1.3 Add additional boards ...  `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
2. Make sure serial Monitor is set to `115200` baud
3. restart Arduino IDE

## Install Libraries
- ArduinoBLE
- ArduinoMqttClient

