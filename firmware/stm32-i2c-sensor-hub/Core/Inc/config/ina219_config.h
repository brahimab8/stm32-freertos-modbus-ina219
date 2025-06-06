/* Auto-generated ina219 config */
#pragma once
#include <stdint.h>
#include "drivers/ina219.h"

typedef struct {
    INA219_PERIOD_t period;
    INA219_GAIN_t gain;
    INA219_BUS_RANGE_t bus_range;
    INA219_SHUNT_MILLIOHM_t shunt_milliohm;
    INA219_CURRENT_LSB_UA_t current_lsb_uA;
} INA219_config_defaults_t;

#define SENSOR_PAYLOAD_SIZE_INA219 4

extern INA219_config_defaults_t ina219_defaults;
