#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include "sensor_task.h"   // brings in SensorSample_t and SensorDriver_t

#include <stdint.h>

/** Maximum active sensors (must match real SM_MAX_SENSORS) **/
#define SM_MAX_SENSORS 8

/**
 * Minimal entry struct so that BuildList and test_generated_drivers compile.
 * We only need type_code and addr7 here.
 */
typedef struct {
    uint8_t  sensor_id;    ///< index (0..count-1)
    uint8_t  type_code;    ///< e.g. SENSOR_TYPE_INA219
    uint8_t  addr7;        ///< 7-bit I²C address
    uint32_t period_ms;    ///< poll interval
    const SensorDriver_t *drv;   ///< vtable pointer (from sensor_task.h)
    void     *ctx;         ///< opaque context
    void     *task;        ///< opaque task handle
} SM_Entry_t;

#endif // SENSOR_MANAGER_H
