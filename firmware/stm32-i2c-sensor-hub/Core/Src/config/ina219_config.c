/* Auto-generated ina219 defaults definition */
#include "config/ina219_config.h"


/**
 * @brief Default values for sensor ina219 configuration.
 */
INA219_config_defaults_t ina219_defaults = {
    .period =        5,
    .gain =        INA219_GAIN_40MV,
    .bus_range =        0,
    .shunt_milliohm =        100,
    .current_lsb_uA =        100,
};