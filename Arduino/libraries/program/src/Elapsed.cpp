#include "Elapsed.h"
#include "Arduino.h"

Elapsed::Elapsed(unsigned long intervalMS, bool triggerOnStart)
{

    if (triggerOnStart)
    {
        last = 0;
    }
    else
    {
        last = millis();
    }
    interval = intervalMS;
}

Elapsed::operator bool()
{
    unsigned long n = millis();
    if (n - last >= interval)
    {
        last = n;
        return true;
    }
    return false;
}

void Elapsed::setInterval(unsigned long intervalMS)
{
    interval = intervalMS;
}

void Elapsed::reset()
{
    last = millis();
}

void Elapsed::reset(unsigned long intervalMS)
{
    interval = intervalMS;
    last = millis();
}