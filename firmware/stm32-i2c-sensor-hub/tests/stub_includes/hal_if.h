#pragma once
#include "stm32l4xx_hal.h"   // brings in: typedef int HAL_StatusTypeDef; #define HAL_OK 0, HAL_ERROR 1
#include <stdint.h>

// Opaque handle type
typedef void *halif_handle_t;

// Must match exactly the real enum in Inc/hal_if.h, but map to HAL_OK/HAL_ERROR:
typedef enum {
    HALIF_OK    = HAL_OK,
    HALIF_ERROR = HAL_ERROR
} halif_status_t;

// Function signatures must also match exactly:
halif_handle_t halif_i2c_init(uint32_t i2c_bus, uint32_t baudrate);

halif_status_t halif_i2c_write(
    halif_handle_t handle,
    uint8_t        device_addr,
    const uint8_t *data,
    uint16_t       length,
    uint32_t       timeout_ms
);

halif_status_t halif_i2c_read(
    halif_handle_t handle,
    uint8_t        device_addr,
    uint8_t       *data,
    uint16_t       length,
    uint32_t       timeout_ms
);
