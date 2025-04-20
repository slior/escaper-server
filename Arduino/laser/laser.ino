#include <Program.h>
#include <Reading.h>
#include <MQTT.h>

#define LASER_SCAN_INTERVAL 10
#define LASER_SCAN_MIN 600
#define LASER_SCAN_MAX 1024
#define LASER_BUCKETS 16

const int bucketDiv = (LASER_SCAN_MAX-LASER_SCAN_MIN)/LASER_BUCKETS;

#define MODULE_ID 2

Elapsed timeToScan = Elapsed(LASER_SCAN_INTERVAL);

IntReading v;

void setup()
{
  // Generic setup
  Program::setup();
  // Moduler setup
  pinMode(A0, INPUT);
  Serial.println("Setup done!");
}

int bucket(int reading) {
  return (reading-LASER_SCAN_MIN) / bucketDiv;
}

void loop()
{
  Program::loop();
  if (timeToScan)
  {
    // read and map values to laser being on or off
    // TODO: this needs to be calibrated from server according to ambient light and laser distance
    int reading = analogRead(A0);
    //Serial.println(reading);
    v.updateIfChanged(bucket(reading));

    // notify server if a change happened
    if (v.available())
    {
      int bucket = v.get();
      //Serial.printf("Notify server: %d\n", bucket);
      Mqtt::send("mp/02", bucket);
    }
  }
}
