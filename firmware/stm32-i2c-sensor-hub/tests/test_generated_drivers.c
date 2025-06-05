// A generic registry‐driven test that exercises every registered
// SensorDriverInfo_t.  It derives the correct “SET” opcode from each “GET”
// opcode by inspecting the ranges defined in protocol.h.

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

// Pull in command‐ID constants (CMD_GET_…, CMD_SET_…, ranges, etc.)
#include "config/protocol.h"

// Pull in the registry API (and, indirectly, every <sensor>_RegisterDriver()):
#include "driver_registry.h"

// Pull in HAL-IF so that init_ctx signatures compile. We’ll pass a dummy handle = NULL.
#include "hal_if.h"

int main(void) {
    // 1) Register all drivers via the “calls.inc” mechanism:
    DriverRegistry_InitAll();

    // 2) Grab the NULL-terminated array of descriptors:
    const SensorDriverInfo_t * const *all_drivers = SensorRegistry_All();
    assert(all_drivers != NULL);

    // 3) Verify there is at least one driver:
    int total = 0;
    while (all_drivers[total] != NULL) {
        total++;
    }
    assert(total > 0);
    printf("Found %d driver(s) in registry.\n\n", total);

    // 4) For each registered SensorDriverInfo_t, exercise the minimal contract:
    for (int idx = 0; all_drivers[idx] != NULL; idx++) {
        const SensorDriverInfo_t *info = all_drivers[idx];
        printf("→ Testing driver type_code = 0x%02X  (ctx_size = %zu)\n",
               info->type_code,
               info->ctx_size);

        // 4a) Allocate a zero-filled buffer of size ctx_size:
        void *ctx = malloc(info->ctx_size);
        assert(ctx != NULL);
        memset(ctx, 0, info->ctx_size);

        // 4b) Call init_ctx(ctx, /*dummy-handle*/ NULL, /*dummy-addr7*/ 0x42):
        info->init_ctx(ctx, (halif_handle_t)NULL, (uint8_t)0x42);

        // 4c) Grab the v-table for this driver:
        const SensorDriver_t *drv = info->get_driver();
        assert(drv != NULL);

        // 4d) Ensure init() is non-NULL, then call it:
        assert(drv->init != NULL);
        HAL_StatusTypeDef rc = drv->init(ctx);
        assert(rc == HAL_OK);

        // 4e) Ensure sample_size() is non-NULL, then call it and expect > 0:
        assert(drv->sample_size != NULL);
        uint8_t sz = drv->sample_size(ctx);
        assert(sz > 0);

        // 4f) Query valid config-field IDs, then test read & configure on each:
        size_t field_count = 0;
        const uint8_t *fields = info->get_config_fields(&field_count);
        // If get_config_fields() returns NULL but count == 0, that’s fine, too:
        assert(fields != NULL || field_count == 0);

        for (size_t f = 0; f < field_count; f++) {
            uint8_t get_id = fields[f];
            uint8_t val    = 0;
            bool    ok;

            // (i) Test read_config(GET_xxx):
            printf("    • read_config for GET=0x%02X… ", get_id);
            ok = info->read_config(ctx, get_id, &val);
            if (!ok) {
                printf("FAILED (read_config returned false)\n");
                assert(ok == true);  // abort, showing get_id
            }
            printf("OK (returned value=0x%02X)\n", val);

            // (ii) Derive the matching SET opcode:
            uint8_t set_id = 0xFF;
            if (get_id >= CMD_CONFIG_GETTERS_START && get_id <= CMD_CONFIG_GETTERS_END) {
                // “[30..39] → [20..29]” by subtracting 10
                set_id = (uint8_t)(get_id - 
                           (CMD_CONFIG_GETTERS_START - CMD_CONFIG_SETTERS_START));
            }
            else if (get_id == CMD_GET_PAYLOAD_MASK) {
                // GET=6, SET=5
                set_id = CMD_SET_PAYLOAD_MASK;
            }
            else {
                // No SET exists for this GET. Skip configure() for this field.
                printf("    • (no matching SET for GET=0x%02X, skipping configure)\n", get_id);
                continue;
            }

            // (iii) Now call configure(SET_xxx, same val):
            printf("    • configure with SET=0x%02X (value=0x%02X)… ", set_id, val);
            ok = info->configure(ctx, set_id, val);
            if (!ok) {
                printf("FAILED (configure returned false)\n");
                assert(ok == true);  // abort, showing set_id & val
            }
            printf("OK\n");
        }

        free(ctx);
        printf("  [PASS] driver 0x%02X\n\n", info->type_code);
    }

    printf("All registered drivers passed the generic test!\n");
    return 0;
}
