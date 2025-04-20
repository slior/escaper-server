#ifndef LED_BLINKER
#define LED_BLINKER

#include "Elapsed.h"

/* Constants */
#define LED_FAST_INTERVAL 300
#define LED_SLOW_INTERVAL 4000
#define LED_LIGHT_ON_INTERVAL 100

// flip high/low for 8266
#if defined(ARDUINO_ARCH_ESP8266)
#define LED_HIGH LOW
#define LED_LOW HIGH
#else
#define LED_HIGH HIGH
#define LED_LOW LOW
#endif

#ifndef LED_BUILTIN
#define LED_BUILTIN 9
#endif

/* Class used for led blinking
  Modes:
  * Fast blinking (default)
  * Slow blinking
  * On
  * Off

  Notes:
  - call the loop function in your idle loop
  - Fast / Slow changes the time between blinks. Blink is always LED_LIGHT_ON_INTERVAL millis
  - Blocking operations (e.g. wifi scan) will block the blinking
  - Always starts with light on (and will probably be on as long as wifi scan)

*/
class Blinker
{
private:
  static unsigned int ledOffInterval;
  static Elapsed timeToSwitch; // different intervals for led on and led off
  static char pinNumber;
  static bool isOn;
  static bool blinking;

public:
  static void loop();
  static void setup(char _pinNumber);
  static void setIsOn(bool onoff);
  static void slow();
  static void fast();
  static void on();
  static void off();
};

/* Blinker */

#endif