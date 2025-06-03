#include "task/sensor_manager.h"
#include "config/protocol.h"  
#include <string.h>

/* Internal SensorManager structure */
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
    memset(m, 0, sizeof(*m));
    m->busMutex = busMutex;
    m->hi2c     = hi2c;
    m->count    = 0;
    return m;
}

void SensorManager_Destroy(SensorManager_t *mgr)
{
    if (!mgr) return;
    for (uint8_t i = 0; i < mgr->count; ++i) {
        /* Free each driver‐context and terminate its task */
        if (mgr->entries[i].ctx) {
            vPortFree(mgr->entries[i].ctx);
        }
        if (mgr->entries[i].task) {
            SensorTask_Destroy(mgr->entries[i].task);
        }
    }

    vPortFree(mgr);
}

SM_Status_t SensorManager_AddByType(SensorManager_t *mgr,
                                    uint8_t          type_code,
                                    uint8_t          addr7,
                                    uint32_t         period_ms)
{
    if (!mgr) {
        return SM_ERROR;
    }

    /* Reject duplicates by I²C address */
    for (uint8_t i = 0; i < mgr->count; ++i) {
        if (mgr->entries[i].addr7 == addr7) {
            // already managing that address 
            return SM_ERROR;
        }
    }

    // check max capacity
    if (mgr->count >= SM_MAX_SENSORS) return SM_ERROR;
    
    /* Look up driver‐info at run‐time */
    const SensorDriverInfo_t *info = SensorRegistry_Find(type_code);
    if (!info) {
        return SM_ERROR; // No driver registered for this type_code
    }

    // allocate & init context
    void *ctx = pvPortMalloc(info->ctx_size);
    if (!ctx) return SM_ERROR;
    memset(ctx, 0, info->ctx_size);
    info->init_ctx(ctx, mgr->hi2c, addr7);

    // get driver vtable
    const SensorDriver_t *drv = info->get_driver();
    if (!drv) {
        vPortFree(ctx);
        return SM_ERROR;
    }

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
    e->period_ms = period_ms;
    e->drv       = drv;
    e->ctx       = ctx;
    e->task      = task;
    mgr->count++;
    return SM_OK;
}

SM_Status_t SensorManager_Remove(SensorManager_t *mgr, uint8_t addr7)
{
    if (!mgr) return SM_ERROR;

    for (uint8_t i = 0; i < mgr->count; ++i) {
        SM_Entry_t *e = &mgr->entries[i];
        if (e->addr7 == addr7) {
            /* Free this sensor’s context and terminate its task */
            if (e->ctx) {
                vPortFree(e->ctx);
            }
            if (e->task) {
                SensorTask_Destroy(e->task);
            }
            /* Shift remaining entries down by one */
            uint8_t move_count = mgr->count - i - 1;
            if (move_count > 0) {
                memmove(&mgr->entries[i],
                        &mgr->entries[i + 1],
                        move_count * sizeof(SM_Entry_t));
                /* Fix sensor_id fields of shifted entries */
                for (uint8_t j = i; j < mgr->count - 1; ++j) {
                    mgr->entries[j].sensor_id = j;
                }
            }
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
    if (!mgr) return SM_ERROR;
    
    // Find the matching sensor entry
    for (uint8_t i = 0; i < mgr->count; ++i) {
        SM_Entry_t *e = &mgr->entries[i];
        if (e->addr7 == addr7) {
            // Find matching driver info in the registry
            const SensorDriverInfo_t *info = SensorRegistry_Find(e->type_code);
            if (!info) {
                return SM_ERROR;
            }
            /* Call that sensor’s configure callback */
            bool ok = info->configure(e->ctx, cmd_id, param);
            return ok ? SM_OK : SM_ERROR;
        }
    }
    return SM_ERROR;
}

SM_Status_t SensorManager_GetConfig(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint8_t          field_id,
                                    uint8_t         *out_value)
{
    if (!mgr || !out_value) {
        return SM_ERROR;
    }

    /* Special‐case: if the client asks for “GET_PERIOD”, return our stored period. */
    if (field_id == CMD_GET_PERIOD) {
        for (uint8_t i = 0; i < mgr->count; ++i) {
            SM_Entry_t *e = &mgr->entries[i];
            if (e->addr7 == addr7) {
                *out_value = (uint8_t)(e->period_ms / 100);
                return SM_OK;
            }
        }
        return SM_ERROR;
    }

    /* Otherwise, delegate to the driver’s read_config(...) */
    for (uint8_t i = 0; i < mgr->count; ++i) {
        SM_Entry_t *e = &mgr->entries[i];
        if (e->addr7 == addr7) {
            const SensorDriverInfo_t *info = SensorRegistry_Find(e->type_code);
            if (!info) {
                return SM_ERROR;
            }
            bool ok = info->read_config(e->ctx, field_id, out_value);
            return ok ? SM_OK : SM_ERROR;
        }
    }
    return SM_ERROR;
}

SM_Status_t SensorManager_Read(SensorManager_t *mgr,
                               uint8_t          addr7,
                               SensorSample_t   out[],
                               uint32_t         max_samples,
                               uint32_t        *got)
{
    if (!mgr || !got) {
        return SM_ERROR;
    }
    for (uint8_t i = 0; i < mgr->count; ++i) {
        if (mgr->entries[i].addr7 == addr7) {
            return SensorTask_ReadSamples(
                       mgr->entries[i].task,
                       out,
                       max_samples,
                       got
                   ) == HAL_OK
                   ? SM_OK
                   : SM_ERROR;
        }
    }
    return SM_ERROR;
}

uint8_t SensorManager_List(SensorManager_t *mgr,
                           SM_Entry_t       list[],
                           uint8_t          max)
{
    if (!mgr || !list) return 0;
    uint8_t n = (mgr->count < max) ? mgr->count : max;
    memcpy(list, mgr->entries, n * sizeof(SM_Entry_t));
    return n;
}

SM_Status_t SensorManager_SetPeriod(SensorManager_t *mgr,
                                    uint8_t          addr7,
                                    uint32_t         new_period_ms)
{
    if (!mgr) return SM_ERROR;
    for (uint8_t i = 0; i < mgr->count; ++i) {
        SM_Entry_t *e = &mgr->entries[i];
        if (e->addr7 == addr7) {
            SensorTask_UpdatePeriod(e->task, new_period_ms);
            e->period_ms = new_period_ms;
            return SM_OK;
        }
    }
    return SM_ERROR;
}

SensorTaskHandle_t *SensorManager_GetTask(SensorManager_t *mgr, uint8_t addr7) {
    if (!mgr) return NULL;
    for (uint8_t i = 0; i < mgr->count; ++i) {
        if (mgr->entries[i].addr7 == addr7) {
            return mgr->entries[i].task;
        }
    }
    return NULL;
}

uint8_t SensorManager_GetCount(SensorManager_t *mgr) {
    return mgr ? mgr->count : 0;
}

SM_Entry_t *SensorManager_GetByIndex(SensorManager_t *mgr, uint8_t index) {
    if (!mgr || index >= mgr->count) return NULL;
    return &mgr->entries[index];
}
