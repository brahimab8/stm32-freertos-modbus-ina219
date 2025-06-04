#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "task/sensor_task.h"   // for SensorDriver_t

typedef struct __I2C_HandleTypeDef I2C_HandleTypeDef;

typedef struct {
    uint8_t  type_code;        ///< e.g. SENSOR_TYPE_INA219
    size_t   ctx_size;         ///< sizeof(that sensor’s ctx struct)

    void (*init_ctx)(void *ctx,
                     I2C_HandleTypeDef *hi2c,
                     uint8_t addr7);

    const SensorDriver_t *(*get_driver)(void);
    bool (*configure)(void *ctx, uint8_t field_id, uint8_t value);
    bool (*read_config)(void *ctx, uint8_t field_id, uint8_t *value);
    const uint8_t *(*get_config_fields)(size_t *count); 
    uint32_t (*get_default_period_ms)(void);

} SensorDriverInfo_t;

void SensorRegistry_Register(const SensorDriverInfo_t *info);
const SensorDriverInfo_t *SensorRegistry_Find(uint8_t type_code);
const SensorDriverInfo_t * const *SensorRegistry_All(void);

/**
 * @brief  Calls each <sensor>_RegisterDriver() to populate the registry.
 *         Its body is pulled in from driver_registry_sensors_calls.inc
 */
void DriverRegistry_InitAll(void);
