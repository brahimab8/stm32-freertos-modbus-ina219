#pragma once
#include <stdint.h>

// Minimal HAL_StatusTypeDef and return codes
typedef int HAL_StatusTypeDef;
#define HAL_OK    0
#define HAL_ERROR 1

// Fake I2C handle type (unused in stub)
typedef struct {
    int dummy;
} I2C_HandleTypeDef;
