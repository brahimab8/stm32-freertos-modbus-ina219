#pragma once

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "task/sensor_task.h"   /**< for SensorDriver_t */
#include <hal_if.h>

/**
 * Descriptor for a sensor driver. Each sensor’s driver code will register
 * one of these.  The `init_ctx` callback now takes a HAL-IF handle instead
 * of a raw I2C_HandleTypeDef pointer.
 */
typedef struct {
    uint8_t  type_code;        ///< e.g. SENSOR_TYPE_INA219
    size_t   ctx_size;         ///< sizeof(that sensor’s ctx struct)

    /**
     * @brief Initialize the context with bus handle and 7-bit address
     * @param ctx    Pointer to sensor-specific context struct
     * @param h_i2c  HAL-IF I²C handle (returned by halif_i2c_init)
     * @param addr7  7-bit I²C address
     */
    void (*init_ctx)(
        void *ctx,
        halif_handle_t h_i2c,
        uint8_t        addr7
    );

    /** Return pointer to the SensorDriver vtable (init, read, etc.) */
    const SensorDriver_t *(*get_driver)(void);

    /** Configure a sensor field (period, gain, etc.) */
    bool (*configure)(void *ctx, uint8_t field_id, uint8_t value);

    /** Read a sensor configuration field */
    bool (*read_config)(void *ctx, uint8_t field_id, uint8_t *value);

    /** List of valid config field IDs */
    const uint8_t *(*get_config_fields)(size_t *count);

    /** Default polling period in milliseconds */
    uint32_t (*get_default_period_ms)(void);
} SensorDriverInfo_t;

/** Register a driver descriptor into the global registry */
void SensorRegistry_Register(const SensorDriverInfo_t *info);

/** Find a registered driver by its type code, or NULL if not found */
const SensorDriverInfo_t *SensorRegistry_Find(uint8_t type_code);

/** Return a NULL-terminated array of all registered drivers */
const SensorDriverInfo_t * const *SensorRegistry_All(void);

/**
 * @brief  Calls each <sensor>_RegisterDriver() to populate the registry.
 *         Its body is pulled in from driver_registry_sensors_calls.inc
 */
void DriverRegistry_InitAll(void);
