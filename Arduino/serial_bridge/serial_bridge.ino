/** Wire

src TX -> 16
src ground -> ground

*/

///// for esp32
#define RX 16
#define TX 17



/**

src TX -> monitor RX  (16)

Common ground

Use level shifters if one ESP is 5V and the other is 3.3V (unlikely, but be aware).

*/


void setup() {
  Serial.begin(115200);                       // USB to PC
  Serial2.begin(115200, SERIAL_8N1, RX, TX);  // RX=16, TX=17 (only RX used)
  delay(5000);
  Serial.println("\n\nOn!");
}

void loop() {
  while (Serial2.available()) {
    Serial.write(Serial2.read());
  }
  while (Serial.available()) {
    Serial2.write(Serial.read());
  }
}