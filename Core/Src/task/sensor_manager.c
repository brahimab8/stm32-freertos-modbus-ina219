#include "task/sensor_manager.h"
#include "driver_registry.h"  
#include <stdlib.h>
#include <string.h>

struct SensorManager {
    osMutexId_t        busMutex;
    I2C_HandleTypeDef *hi2c;
    uint8_t            count;
    SM_Entry_t         entries[SM_MAX_SENSORS];
};

SensorManager_t *SensorManager_Create(osMutexId_t busMutex,
                                      I2C_HandleTypeDef *hi2c)
{
    SensorManager_t *m = pvPortMalloc(sizeof(*m));
    if (!m) return NULL;
    m->busMutex = busMutex;
    m->hi2c     = hi2c;
    m->count    = 0;
    return m;
}

void SensorManager_Destroy(SensorManager_t *mgr)
{
    if (!mgr) return;
    for (uint8_t i = 0; i < mgr->count; ++i) {
        vPortFree(mgr->entries[i].ctx);
        SensorTask_Destroy(mgr->entries[i].task);
    }
    vPortFree(mgr);
}

SM_Status_t SensorManager_AddByType(SensorManager_t *mgr,
                                    uint8_t          type_code,
                                    uint8_t          addr7,
                                    uint32_t         period_ms)
{
    if (mgr->count >= SM_MAX_SENSORS) return SM_ERROR;

    // find registry entry
    const SensorDriverInfo_t *info = NULL;
    for (const SensorDriverInfo_t *r = sensor_driver_registry; r->type_code; ++r) {
        if (r->type_code == type_code) {
            info = r;
            break;
        }
    }
    if (!info) return SM_ERROR;

    // allocate & init context
    void *ctx = pvPortMalloc(info->ctx_size);
    if (!ctx) return SM_ERROR;
    info->init_ctx(ctx, mgr->hi2c, addr7);

    // get driver vtable
    const SensorDriver_t *drv = info->get_driver();

    // create the polling task
    SensorTaskHandle_t *task = SensorTask_Create(
        drv, ctx, period_ms, mgr->busMutex, QUEUE_DEPTH
    );
    if (!task) {
        vPortFree(ctx);
        return SM_ERROR;
    }

    // record entry
    SM_Entry_t *e = &mgr->entries[mgr->count];
    e->sensor_id = mgr->count;
    e->type_code = type_code;
    e->addr7     = addr7;
    e->drv       = drv;
    e->ctx       = ctx;
    e->task      = task;
    mgr->count++;
    return SM_OK;
}

SM_Status_t SensorManager_Remove(SensorManager_t *mgr, uint8_t addr7)
{
    for (uint8_t i = 0; i < mgr->count; ++i) {
        if (mgr->entries[i].addr7 == addr7) {
            vPortFree(mgr->entries[i].ctx);
            SensorTask_Destroy(mgr->entries[i].task);
            memmove(&mgr->entries[i],
                    &mgr->entries[i+1],
                    (mgr->count - i - 1) * sizeof(SM_Entry_t));
            mgr->count--;
            return SM_OK;
        }
    }
    return SM_ERROR;
}

SM_Status_t SensorManager_Configure(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint8_t          cmd_id,
                                    uint8_t          param)
{
    // Find the matching sensor entry
    for (uint8_t i = 0; i < mgr->count; ++i) {
        SM_Entry_t *e = &mgr->entries[i];
        if (e->addr7 != addr7) continue;

        // Find matching driver info in the registry
        for (const SensorDriverInfo_t *r = sensor_driver_registry; r->type_code; ++r) {
            if (r->type_code == e->type_code)
                return r->configure(e->ctx, cmd_id, param);
        }

        // Driver not found
        return SM_ERROR;
    }

    // Sensor not found
    return SM_ERROR;
}

SM_Status_t SensorManager_Read(SensorManager_t *mgr,
                               uint8_t          addr7,
                               SensorSample_t   out[],
                               uint32_t         max_samples,
                               uint32_t        *got)
{
    for (uint8_t i = 0; i < mgr->count; ++i) {
        if (mgr->entries[i].addr7 == addr7) {
            return (SensorTask_ReadSamples(
                      mgr->entries[i].task, out, max_samples, got
                    ) == HAL_OK) ? SM_OK : SM_ERROR;
        }
    }
    return SM_ERROR;
}

uint8_t SensorManager_List(SensorManager_t *mgr, SM_Entry_t list[], uint8_t max)
{
    uint8_t n = (mgr->count < max ? mgr->count : max);
    memcpy(list, mgr->entries, n * sizeof(SM_Entry_t));
    return n;
}

SM_Status_t SensorManager_SetPeriod(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint32_t         new_period_ms)
{
    for (uint8_t i = 0; i < mgr->count; ++i) {
        SM_Entry_t *e = &mgr->entries[i];
        if (e->addr7 == addr7) {
            SensorTask_UpdatePeriod(e->task, new_period_ms);
            return SM_OK;
        }
    }
    return SM_ERROR;
}

SensorTaskHandle_t *SensorManager_GetTask(SensorManager_t *mgr, uint8_t addr7) {
    for (uint8_t i = 0; i < mgr->count; ++i) {
        if (mgr->entries[i].addr7 == addr7)
            return mgr->entries[i].task;
    }
    return NULL;
}
