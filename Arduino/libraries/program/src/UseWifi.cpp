#include "UseWifi.h"
#include "Arduino.h"

//////////////////////////////////
// implementation

#if defined(ARDUINO_ARCH_ESP8266)
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif

// max wificonfigs  = 3
int WifiScanner::selectedSsid = WIFI_SSID_UNKNOWN;
WifiConfig WifiScanner::wifiConfigs[] = {{"???", "???", ""}, {"???", "???", ""}, {"???", "???", ""}};
WifiConfig WifiScanner::config = {"???", "???", ""};
byte WifiScanner::numOfWifiConfigs = 0;

//////////////////////////////////
// Wifi Scanner

void WifiScanner::addWifiConfig(WifiConfig config)
{
    if (numOfWifiConfigs < MAX_WIFI_CONFIGS)
    {
        wifiConfigs[numOfWifiConfigs] = config;
        numOfWifiConfigs++;
    }
}

int WifiScanner::tryToMatchNetwork(String ssid)
{
    Serial.printf("[SSID] Matching against %d predefined networks\n", numOfWifiConfigs);
    // scan predefined configurations
    for (int i = 0; i < numOfWifiConfigs; i++)
    {
        if (ssid.equals(wifiConfigs[i].ssid))
        {
            return i;
        }
    }
    // nothing found
    return WIFI_SSID_UNKNOWN;
}

void WifiScanner::printFoundSSIDs(int n)
{
    Serial.printf("[SSID] %d networks found \n", n);
    for (int i = 0; i < n; i++)
    {
        Serial.printf("[SSID] %s (%ldb) \n", WiFi.SSID(i).c_str(), WiFi.RSSI(i));
        delay(10);
    }
    Serial.println("[SSID] ---");
}

bool WifiScanner::hasSSID()
{
    return (selectedSsid != WIFI_SSID_UNKNOWN);
}

int WifiScanner::scanNetworks()
{

    int firstMatch = WIFI_SSID_UNKNOWN;

    Serial.println("[SSID] Scan start");
    int n = WiFi.scanNetworks();
    printFoundSSIDs(n);

    for (int i = 0; i < n; ++i)
    {
        firstMatch = tryToMatchNetwork(WiFi.SSID(i));
        if (firstMatch != WIFI_SSID_UNKNOWN)
        {
            return firstMatch;
        }
        delay(10);
    }
    return firstMatch;
}

void WifiScanner::scanForSSID()
{
    selectedSsid = scanNetworks();
    if (hasSSID())
        config = wifiConfigs[selectedSsid];
}

WifiConfig WifiScanner::getConfig()
{
    return config;
}

//////////////////////////////////
// Wifi Connect

// Initialize static members
bool WifiConnect::connected = false;

void WifiConnect::setup()
{
    // Set WiFi to station mode and disconnect from an AP if it was previously connected
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);
}

bool WifiConnect::status()
{
    // detect current status
    switch (WiFi.status())
    {
    case WL_NO_SSID_AVAIL:
        Serial.println("[WiFi] SSID not found");
        break;
    case WL_CONNECT_FAILED:
        Serial.print("[WiFi] Failed - WiFi not connected! Reason: ");
        return false;
        break;
    case WL_CONNECTION_LOST:
        Serial.println("[WiFi] Connection was lost");
        break;
    case WL_SCAN_COMPLETED:
        Serial.println("[WiFi] Scan is completed");
        break;
    case WL_DISCONNECTED:
        Serial.println("[WiFi] WiFi is disconnected");
        break;
    case WL_CONNECTED:
        Serial.print("[WiFi] WiFi is connected! with IP: ");
        Serial.println(WiFi.localIP());
        connected = true;
        return true;
        break;
    default:
        Serial.print("[WiFi] WiFi Status: ");
        Serial.println(WiFi.status());
        break;
    }
    return false;
}

void WifiConnect::connect(WifiConfig config)
{
    Serial.printf("[WiFi] Connecting to %s\n", config.ssid);
    WiFi.begin(config.ssid, config.pass);
    status();
}

bool WifiConnect::isConnected()
{
    return connected;
}
