#ifndef INA219_H
#define INA219_H

#include "stm32l4xx_hal.h"
#include <stdint.h>

/**
 * @brief   Programmable PGA gain settings for INA219
 */
typedef enum {
    INA219_GAIN_1_40MV = 0,  /**< Gain = 1, LSB = 40 mV */
    INA219_GAIN_2_80MV,     /**< Gain = 2, LSB = 80 mV */
    INA219_GAIN_4_160MV,    /**< Gain = 4, LSB = 160 mV */
    INA219_GAIN_8_320MV     /**< Gain = 8, LSB = 320 mV */
} INA219_Gain_t;

/**
 * @brief   Bus voltage range selection for INA219
 */
typedef enum {
    INA219_BVOLTAGERANGE_16V = 0,  /**< 0–16 V range */
    INA219_BVOLTAGERANGE_32V      /**< 0–32 V range */
} INA219_BusRange_t;

/**
 * @brief   Write to the CONFIG register (sets gain & bus range)
 * @param   hi2c    Pointer to initialized I2C handle
 * @param   addr8   8-bit I²C address (7-bit << 1)
 * @param   gain    One of INA219_Gain_t
 * @param   range   One of INA219_BusRange_t
 * @return  HAL_OK on success, HAL_ERROR on bus or device error
 */
HAL_StatusTypeDef INA219_SetConfig(I2C_HandleTypeDef *hi2c,
                                   uint16_t           addr8,
                                   INA219_Gain_t      gain,
                                   INA219_BusRange_t  range);

/**
 * @brief   Write to the CALIBRATION register
 * @param   hi2c      I2C handle
 * @param   addr8     8-bit I²C address
 * @param   calValue  Calibration value (LSB)
 * @return  HAL_OK on success
 */
HAL_StatusTypeDef INA219_SetCalibration(I2C_HandleTypeDef *hi2c,
                                        uint16_t           addr8,
                                        uint16_t           calValue);

/**
 * @brief   Read bus voltage in millivolts
 * @param   hi2c    I2C handle
 * @param   addr8   8-bit I²C address
 * @param   mV      Output pointer for voltage in mV
 * @return  HAL_OK on success
 */
HAL_StatusTypeDef INA219_ReadBusVoltage_mV(I2C_HandleTypeDef *hi2c,
                                           uint16_t           addr8,
                                           uint16_t          *mV);

/**
 * @brief   Read shunt voltage in microvolts
 * @param   hi2c    I2C handle
 * @param   addr8   8-bit I²C address
 * @param   uV      Output pointer for voltage in µV
 * @return  HAL_OK on success
 */
HAL_StatusTypeDef INA219_ReadShuntVoltage_uV(I2C_HandleTypeDef *hi2c,
                                             uint16_t           addr8,
                                             int32_t           *uV);

/**
 * @brief   Read current in microamps (requires correct calibration)
 * @param   hi2c    I2C handle
 * @param   addr8   8-bit I²C address
 * @param   uA      Output pointer for current in µA
 * @return  HAL_OK on success
 */
HAL_StatusTypeDef INA219_ReadCurrent_uA(I2C_HandleTypeDef *hi2c,
                                        uint16_t           addr8,
                                        int32_t           *uA);

#endif // INA219_H
