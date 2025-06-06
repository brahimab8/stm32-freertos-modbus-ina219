#ifndef SENSOR_TASK_H
#define SENSOR_TASK_H

#include "cmsis_os.h"
#include "stm32l4xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/** Maximum payload bytes per sample*/
#define SENSOR_MAX_PAYLOAD  10

/** Raw sample from a sensor, with timestamp and payload bytes. */
typedef struct {
    uint32_t tick;                        /**< OS tick count at read time */
    uint8_t  buf[SENSOR_MAX_PAYLOAD];     /**< Packed sensor data */
    uint8_t  len;                         /**< Number of valid bytes in buf */
} SensorSample_t;

/** V-table for a sensor driver: init + read callback, and its payload size. */
typedef struct {
    /**
     * @brief   Initialize the sensor (e.g. set I²C address, configure registers).
     * @param   ctx  Opaque driver context (driver-specific).
     * @return  HAL_OK on success, HAL_ERROR on failure.
     */
    HAL_StatusTypeDef (*init)(void *ctx);

    /**
     * @brief   Read one sample from the sensor.
     * @param   ctx      Opaque driver context.
     * @param   out_buf  Buffer to receive up to SENSOR_MAX_PAYLOAD bytes.
     * @param   out_len  Returns actual byte count written to out_buf.
     * @return  HAL_OK if read succeeded, HAL_ERROR otherwise.
     */
    HAL_StatusTypeDef (*read)(void *ctx,
                              uint8_t out_buf[SENSOR_MAX_PAYLOAD],
                              uint8_t *out_len);

    /**function pointer: Number of payload bytes produced by this driver on each read. */
    uint8_t           (*sample_size)(void *ctx);

    /**
     * @brief Read one or more bytes for a given configuration field
     * @param ctx       Pointer to that sensor's context struct
     * @param field     The CMD_GET_… opcode
     * @param out_buf   Buffer where to write up to N bytes
     * @param out_len   Pointer to size_t where we write "how many bytes we returned"
     * @return true if successful, false otherwise
     */
    bool (*read_config_bytes)(void *ctx,
                            uint8_t field,
                            uint8_t *out_buf,
                            size_t *out_len);


} SensorDriver_t;

/** Opaque handle for a SensorTask instance. */
typedef struct SensorTaskHandle_t SensorTaskHandle_t;

/**
 * @brief   Create and start a FreeRTOS task that polls a sensor periodically.
 * @param   driver       Pointer to the driver’s v-table.
 * @param   ctx          Opaque driver context (passed to init/read).
 * @param   period_ms    Poll interval in milliseconds.
 * @param   busMutex     Mutex protecting shared I²C bus.
 * @param   queue_depth  Number of samples to buffer in the FIFO.
 * @return  Handle to the created task, or NULL on error.
 */
SensorTaskHandle_t *SensorTask_Create(const SensorDriver_t *driver,
                                      void                 *ctx,
                                      uint32_t              period_ms,
                                      osMutexId_t           busMutex,
                                      uint32_t              queue_depth);

/**
 * @brief   Delete a SensorTask, free its queue and resources.
 * @param   h  Handle returned by SensorTask_Create.
 */
void SensorTask_Destroy(SensorTaskHandle_t *h);

/**
 * @brief   Non-blocking read of up to `max` samples from the task’s queue.
 * @param   h       Task handle.
 * @param   out     Array to receive SensorSample_t entries.
 * @param   max     Maximum number of samples to read.
 * @param   got     Returns actual number of samples read.
 * @return  HAL_OK if at least one sample was returned, HAL_ERROR otherwise.
 */
HAL_StatusTypeDef SensorTask_ReadSamples(SensorTaskHandle_t *h,
                                         SensorSample_t     out[],
                                         uint32_t           max,
                                         uint32_t          *got);

/**
 * @brief   Discard and free all pending samples in the queue.
 * @param   h  Task handle.
 */
void SensorTask_Flush(SensorTaskHandle_t *h);

/**
 * @brief   Return the per-sample payload size produced by the driver.
 * @param   h  Task handle.
 * @return  Number of bytes each sample contains (<= SENSOR_MAX_PAYLOAD).
 */
uint8_t SensorTask_GetSampleSize(const SensorTaskHandle_t *h);

/**
 * @brief   Change the polling interval of an existing SensorTask.
 * @param   h           SensorTask handle returned from SensorTask_Create().
 * @param   period_ms   New interval in milliseconds.
 */
void SensorTask_UpdatePeriod(SensorTaskHandle_t *h, uint32_t period_ms);

/**
 * @brief   Expose thread handle.
 * @param   h           SensorTask handle 
 */
osThreadId_t SensorTask_GetThread(SensorTaskHandle_t *h);

#endif // SENSOR_TASK_H
