#include "driver_registry.h"
#include "driver_registry_sensors_includes.inc"   // pulls in all <sensor>_driver.h prototypes

#define MAX_DRIVERS 16
static const SensorDriverInfo_t *gDrivers[MAX_DRIVERS];
static size_t                     gNumDrivers = 0;

void SensorRegistry_Register(const SensorDriverInfo_t *info) {
    if (gNumDrivers < MAX_DRIVERS) {
        gDrivers[gNumDrivers++] = info;
    }
    // else: overflow, ignore or handle error
}

const SensorDriverInfo_t *SensorRegistry_Find(uint8_t type_code) {
    for (size_t i = 0; i < gNumDrivers; i++) {
        if (gDrivers[i]->type_code == type_code) {
            return gDrivers[i];
        }
    }
    return NULL;
}

const SensorDriverInfo_t * const *SensorRegistry_All(void) {
    if (gNumDrivers < MAX_DRIVERS) {
        gDrivers[gNumDrivers] = NULL;
    } else {
        gDrivers[MAX_DRIVERS - 1] = NULL;
    }
    return (const SensorDriverInfo_t * const *)gDrivers;
}

void DriverRegistry_InitAll(void)
{
#include "driver_registry_sensors_calls.inc"
}
