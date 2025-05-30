#ifndef INA219_DRIVER_H
#define INA219_DRIVER_H

#include "task/sensor_task.h"   /**< SensorDriver_t, SensorSample_t */
#include "drivers/ina219.h"     /**< Low-level INA219 HAL wrapper */
#include "stm32l4xx_hal.h"      /**< I2C_HandleTypeDef */
#include <stdint.h>

/**
 * @brief   Context for an INA219 sensor instance.
 * @details Holds the I²C handle and 8-bit address (7-bit << 1).
 */
typedef struct {
    I2C_HandleTypeDef *hi2c;   /**< Pointer to initialized I2C bus handle */
    uint16_t           addr8;  /**< 8-bit I²C address of the INA219 */
} INA219_Ctx_t;

/**
 * @brief   Retrieve the SensorDriver_t v-table for INA219.
 * @note    The returned static v-table uses INA219_Ctx_t as its context.
 * @return  Pointer to SensorDriver_t with .init/.read callbacks and sample_size.
 */
const SensorDriver_t *INA219_GetDriver(void);

#endif // INA219_DRIVER_H
