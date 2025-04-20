#ifndef ER_READING
#define ER_READING

template <typename T>
class Reading
{
private:
  bool hasNewValue;
  T currentValue;
  T lastSentValue;

public:
  Reading()
      : hasNewValue(false) {}

  void update(T newValue)
  {
    currentValue = newValue;
    hasNewValue = true;
  }

  void updateIfChanged(T newValue)
  {
    if (newValue != lastSentValue)
    {
      currentValue = newValue;
      hasNewValue = true;
    }
  }

  bool available() const
  {
    return hasNewValue;
  }

  int get()
  {
    hasNewValue = false;
    lastSentValue = currentValue;
    return currentValue;
  }
};

class IntReading : public Reading<int>
{
};

#endif