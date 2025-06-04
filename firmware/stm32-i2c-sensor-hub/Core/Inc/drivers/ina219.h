/* Auto-generated from ina219.json; do not edit! */
#pragma once
#include "stm32l4xx_hal.h"
#include <stdint.h>

typedef uint8_t INA219_PERIOD_t;
typedef enum {
    INA219_GAIN_40MV = 0,
    INA219_GAIN_80MV = 1,
    INA219_GAIN_160MV = 2,
    INA219_GAIN_320MV = 3,
} INA219_GAIN_t;
typedef uint8_t INA219_BUS_RANGE_t;
typedef uint16_t INA219_CALIBRATION_t;
typedef uint8_t INA219_ALL_t[4];
#define REG_GAIN                 0x00
#define REG_BUS_RANGE            0x00
#define REG_CALIBRATION          0x05

#define REG_BUS_VOLTAGE_MV       0x02
#define REG_SHUNT_VOLTAGE_UV     0x01
#define REG_CURRENT_UA           0x04
#define REG_POWER_MW             0x03

// Payload-bit definitions (each bit selects one field)
#define BIT_BUS_VOLTAGE_MV         (1 << 0)
#define BIT_SHUNT_VOLTAGE_UV       (1 << 1)
#define BIT_CURRENT_UA             (1 << 2)
#define BIT_POWER_MW               (1 << 3)

/**
 * @brief Write to register 0x00 (set gain).
 */
HAL_StatusTypeDef INA219_SetGain(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    INA219_GAIN_t         value
);

/**
 * @brief Read gain from register 0x00.
 */
HAL_StatusTypeDef INA219_ReadGain(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    uint8_t *out
);

/**
 * @brief Write to register 0x00 (set bus_range).
 */
HAL_StatusTypeDef INA219_SetBusRange(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    INA219_BUS_RANGE_t         value
);

/**
 * @brief Read bus_range from register 0x00.
 */
HAL_StatusTypeDef INA219_ReadBusRange(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    uint8_t *out
);

/**
 * @brief Write to register 0x05 (set calibration).
 */
HAL_StatusTypeDef INA219_SetCalibration(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    INA219_CALIBRATION_t         value
);

/**
 * @brief Read calibration from register 0x05.
 */
HAL_StatusTypeDef INA219_ReadCalibration(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    uint16_t *out
);

/**
 * @brief Set period (handled internally; no register).
 */
HAL_StatusTypeDef INA219_SetPeriod(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    INA219_PERIOD_t         value
);

// Reads bus_voltage_mV from register 0x02
HAL_StatusTypeDef INA219_ReadBusVoltageMv(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    uint16_t           *out
);

// Reads shunt_voltage_uV from register 0x01
HAL_StatusTypeDef INA219_ReadShuntVoltageUv(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    int16_t           *out
);

// Reads current_uA from register 0x04
HAL_StatusTypeDef INA219_ReadCurrentUa(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    int16_t           *out
);

// Reads power_mW from register 0x03
HAL_StatusTypeDef INA219_ReadPowerMw(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    uint16_t           *out
);
