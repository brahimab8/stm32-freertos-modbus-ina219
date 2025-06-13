/* Auto-generated ina219.h */
#pragma once

#include <hal_if.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif


/* --- Typedefs for config fields --- */
typedef uint8_t INA219_PERIOD_t;
typedef enum {
    INA219_GAIN_40MV = 0,
    INA219_GAIN_80MV = 1,
    INA219_GAIN_160MV = 2,
    INA219_GAIN_320MV = 3,
} INA219_GAIN_t;
typedef uint8_t INA219_BUS_RANGE_t;
typedef uint8_t INA219_SHUNT_MILLIOHM_t;
typedef uint8_t INA219_CURRENT_LSB_UA_t;
typedef uint16_t INA219_CALIBRATION_t;
typedef uint8_t INA219_ALL_t;

/* --- Typedefs for payload fields --- */
typedef uint16_t INA219_BUS_VOLTAGE_MV_t;
typedef int16_t INA219_SHUNT_VOLTAGE_UV_t;
typedef int16_t INA219_CURRENT_UA_t;
typedef uint16_t INA219_POWER_MW_t;

/* --- Register address defines --- */
#define REG_GAIN   0x00
#define REG_BUS_RANGE   0x00
#define REG_CALIBRATION   0x05
#define REG_BUS_VOLTAGE_MV   0x02
#define REG_SHUNT_VOLTAGE_UV   0x01
#define REG_CURRENT_UA   0x04
#define REG_POWER_MW   0x03

/* --- Payload field indices and bitmask defines for ina219 --- */
typedef enum {
        INA219_PAYLOAD_IDX_BUS_VOLTAGE_MV = 0,
        INA219_PAYLOAD_IDX_SHUNT_VOLTAGE_UV = 1,
        INA219_PAYLOAD_IDX_CURRENT_UA = 2,
        INA219_PAYLOAD_IDX_POWER_MW = 3,
        INA219_PAYLOAD_IDX_COUNT
} INA219_PayloadIndex_t;

#define INA219_PAYLOAD_BIT(field_idx)   (1U << (field_idx))

/* Individual field bit defines */
#define INA219_PAYLOAD_BIT_BUS_VOLTAGE_MV  (1U << INA219_PAYLOAD_IDX_BUS_VOLTAGE_MV)
#define INA219_PAYLOAD_BIT_SHUNT_VOLTAGE_UV  (1U << INA219_PAYLOAD_IDX_SHUNT_VOLTAGE_UV)
#define INA219_PAYLOAD_BIT_CURRENT_UA  (1U << INA219_PAYLOAD_IDX_CURRENT_UA)
#define INA219_PAYLOAD_BIT_POWER_MW  (1U << INA219_PAYLOAD_IDX_POWER_MW)

/* Default payload mask */
#define INA219_DEFAULT_PAYLOAD_MASK  (INA219_PAYLOAD_BIT_BUS_VOLTAGE_MV | INA219_PAYLOAD_BIT_SHUNT_VOLTAGE_UV)

/* --- Function prototypes for config fields --- */

/**
 * @brief  Set the period field.
 */
halif_status_t INA219_SetPeriod(
    halif_handle_t         h_i2c,
    uint8_t                addr7bit,
    INA219_PERIOD_t value
);


/**
 * @brief  Set the gain field.
 */
halif_status_t INA219_SetGain(
    halif_handle_t         h_i2c,
    uint8_t                addr7bit,
    INA219_GAIN_t value
);

/**
 * @brief  Read back the gain field.
 */
halif_status_t INA219_ReadGain(
    halif_handle_t              h_i2c,
    uint8_t                     addr7bit,
    INA219_GAIN_t *out
);

/**
 * @brief  Set the bus_range field.
 */
halif_status_t INA219_SetBusRange(
    halif_handle_t         h_i2c,
    uint8_t                addr7bit,
    INA219_BUS_RANGE_t value
);

/**
 * @brief  Read back the bus_range field.
 */
halif_status_t INA219_ReadBusRange(
    halif_handle_t              h_i2c,
    uint8_t                     addr7bit,
    INA219_BUS_RANGE_t *out
);

/**
 * @brief  Set the shunt_milliohm field.
 */
halif_status_t INA219_SetShuntMilliohm(
    halif_handle_t         h_i2c,
    uint8_t                addr7bit,
    INA219_SHUNT_MILLIOHM_t value
);


/**
 * @brief  Set the current_lsb_uA field.
 */
halif_status_t INA219_SetCurrentLsbUa(
    halif_handle_t         h_i2c,
    uint8_t                addr7bit,
    INA219_CURRENT_LSB_UA_t value
);


/**
 * @brief  Set the calibration field.
 */
halif_status_t INA219_SetCalibration(
    halif_handle_t         h_i2c,
    uint8_t                addr7bit,
    INA219_CALIBRATION_t value
);

/**
 * @brief  Read back the calibration field.
 */
halif_status_t INA219_ReadCalibration(
    halif_handle_t              h_i2c,
    uint8_t                     addr7bit,
    INA219_CALIBRATION_t *out
);

/* --- Function prototypes for payload fields --- */

/**
 * @brief  Read payload field bus_voltage_mV.
 */
halif_status_t INA219_ReadBusVoltageMv(
    halif_handle_t                h_i2c,
    uint8_t                       addr7bit,
    INA219_BUS_VOLTAGE_MV_t *out
);

/**
 * @brief  Read payload field shunt_voltage_uV.
 */
halif_status_t INA219_ReadShuntVoltageUv(
    halif_handle_t                h_i2c,
    uint8_t                       addr7bit,
    INA219_SHUNT_VOLTAGE_UV_t *out
);

/**
 * @brief  Read payload field current_uA.
 */
halif_status_t INA219_ReadCurrentUa(
    halif_handle_t                h_i2c,
    uint8_t                       addr7bit,
    INA219_CURRENT_UA_t *out
);

/**
 * @brief  Read payload field power_mW.
 */
halif_status_t INA219_ReadPowerMw(
    halif_handle_t                h_i2c,
    uint8_t                       addr7bit,
    INA219_POWER_MW_t *out
);

#ifdef __cplusplus
}
#endif