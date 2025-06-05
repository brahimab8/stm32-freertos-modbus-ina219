#include "hal_if.h"
#include <string.h>

halif_handle_t halif_i2c_init(uint32_t i2c_bus, uint32_t baudrate) {
    (void)i2c_bus;
    (void)baudrate;
    return (halif_handle_t)0x1;  // dummy non‐NULL handle
}

halif_status_t halif_i2c_write(
    halif_handle_t handle,
    uint8_t        device_addr,
    const uint8_t *data,
    uint16_t       length,
    uint32_t       timeout_ms
) {
    (void)handle;
    (void)device_addr;
    (void)data;
    (void)length;
    (void)timeout_ms;
    return HALIF_OK;   // maps to HAL_OK
}

halif_status_t halif_i2c_read(
    halif_handle_t handle,
    uint8_t        device_addr,
    uint8_t       *data,
    uint16_t       length,
    uint32_t       timeout_ms
) {
    (void)handle;
    (void)device_addr;
    (void)timeout_ms;
    memset(data, 0, length);
    return HALIF_OK;   // maps to HAL_OK
}
