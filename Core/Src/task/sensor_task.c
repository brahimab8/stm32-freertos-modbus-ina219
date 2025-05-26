#include "task/sensor_task.h"
#include <stdlib.h>
#include <string.h>

struct SensorTaskHandle_t {
    const SensorDriver_t *drv;
    void                 *ctx;
    uint32_t              period_ms;
    osMutexId_t           busMutex;
    osMessageQueueId_t    queue;
    osThreadId_t          thread;
    uint32_t              queue_depth;

};

static void thread_fn(void *arg) {
    SensorTaskHandle_t *h = arg;
    h->drv->init(h->ctx);

    uint32_t next = osKernelGetTickCount();
    for (;;) {
        next += h->period_ms;

        uint8_t           tmpbuf[SENSOR_MAX_PAYLOAD];
        uint8_t           tmplen = 0;
        HAL_StatusTypeDef st;

        osMutexAcquire(h->busMutex, osWaitForever);
          st = h->drv->read(h->ctx, tmpbuf, &tmplen);
        osMutexRelease(h->busMutex);

        if (st == HAL_OK && tmplen <= SENSOR_MAX_PAYLOAD) {
            SensorSample_t samp = {
                .tick = osKernelGetTickCount(),
                .len  = tmplen,
            };
            memcpy(samp.buf, tmpbuf, tmplen);

            // if queue full, drop oldest
            if (osMessageQueueGetCount(h->queue)
                >= h->queue_depth)
            {
                SensorSample_t drop;
                osMessageQueueGet(h->queue, &drop, NULL, 0);
            }
            osMessageQueuePut(h->queue, &samp, 0, 0);
        }

        osDelayUntil(next);
    }
}

SensorTaskHandle_t *SensorTask_Create(const SensorDriver_t *driver,
                                      void                 *ctx,
                                      uint32_t              period_ms,
                                      osMutexId_t           busMutex,
                                      uint32_t              queue_depth)
{
    if (!driver || !driver->init || !driver->read
        || !ctx || period_ms == 0 || !busMutex
        || queue_depth == 0 || driver->sample_size == 0
        || driver->sample_size > SENSOR_MAX_PAYLOAD)
    {
        return NULL;
    }

    SensorTaskHandle_t *h = pvPortMalloc(sizeof(*h));
    if (!h) return NULL;
    *h = (SensorTaskHandle_t){
        .drv       = driver,
        .ctx       = ctx,
        .period_ms = period_ms,
        .busMutex  = busMutex,
        .queue_depth = queue_depth,
    };

    h->queue = osMessageQueueNew(queue_depth,
                                 sizeof(SensorSample_t),
                                 NULL);
    if (!h->queue) { vPortFree(h); return NULL; }

    osThreadAttr_t attr = {
        .name       = "SensorTask",
        .stack_size = 512,
        .priority   = osPriorityBelowNormal
    };
    h->thread = osThreadNew(thread_fn, h, &attr);
    if (!h->thread) {
        osMessageQueueDelete(h->queue);
        vPortFree(h);
        return NULL;
    }

    return h;
}

void SensorTask_Destroy(SensorTaskHandle_t *h) {
    if (!h) return;
    osThreadTerminate(h->thread);
    osMessageQueueDelete(h->queue);
    vPortFree(h);
}

HAL_StatusTypeDef SensorTask_ReadSamples(SensorTaskHandle_t *h,
                                         SensorSample_t     out[],
                                         uint32_t           max,
                                         uint32_t          *got)
{
    if (!h || !out || max == 0 || !got) {
        return HAL_ERROR;
    }

    uint32_t count = 0;
    SensorSample_t samp;
    while (count < max &&
           osMessageQueueGet(h->queue, &samp, NULL, 0) == osOK)
    {
        out[count++] = samp;
    }

    if (count == 0) {
        return HAL_ERROR;
    }
    *got = count;
    return HAL_OK;
}

void SensorTask_Flush(SensorTaskHandle_t *h) {
    if (!h) return;
    SensorSample_t samp;
    while (osMessageQueueGet(h->queue, &samp, NULL, 0) == osOK) {
        /* discard */
    }
}

uint8_t SensorTask_GetSampleSize(const SensorTaskHandle_t *h) {
    return h ? h->drv->sample_size : 0;
}

void SensorTask_UpdatePeriod(SensorTaskHandle_t *h, uint32_t period_ms)
{
    if (!h || period_ms == 0) {
        return;
    }
    h->period_ms = period_ms;
}
