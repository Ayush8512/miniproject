/*
 * Smart Attendance SaaS - ESP32 BLE Beacon Firmware
 * =================================================
 * 
 * DEPLOYMENT INSTRUCTIONS FOR MULTI-ROOM SETUP:
 * =============================================
 * Each physical ESP32 module must broadcast a UNIQUE UUID so the
 * mobile app can identify which classroom the student is in.
 * 
 * Before flashing each ESP32, change the two #define values below:
 * 
 * Example for Room 301:
 *   #define BEACON_UUID    "e2c56db5-dffb-48d2-b060-d0f5a71096e0"
 *   #define BEACON_NAME    "ROOM_301"
 * 
 * Example for Room 302:
 *   #define BEACON_UUID    "f7826da6-4fa2-4e98-8024-bc5b71e0893e"
 *   #define BEACON_NAME    "ROOM_302"
 * 
 * Example for Room 303:
 *   #define BEACON_UUID    "a495bb10-c5b1-4b44-b512-1370f02d74de"
 *   #define BEACON_NAME    "ROOM_303"
 * 
 * IMPORTANT: Each room MUST have a unique UUID. Generate new UUIDs at:
 * https://www.uuidgenerator.net/
 * 
 * HARDWARE: Any ESP32 dev board (ESP32-WROOM-32, ESP32-S3, etc.)
 * LIBRARY:  ESP32 BLE Arduino (included with ESP32 board package)
 */

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>
#include <esp_sleep.h>

// ============================================================
// >>> CHANGE THESE FOR EACH ROOM BEFORE FLASHING <<<
// ============================================================
#define BEACON_UUID    "e2c56db5-dffb-48d2-b060-d0f5a71096e0"
#define BEACON_NAME    "ROOM_301"
// ============================================================

#define MANUFACTURER_ID  0x4C00   // Apple iBeacon manufacturer ID
#define BEACON_MAJOR     1        // Can be used for floor number
#define BEACON_MINOR     301      // Can be used for room number
#define TX_POWER         -59      // Calibrated TX power at 1 meter (dBm)
#define ADV_INTERVAL_MS  100      // Advertising interval (ms) - 100ms for reliable detection

BLEAdvertising *pAdvertising;

void setup() {
    Serial.begin(115200);
    Serial.println("\n================================");
    Serial.print("Smart Attendance BLE Beacon: ");
    Serial.println(BEACON_NAME);
    Serial.print("UUID: ");
    Serial.println(BEACON_UUID);
    Serial.println("================================\n");

    BLEDevice::init(BEACON_NAME);
    
    // Set transmit power to maximum for reliable classroom coverage
    BLEDevice::setPower(ESP_PWR_LVL_P9);  // +9dBm - maximum range

    BLEServer *pServer = BLEDevice::createServer();
    pAdvertising = BLEDevice::getAdvertising();

    // Configure iBeacon
    BLEBeacon oBeacon = BLEBeacon();
    oBeacon.setManufacturerId(MANUFACTURER_ID);
    oBeacon.setProximityUUID(BLEUUID(BEACON_UUID));
    oBeacon.setMajor(BEACON_MAJOR);
    oBeacon.setMinor(BEACON_MINOR);
    oBeacon.setSignalPower(TX_POWER);

    // Build advertisement data
    BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
    oAdvertisementData.setFlags(0x06); // BR_EDR_NOT_SUPPORTED | LE_GENERAL_DISCOVERABLE
    
    // Set iBeacon manufacturer data
    std::string strServiceData = "";
    strServiceData += (char)26;  // Length
    strServiceData += (char)0xFF; // Manufacturer Specific Data
    strServiceData += oBeacon.getData();
    oAdvertisementData.addData(strServiceData);
    
    // Also set the complete local name for easier debugging
    BLEAdvertisementData oScanResponseData = BLEAdvertisementData();
    oScanResponseData.setName(BEACON_NAME);

    pAdvertising->setAdvertisementData(oAdvertisementData);
    pAdvertising->setScanResponseData(oScanResponseData);
    
    // Set advertising interval for optimal iOS/Android background detection
    // 100ms = 160 units (each unit = 0.625ms)
    pAdvertising->setMinInterval(160);  // 100ms
    pAdvertising->setMaxInterval(320);  // 200ms
    
    // Set advertisement type
    pAdvertising->setAdvertisementType(ADV_TYPE_NONCONN_IND);

    // Start advertising
    pAdvertising->start();
    
    Serial.println("[OK] BLE Beacon broadcasting...");
    Serial.print("[OK] Advertising interval: ");
    Serial.print(ADV_INTERVAL_MS);
    Serial.println("ms");
    Serial.println("[OK] Beacon is now discoverable by the Smart Attendance app.");
    Serial.println("\n--- Beacon running. Do not disconnect power. ---\n");
}

void loop() {
    // Restart advertising every 60 seconds as a safety measure
    // (in case advertising stops due to BLE stack issues)
    delay(60000);
    
    pAdvertising->stop();
    delay(100);
    pAdvertising->start();
    
    Serial.println("[HEARTBEAT] Beacon re-advertised. Still running...");
}
