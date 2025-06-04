/* Auto-generated from ina219.json; do not edit! */
#include "drivers/ina219.h"
#include "stm32l4xx_hal.h"

HAL_StatusTypeDef INA219_SetGain(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, INA219_GAIN_t value) {
    uint8_t buf[2] = { 0x00, (uint8_t)value };
    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 2, 100);
}

HAL_StatusTypeDef INA219_SetBusRange(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, INA219_BUS_RANGE_t value) {
    uint8_t buf[2] = { 0x00, (uint8_t)value };
    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 2, 100);
}

HAL_StatusTypeDef INA219_SetCalibration(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, INA219_CALIBRATION_t value) {
    uint8_t buf[3] = {
        0x05,
        (uint8_t)(value >> 8),
        (uint8_t)(value & 0xFF)
    };
    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 3, 100);
}

HAL_StatusTypeDef INA219_SetPeriod(
    I2C_HandleTypeDef *hi2c,
    uint16_t           addr8bit,
    INA219_PERIOD_t   value
) {
    (void)hi2c; (void)addr8bit; (void)value;
    return HAL_OK;  // Period is handled internally
}

HAL_StatusTypeDef INA219_ReadGain(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, uint8_t *out) {
    uint8_t cmd = 0x00;
    uint8_t data[1];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 1, 100) != HAL_OK) return HAL_ERROR;
    *out = data[0];
    return HAL_OK;
}

HAL_StatusTypeDef INA219_ReadBusRange(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, uint8_t *out) {
    uint8_t cmd = 0x00;
    uint8_t data[1];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 1, 100) != HAL_OK) return HAL_ERROR;
    *out = data[0];
    return HAL_OK;
}

HAL_StatusTypeDef INA219_ReadCalibration(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, uint16_t *out) {
    uint8_t cmd = 0x05;
    uint8_t data[2];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 2, 100) != HAL_OK) return HAL_ERROR;
    uint16_t raw = (data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw;
    return HAL_OK;
}

HAL_StatusTypeDef INA219_ReadBusVoltageMv(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, uint16_t *out) {
    uint8_t cmd = REG_BUS_VOLTAGE_MV;
    uint8_t data[2];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 2, 100) != HAL_OK) return HAL_ERROR;
    uint16_t raw = (data[0] << 8) | data[1];
    raw = raw >> 3;
    raw = raw & 0x1FFF;
    *out = raw * 4;
    return HAL_OK;
}
HAL_StatusTypeDef INA219_ReadShuntVoltageUv(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, int16_t *out) {
    uint8_t cmd = REG_SHUNT_VOLTAGE_UV;
    uint8_t data[2];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 2, 100) != HAL_OK) return HAL_ERROR;
    uint16_t raw = (data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw * 10;
    return HAL_OK;
}
HAL_StatusTypeDef INA219_ReadCurrentUa(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, int16_t *out) {
    uint8_t cmd = REG_CURRENT_UA;
    uint8_t data[2];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 2, 100) != HAL_OK) return HAL_ERROR;
    uint16_t raw = (data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw * 1;
    return HAL_OK;
}
HAL_StatusTypeDef INA219_ReadPowerMw(
I2C_HandleTypeDef *hi2c, uint16_t addr8bit, uint16_t *out) {
    uint8_t cmd = REG_POWER_MW;
    uint8_t data[2];
    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;
    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, 2, 100) != HAL_OK) return HAL_ERROR;
    uint16_t raw = (data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw * 20;
    return HAL_OK;
}