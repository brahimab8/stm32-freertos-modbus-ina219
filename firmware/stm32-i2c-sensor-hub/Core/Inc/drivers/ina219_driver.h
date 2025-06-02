/* Auto-generated ina219_driver.h; do not edit! */
#pragma once

#include "task/sensor_task.h"  /**< SensorDriver_t, SensorSample_t */
#include "driver_registry.h"   /**< SensorRegistry_Register */
#include "drivers/ina219.h"        /**< HAL-level wrapper */
#include "stm32l4xx_hal.h"       /**< I2C_HandleTypeDef */
#include <stdint.h>
#include <stdbool.h>

// ---------------- Public callbacks ----------------
void ina219_init_ctx(void *vctx, I2C_HandleTypeDef *hi2c, uint8_t addr7);
bool ina219_configure(void *vctx, uint8_t field_id, uint8_t value);
bool ina219_read_config(void *vctx, uint8_t field_id, uint8_t *value);

// vtable getter:
const SensorDriver_t *INA219_GetDriver(void);

// Register this driver into the global registry:
void ina219_RegisterDriver(void);

/**
 * @brief   Context for a sensor instance.
 */
typedef struct {
    I2C_HandleTypeDef *hi2c;      /**< I2C handle */
    uint16_t           addr8;     /**< 8-bit I²C address */
    INA219_GAIN_t gain;
    INA219_BUS_RANGE_t bus_range;
    INA219_CALIBRATION_t calibration;
    uint8_t payload_mask;   /**< which payload bits are enabled */
} INA219_Ctx_t;
