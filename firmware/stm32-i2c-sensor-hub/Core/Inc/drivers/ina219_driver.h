/* Manually edited ina219_driver.h; */
#pragma once

#include "task/sensor_task.h"  /**< SensorDriver_t, SensorSample_t */
#include "driver_registry.h"   /**< SensorRegistry_Register */
#include "drivers/ina219.h"     /**< HAL-IF–based wrapper */
#include <hal_if.h>
#include <stdint.h>
#include <stdbool.h>

// ---------------- Public callbacks ----------------
/**
 * @brief   Initialize INA219 context.
 * @param   vctx    Pointer to INA219_Ctx_t
 * @param   h_i2c   HAL-IF handle (from halif_i2c_init)
 * @param   addr7   7-bit I²C address
 */
void ina219_init_ctx(void *vctx, halif_handle_t h_i2c, uint8_t addr7);

/**
 * @brief   Configure a register field.
 * @param   vctx       Pointer to INA219_Ctx_t
 * @param   field_id   Command ID for the configuration field
 * @param   value      Value to write
 * @return  true on success, false on error
 */
bool ina219_configure(void *vctx, uint8_t field_id, uint8_t value);

/**
 * @brief   Read a configuration field.
 * @param   vctx       Pointer to INA219_Ctx_t
 * @param   field_id   Command ID for the configuration field
 * @param   value      Output pointer for the read value
 * @return  true on success, false on error
 */
bool ina219_read_config(void *vctx, uint8_t field_id, uint8_t *value);

// vtable getter:
const SensorDriver_t *INA219_GetDriver(void);

// Register this driver into the global registry:
void ina219_RegisterDriver(void);

/**
 * @brief   Context for a sensor instance.
 */
typedef struct {
    halif_handle_t        h_i2c;       /**< HAL-IF handle */
    uint8_t               addr7;       /**< 7-bit I²C address */
    INA219_PERIOD_t       period;
    INA219_GAIN_t         gain;
    INA219_BUS_RANGE_t    bus_range;
    INA219_CALIBRATION_t  calibration;
    uint8_t               payload_mask;  /**< which payload bits are enabled */
} INA219_Ctx_t;
