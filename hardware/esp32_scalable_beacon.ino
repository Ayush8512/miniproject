/*
 * Smart Attendance SaaS - ESP32 BLE Beacon Firmware with Deep Sleep
 * =================================================================
 * 
 * Contributed by: Shivansh Tripathi (@snt733228-wq)
 * 
 * LOW POWER OPTIMIZATIONS (DEEP SLEEP):
 * =====================================
 * By default, ENABLE_DEEP_SLEEP is set to true. The beacon alternates
 * between active BLE broadcasting (10s) and ultra-low power Deep Sleep (20s),
 * slashing power consumption from ~100mA to ~15µA.
 */

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>
#include <esp_sleep.h>

// ============================================================
// >>> ROOM CONFIGURATION <<<
// ============================================================
#define BEACON_UUID    "e2c56db5-dffb-48d2-b060-d0f5a71096e0"
#define BEACON_NAME    "ROOM_301"

#define MANUFACTURER_ID  0x4C00   // Apple iBeacon manufacturer ID
#define BEACON_MAJOR     1        // Floor number
#define BEACON_MINOR     301      // Room number
#define TX_POWER         -59      // Calibrated TX power at 1 meter (dBm)
#define ADV_INTERVAL_MS  100      // Advertising interval (ms)

// ============================================================
// >>> DEEP SLEEP CONFIGURATION <<<
// ============================================================
#define ENABLE_DEEP_SLEEP       true   // Set to false for 24/7 continuous plugged mode
#define ADVERTISE_DURATION_SEC  10     // Active BLE broadcast window (seconds)
#define SLEEP_DURATION_SEC      20     // Deep sleep window (seconds)
#define uS_TO_S_FACTOR          1000000ULL

RTC_DATA_ATTR int bootCount = 0;
BLEAdvertising *pAdvertising = nullptr;

void setup() {
    Serial.begin(115200);
    ++bootCount;

    Serial.println("\n==================================================");
    Serial.printf("Smart Attendance BLE Beacon: %s (Cycle #%d)\n", BEACON_NAME, bootCount);
    Serial.printf("Room UUID: %s\n", BEACON_UUID);
    Serial.printf("Deep Sleep Mode: %s\n", ENABLE_DEEP_SLEEP ? "ENABLED" : "DISABLED");
    Serial.println("==================================================\n");

    BLEDevice::init(BEACON_NAME);
    BLEDevice::setPower(ESP_PWR_LVL_P9); // Maximum power (+9dBm)

    BLEServer *pServer = BLEDevice::createServer();
    pAdvertising = BLEDevice::getAdvertising();

    BLEBeacon oBeacon = BLEBeacon();
    oBeacon.setManufacturerId(MANUFACTURER_ID);
    oBeacon.setProximityUUID(BLEUUID(BEACON_UUID));
    oBeacon.setMajor(BEACON_MAJOR);
    oBeacon.setMinor(BEACON_MINOR);
    oBeacon.setSignalPower(TX_POWER);

    BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
    oAdvertisementData.setFlags(0x06);
    
    std::string strServiceData = "";
    strServiceData += (char)26;
    strServiceData += (char)0xFF;
    strServiceData += oBeacon.getData();
    oAdvertisementData.addData(strServiceData);
    
    BLEAdvertisementData oScanResponseData = BLEAdvertisementData();
    oScanResponseData.setName(BEACON_NAME);

    pAdvertising->setAdvertisementData(oAdvertisementData);
    pAdvertising->setScanResponseData(oScanResponseData);
    pAdvertising->setMinInterval(160);
    pAdvertising->setMaxInterval(320);
    pAdvertising->setAdvertisementType(ADV_TYPE_NONCONN_IND);

    pAdvertising->start();
    Serial.println("[OK] BLE Beacon actively broadcasting...");

    if (ENABLE_DEEP_SLEEP) {
        delay(ADVERTISE_DURATION_SEC * 1000);

        pAdvertising->stop();
        BLEDevice::deinit(false);
        btStop();

        Serial.printf("[POWER] Entering Deep Sleep for %d seconds...\n", SLEEP_DURATION_SEC);
        Serial.flush();

        esp_sleep_enable_timer_wakeup(SLEEP_DURATION_SEC * uS_TO_S_FACTOR);
        esp_deep_sleep_start();
    }
}

void loop() {
    if (!ENABLE_DEEP_SLEEP) {
        delay(60000);
        if (pAdvertising) {
            pAdvertising->stop();
            delay(100);
            pAdvertising->start();
        }
    }
}
