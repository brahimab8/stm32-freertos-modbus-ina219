#ifndef RESPONSE_BUILDER_H
#define RESPONSE_BUILDER_H

#include "stm32l4xx_hal.h"
#include "task/sensor_manager.h"
#include <stdint.h>
#include <stddef.h>

size_t ResponseBuilder_BuildStatus(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status
);

/**
 * @brief Build a samples response frame.
 *
 * @param outbuf       Buffer to fill.
 * @param addr7        Target address.
 * @param samples      Pointer to array of SensorSample_t.
 * @param count        Number of samples in the array.
 * @param sample_size  Number of data bytes per sample (i.e. sizeof SensorSample_t.buf).
 * @return total frame length, or 0 on error.
 */
size_t ResponseBuilder_BuildSamples(
    uint8_t *outbuf,
    uint8_t  addr7,
    const SensorSample_t *samples,
    uint32_t count,
    uint8_t  sample_size
);

#endif // RESPONSE_BUILDER_H
