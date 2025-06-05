#include "hal_if.h"
#include "stm32l4xx_hal.h"

// -----------------------------------------------------------------------------
// NOTE: This extern must match the I2C handle. (hi2c1; hi2c2 ...)
// -----------------------------------------------------------------------------
extern I2C_HandleTypeDef hi2c1;

halif_handle_t halif_i2c_init(uint32_t i2c_bus, uint32_t baudrate) {
    (void)baudrate;

    // Ignore i2c_bus for now; always return &hi2c1.
    // uncomment if multiple busses are supported:
    //   if (i2c_bus == 2) return (halif_handle_t)&hi2c2;
    return (halif_handle_t)&hi2c1;
}

halif_status_t halif_i2c_write(
    halif_handle_t handle,
    uint8_t        device_addr,
    const uint8_t *data,
    uint16_t       length,
    uint32_t       timeout_ms
) {
    HAL_StatusTypeDef hres = HAL_I2C_Master_Transmit(
        (I2C_HandleTypeDef *)handle,
        (uint16_t)(device_addr << 1),
        (uint8_t *)data,
        length,
        timeout_ms
    );
    return (hres == HAL_OK ? HALIF_OK : HALIF_ERROR);
}

halif_status_t halif_i2c_read(
    halif_handle_t handle,
    uint8_t        device_addr,
    uint8_t       *data,
    uint16_t       length,
    uint32_t       timeout_ms
) {
    HAL_StatusTypeDef hres = HAL_I2C_Master_Receive(
        (I2C_HandleTypeDef *)handle,
        (uint16_t)(device_addr << 1),
        data,
        length,
        timeout_ms
    );
    return (hres == HAL_OK ? HALIF_OK : HALIF_ERROR);
}
