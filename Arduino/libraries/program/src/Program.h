#ifndef PROGRAM
#define PROGRAM

#include "Elapsed.h"

#define LOOP(sucess, op) \
  while (!(sucess))      \
  {                      \
    op;                  \
    Program::loop();     \
  }

#define LOOP_EVERY(sucess, op, interval)   \
  {                                        \
    Elapsed timeCheck = Elapsed(interval); \
    while (!(sucess))                      \
    {                                      \
      if (timeCheck)                       \
      {                                    \
        op;                                \
        timeCheck.reset();                 \
      }                                    \
      Program::loop();                     \
    }                                      \
  }

#define LOOP_FOR(op, interval)                    \
  {                                               \
    Elapsed timeCheck = Elapsed(interval, false); \
    while (!timeCheck)                            \
    {                                             \
      op;                                         \
      Program::loop();                            \
    }                                             \
  }

#define DELAY(interval)                           \
  {                                               \
    Elapsed timeCheck = Elapsed(interval, false); \
    while (!timeCheck)                            \
    {                                             \
      Program::loop();                            \
    }                                             \
  }

class Program
{
public:
  static void setup();

  static void loop();
};

#endif