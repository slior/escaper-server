#include "Arduino.h"
#include "Blinker.h"

// Initialize static members
unsigned int Blinker::ledOffInterval = LED_FAST_INTERVAL;
char Blinker::pinNumber;
Elapsed Blinker::timeToSwitch = Elapsed(Blinker::ledOffInterval);
bool Blinker::isOn = false;
bool Blinker::blinking = true;

void Blinker::setIsOn(bool onoff)
{
    isOn = onoff;
    if (isOn)
    {
        digitalWrite(pinNumber, LED_HIGH);
        timeToSwitch.reset(LED_LIGHT_ON_INTERVAL);
    }
    else
    {
        digitalWrite(pinNumber, LED_LOW);
        timeToSwitch.reset(ledOffInterval);
    }
}

void Blinker::loop()
{
    if (timeToSwitch)
    {
        setIsOn(!isOn);
    }
}

void Blinker::slow()
{
    ledOffInterval = LED_SLOW_INTERVAL;
    blinking = true;
}

void Blinker::fast()
{
    ledOffInterval = LED_FAST_INTERVAL;
    blinking = true;
}

void Blinker::on()
{
    setIsOn(true);
    blinking = false;
}

void Blinker::off()
{
    setIsOn(false);
    blinking = false;
}

void Blinker::setup(char _pinNumber)
{
    pinNumber = _pinNumber;
    // Serial.printf("LED_BUILTIN %d \n", LED_BUILTIN);
    pinMode(pinNumber, OUTPUT);
    fast();
    setIsOn(true);
}