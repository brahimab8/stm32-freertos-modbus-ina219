#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include "cmsis_os.h"
#include "task/sensor_task.h"    ///< for SensorTaskHandle_t, SensorSample_t
#include "driver_registry.h" 

#include <stdint.h>

#define SM_MAX_SENSORS  8

/// Status codes returned by SensorManager APIs
typedef enum {
    SM_OK    = 0,
    SM_ERROR = 1
} SM_Status_t;

/// Opaque manager handle
typedef struct SensorManager SensorManager_t;

/// One entry per active sensor
typedef struct {
    uint8_t               sensor_id;   ///< index (0…count-1)
    uint8_t               type_code;   ///< SENSOR_TYPE_INA219, etc.
    uint8_t               addr7;       ///< 7-bit I²C address
    uint32_t              period_ms;   ///< current poll period (ms)
    const SensorDriver_t *drv;         ///< driver v-table
    void                 *ctx;         ///< driver context (driver-specific)
    SensorTaskHandle_t   *task;        ///< underlying polling task
} SM_Entry_t;

/**
 * @brief   Create a new SensorManager.
 * @param   busMutex  Mutex that will be shared by all SensorTasks.
 * @param   hi2c      Pointer to the HAL I2C handle to pass into each driver.
 * @return  Pointer to the manager, or NULL on allocation failure.
 */
SensorManager_t *SensorManager_Create(osMutexId_t        busMutex,
                                      I2C_HandleTypeDef *hi2c);

/**
 * @brief   Destroy a SensorManager and all its tasks/contexts.
 * @param   mgr  Manager handle returned by SensorManager_Create.
 */
void SensorManager_Destroy(SensorManager_t *mgr);

/**
 * @brief   Add (and start) a new sensor of the given type at the given address.
 * @param   mgr        Manager handle.
 * @param   type_code  One of SENSOR_TYPE_… from protocol.h.
 * @param   addr7      7-bit I²C address.
 * @param   period_ms  Poll interval in milliseconds.
 * @return  SM_OK or SM_ERROR.
 */
SM_Status_t SensorManager_AddByType(SensorManager_t *mgr,
                                    uint8_t          type_code,
                                    uint8_t          addr7,
                                    uint32_t         period_ms);

/**
 * @brief   Remove (and stop) the sensor at the given I²C address.
 * @param   mgr   Manager handle.
 * @param   addr7 7-bit I²C address.
 * @return  SM_OK if found+removed, SM_ERROR otherwise.
 */
SM_Status_t SensorManager_Remove(SensorManager_t *mgr,
                                 uint8_t          addr7);

/**
 * @brief   Reconfigure an existing sensor (gain, range, calibration).
 * @param   mgr     Manager handle.
 * @param   addr7   7-bit I²C address.
 * @param   cmd_id  One of CMD_SET_… from protocol.h.
 * @param   param   Parameter byte for the command.
 * @return  SM_OK or SM_ERROR.
 */
SM_Status_t SensorManager_Configure(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint8_t          cmd_id,
                                    uint8_t          param);

/**
 * @brief   Read back a configuration field from a running sensor.
 * @param   mgr        Manager handle.
 * @param   addr7      7-bit I²C address of the sensor.
 * @param   field_id   Driver-local field ID.
 * @param   out_value  Pointer to a uint8_t to receive the value.
 * @return  SM_OK on success; SM_ERROR if not found.
 */
SM_Status_t SensorManager_GetConfig(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint8_t          field_id,
                                    uint8_t         *out_value);

/**
 * @brief   Read up to `max_samples` from the sensor’s FIFO.
 * @param   mgr          Manager handle.
 * @param   addr7        7-bit I²C address.
 * @param   out          Array to receive SensorSample_t entries.
 * @param   max_samples  Capacity of `out[]`.
 * @param   got          Returns number of samples read.
 * @return  SM_OK if ≥1 sample returned, SM_ERROR otherwise.
 */
SM_Status_t SensorManager_Read(SensorManager_t *mgr,
                               uint8_t          addr7,
                               SensorSample_t   out[],
                               uint32_t         max_samples,
                               uint32_t        *got);

/**
 * @brief   List all active sensors.
 * @param   mgr   Manager handle.
 * @param   list  Array of SM_Entry_t to fill.
 * @param   max   Capacity of `list[]` (SM_MAX_SENSORS).
 * @return  Number of entries written.
 */
uint8_t SensorManager_List(SensorManager_t *mgr,
                           SM_Entry_t       list[],
                           uint8_t          max);

/**
 * @brief   Change the polling interval of a given sensor task.
 * @param   mgr            SensorManager handle returned from SensorManager_Create().
 * @param   addr7          7-bit I²C address of the target sensor.
 * @param   new_period_ms  New polling interval in milliseconds.
 * @return  SM_OK if the sensor was found and updated, SM_ERROR otherwise.
 */
SM_Status_t SensorManager_SetPeriod(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint32_t         new_period_ms);

/**
 * @brief Retrieve the SensorTask handle for a given sensor address.
 *
 * This function returns the SensorTaskHandle_t* associated with a specific
 * 7-bit I²C address, or NULL if the address is not registered.
 *
 * @param mgr   Pointer to the SensorManager instance.
 * @param addr7 7-bit I²C address of the sensor.
 * @return SensorTaskHandle_t* for the sensor, or NULL if not found.
 */
SensorTaskHandle_t *SensorManager_GetTask(SensorManager_t *mgr, uint8_t addr7);

/**
 * @brief Get the number of active sensors managed by the SensorManager.
 *
 * This function returns how many sensor entries are currently registered
 * and managed by the given SensorManager instance.
 *
 * @param mgr Pointer to the SensorManager instance.
 * @return Number of active sensors (0 if mgr is NULL).
 */
uint8_t SensorManager_GetCount(SensorManager_t *mgr);

/**
 * @brief Get a pointer to a sensor entry by its index.
 *
 * This function returns a pointer to the internal SM_Entry_t structure
 * at the specified index. Use this to inspect sensor metadata or task handles.
 *
 * @param mgr   Pointer to the SensorManager instance.
 * @param index Index of the sensor (must be < SensorManager_GetCount()).
 * @return Pointer to the SM_Entry_t entry, or NULL if invalid.
 */
SM_Entry_t *SensorManager_GetByIndex(SensorManager_t *mgr, uint8_t index);

#endif // SENSOR_MANAGER_H
