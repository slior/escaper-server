#ifndef USE_WIFI
#define USE_WIFI

#include "Arduino.h"

/* Constants */

#define WIFI_SCAN_INTERVAL 2000
#define WIFI_CONNECT_INTERVAL 500
#define MAX_WIFI_CONFIGS 3

#define WIFI_SSID_UNKNOWN -1

/* Hard coded wifi networks */

struct WifiConfig
{
  const char *ssid;
  const char *pass;
  const char *mqttServer;
  WifiConfig(const char *SSID, const char *password, const char *serverIp)
  {
    ssid = SSID;
    pass = password;
    mqttServer = serverIp;
  }

  WifiConfig()
  {
    ssid = "";
    pass = "";
    mqttServer = "";
  }
};

/*
WifiScanner
Will connect to a wifi network
1. Scan networks and find a known SSID
2. Once a known SSID is found, WifiConnect will take control
*/

class WifiScanner
{
private:
  static int selectedSsid;
  static WifiConfig wifiConfigs[];
  static byte numOfWifiConfigs;

  static int tryToMatchNetwork(String ssid);

  static void printFoundSSIDs(int n);

  static WifiConfig config;

public:
  static void addWifiConfig(WifiConfig config);

  static WifiConfig getConfig();

  static bool hasSSID();

  static int scanNetworks();

  static void scanForSSID();
};

/*
WifiConnect
Will connect to a wifi network with a known SSID
1. Scan networks and find a known SSID
2. Once a known SSID is found, try to connect
3. Rely on the wifi library to re try to connect and detect wifi lose and reconnect
*/

class WifiConnect
{
private:
  static bool connected;

public:
  static void setup();

  static bool isConnected();

  static bool status();

  static void connect(WifiConfig config);
};

#endif