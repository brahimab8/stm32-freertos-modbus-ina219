/* Manually edited ina219.h; */
#pragma once

#include <hal_if.h>
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
halif_status_t INA219_SetGain(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_GAIN_t  value
);

/**
 * @brief Read gain from register 0x00.
 */
halif_status_t INA219_ReadGain(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    uint8_t       *out
);

/**
 * @brief Write to register 0x00 (set bus_range).
 */
halif_status_t INA219_SetBusRange(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    INA219_BUS_RANGE_t value
);

/**
 * @brief Read bus_range from register 0x00.
 */
halif_status_t INA219_ReadBusRange(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    uint8_t         *out
);

/**
 * @brief Write to register 0x05 (set calibration).
 */
halif_status_t INA219_SetCalibration(
    halif_handle_t      h_i2c,
    uint8_t             addr7bit,
    INA219_CALIBRATION_t value
);

/**
 * @brief Read calibration from register 0x05.
 */
halif_status_t INA219_ReadCalibration(
    halif_handle_t      h_i2c,
    uint8_t             addr7bit,
    uint16_t           *out
);

/**
 * @brief Set period (handled internally; no register).
 */
halif_status_t INA219_SetPeriod(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_PERIOD_t value
);

/**
 * @brief Reads bus_voltage_mV from register 0x02.
 */
halif_status_t INA219_ReadBusVoltageMv(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    uint16_t      *out
);

/**
 * @brief Reads shunt_voltage_uV from register 0x01.
 */
halif_status_t INA219_ReadShuntVoltageUv(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    int16_t       *out
);

/**
 * @brief Reads current_uA from register 0x04.
 */
halif_status_t INA219_ReadCurrentUa(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    int16_t       *out
);

/**
 * @brief Reads power_mW from register 0x03.
 */
halif_status_t INA219_ReadPowerMw(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    uint16_t      *out
);
