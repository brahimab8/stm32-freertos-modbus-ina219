#ifndef SENSOR_TASK_H
#define SENSOR_TASK_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/** Maximum payload bytes per sample (must match real) */
#define SENSOR_MAX_PAYLOAD  10

// “Raw sample” stub
typedef struct {
    uint32_t tick;                       
    uint8_t  buf[SENSOR_MAX_PAYLOAD];    
    uint8_t  len;                        
} SensorSample_t;

/** V‐table stub for a sensor driver **/
typedef struct {
    /** init(ctx): returns HAL_OK or HAL_ERROR **/
    int  (*init)(void *ctx);
    /** read(ctx, out_buf, out_len): returns HAL_OK or HAL_ERROR **/
    int  (*read)(void *ctx, uint8_t out_buf[SENSOR_MAX_PAYLOAD], uint8_t *out_len);
    /** sample_size(ctx): returns number of bytes **/
    uint8_t (*sample_size)(void *ctx);
    /** read_config_bytes: returns true/false **/
    bool (*read_config_bytes)(void   *ctx,
                              uint8_t field_id,
                              uint8_t *out_buf,
                              size_t  *out_len);
} SensorDriver_t;

/** Opaque handle for creating tasks—never actually used in these tests **/
typedef void SensorTaskHandle_t;

#endif // SENSOR_TASK_H
