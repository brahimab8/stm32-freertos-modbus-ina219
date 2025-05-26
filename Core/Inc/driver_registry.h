#ifndef DRIVER_REGISTRY_H
#define DRIVER_REGISTRY_H

#include "stm32l4xx_hal.h"      // for I2C_HandleTypeDef
#include "task/sensor_task.h"   // for SensorDriver_t
#include "task/sensor_manager.h"// for SM_Status_t
#include "config/protocol.h"    // for SENSOR_TYPE_… codes
#include <stdint.h>
#include <stddef.h>

#define DRIVER_REGISTRY_END { 0, 0, NULL, NULL, NULL }

typedef struct {
    uint8_t                type_code;   
    size_t                 ctx_size;     ///< sizeof the ctx struct
    void                 (*init_ctx)(void *ctx,
                                      I2C_HandleTypeDef *hi2c,
                                      uint8_t addr7);
    const SensorDriver_t *(*get_driver)(void);
    SM_Status_t           (*configure)(void *ctx,
                                       uint8_t cmd_id,
                                       uint8_t param);
} SensorDriverInfo_t;

extern const SensorDriverInfo_t sensor_driver_registry[];

#endif // DRIVER_REGISTRY_H
