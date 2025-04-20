#ifndef SHARD_UTILS
#define SHARD_UTILS

/* Class used for non blocking delays
  Will evaluate to true when the interval has passed since the last time.
  Note: It will count start to start. You can call reset on the end of the operation to count end to start.
*/

class Elapsed
{
private:
  unsigned long interval;
  unsigned long last = 0;

public:
  Elapsed(unsigned long intervalMS, bool triggerOnStart = true);

  operator bool();

  void setInterval(unsigned long intervalMS);

  void reset();

  void reset(unsigned long intervalMS);
};

#endif