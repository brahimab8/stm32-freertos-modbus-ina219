/* Auto-generated ina219 config */
#pragma once
#include <stdint.h>
#include "ina219.h"

typedef struct {
    INA219_Gain_t gain;
    INA219_BusRange_t bus_range;
    uint16_t calibration;
} ina219_config_defaults_t;

#define SENSOR_PAYLOAD_SIZE_INA219 6

extern ina219_config_defaults_t ina219_defaults;
