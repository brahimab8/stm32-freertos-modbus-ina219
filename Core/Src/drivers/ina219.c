#include "drivers/ina219.h"

#define REG_CONFIG       0x00
#define REG_SHUNT_VOLT   0x01
#define REG_BUS_VOLTAGE  0x02
#define REG_CURRENT      0x04
#define REG_CALIBRATION  0x05

HAL_StatusTypeDef INA219_SetConfig(I2C_HandleTypeDef *hi2c,
                                   uint16_t addr8bit,
                                   INA219_Gain_t gain,
                                   INA219_BusRange_t range)
{
  uint16_t cfg = (range == INA219_BVOLTAGERANGE_32V ? (1 << 13) : 0)
               | ((gain & 3) << 11)
               | 0x019F;  // default ADC & calibration bits

  uint8_t buf[3] = {
    REG_CONFIG,
    (uint8_t)(cfg >> 8),
    (uint8_t)(cfg & 0xFF)
  };
  return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 3, HAL_MAX_DELAY);
}

HAL_StatusTypeDef INA219_SetCalibration(I2C_HandleTypeDef *hi2c,
                                        uint16_t addr8bit,
                                        uint16_t calValue)
{
  uint8_t buf[3] = {
    REG_CALIBRATION,
    (uint8_t)(calValue >> 8),
    (uint8_t)(calValue & 0xFF)
  };
  return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 3, HAL_MAX_DELAY);
}

HAL_StatusTypeDef INA219_ReadBusVoltage_mV(I2C_HandleTypeDef *hi2c,
                                           uint16_t addr8bit,
                                           uint16_t *mV)
{
  uint8_t cmd = REG_BUS_VOLTAGE, data[2];
  if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, HAL_MAX_DELAY) != HAL_OK)
    return HAL_ERROR;
  if (HAL_I2C_Master_Receive (hi2c, addr8bit, data, 2, HAL_MAX_DELAY) != HAL_OK)
    return HAL_ERROR;

  uint16_t raw = (data[0] << 8) | data[1];
  *mV = (raw >> 3) * 4;  // 4 mV LSB
  return HAL_OK;
}

HAL_StatusTypeDef INA219_ReadShuntVoltage_uV(I2C_HandleTypeDef *hi2c,
                                             uint16_t addr8bit,
                                             int32_t *uV)
{
  uint8_t cmd = REG_SHUNT_VOLT, data[2];
  if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, HAL_MAX_DELAY) != HAL_OK)
    return HAL_ERROR;
  if (HAL_I2C_Master_Receive (hi2c, addr8bit, data, 2, HAL_MAX_DELAY) != HAL_OK)
    return HAL_ERROR;

  int16_t raw = (data[0] << 8) | data[1];
  *uV = raw * 10;  // 10 µV LSB
  return HAL_OK;
}

HAL_StatusTypeDef INA219_ReadCurrent_uA(I2C_HandleTypeDef *hi2c,
                                        uint16_t addr8bit,
                                        int32_t *uA)
{
  uint8_t cmd = REG_CURRENT, data[2];
  if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, HAL_MAX_DELAY) != HAL_OK)
    return HAL_ERROR;
  if (HAL_I2C_Master_Receive (hi2c, addr8bit, data, 2, HAL_MAX_DELAY) != HAL_OK)
    return HAL_ERROR;

  int16_t raw = (data[0] << 8) | data[1];
  *uA = raw;  // current LSB = calibration LSB
  return HAL_OK;
}
