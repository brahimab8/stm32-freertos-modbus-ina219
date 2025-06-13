/* Auto-generated ina219.c */
#include "drivers/ina219.h"
#include <hal_if.h>

#ifdef __cplusplus
extern "C" {
#endif


/* Helper: assemble big-endian unsigned integer */
static uint64_t be_assemble(const uint8_t *data, int bytes) {
    uint64_t acc = 0;
    for (int i = 0; i < bytes; ++i) {
        acc = (acc << 8) | data[i];
    }
    return acc;
}

/* Helper: write big-endian 'value' into buf[0..bytes-1] */
static void write_be(uint8_t *buf, uint64_t value, int bytes) {
    for (int i = 0; i < bytes; ++i) {
        int shift = 8 * (bytes - 1 - i);
        buf[i] = (uint8_t)((value >> shift) & 0xFF);
    }
}

/* Config-field Set/Read functions */

/**
 * @brief  Set the period field.
 */
halif_status_t INA219_SetPeriod(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_PERIOD_t value
) {
    if ((int64_t)value < (int64_t)1 || (int64_t)value > (int64_t)255) {
        return HALIF_ERROR;
    }
    // Not register-backed; nothing to write on chip
    (void)h_i2c; (void)addr7bit; (void)value;
    return HALIF_OK;}


/**
 * @brief  Set the gain field.
 */
halif_status_t INA219_SetGain(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_GAIN_t value
) {
    if ((int)value < 0 || (int)value > 3) {
        return HALIF_ERROR;
    }
    // Read current register
    uint8_t cmd = 0x00;
    uint8_t data_buf[1];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data_buf, sizeof(data_buf), 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint64_t reg = be_assemble(data_buf, 1);
    // Clear bits for this field
    reg &= ~(0x1800);
    // Insert new value shifted
    reg |= ((uint64_t)value << 11) & 0x1800;
    // Prepare write buffer: [reg_addr, big-endian bytes of reg]
    uint8_t write_buf[2];
    write_buf[0] = 0x00;
    write_be(&write_buf[1], reg, 1);
    return halif_i2c_write(h_i2c, addr7bit, write_buf, sizeof(write_buf), 100);}

/**
 * @brief  Read back the gain field.
 */
halif_status_t INA219_ReadGain(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_GAIN_t *out
) {
    uint8_t cmd = 0x00;
    uint8_t data_buf[1];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data_buf, sizeof(data_buf), 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint64_t reg = be_assemble(data_buf, 1);
    uint64_t val = (reg & 0x1800) >> 11;
    *out = (INA219_GAIN_t)val;
    return HALIF_OK;
}

/**
 * @brief  Set the bus_range field.
 */
halif_status_t INA219_SetBusRange(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_BUS_RANGE_t value
) {
    if ((int64_t)value < (int64_t)0 || (int64_t)value > (int64_t)1) {
        return HALIF_ERROR;
    }
    // Read current register
    uint8_t cmd = 0x00;
    uint8_t data_buf[1];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data_buf, sizeof(data_buf), 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint64_t reg = be_assemble(data_buf, 1);
    // Clear bits for this field
    reg &= ~(0x2000);
    // Insert new value shifted
    reg |= ((uint64_t)value << 13) & 0x2000;
    // Prepare write buffer: [reg_addr, big-endian bytes of reg]
    uint8_t write_buf[2];
    write_buf[0] = 0x00;
    write_be(&write_buf[1], reg, 1);
    return halif_i2c_write(h_i2c, addr7bit, write_buf, sizeof(write_buf), 100);}

/**
 * @brief  Read back the bus_range field.
 */
halif_status_t INA219_ReadBusRange(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_BUS_RANGE_t *out
) {
    uint8_t cmd = 0x00;
    uint8_t data_buf[1];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data_buf, sizeof(data_buf), 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint64_t reg = be_assemble(data_buf, 1);
    uint64_t val = (reg & 0x2000) >> 13;
    *out = (INA219_BUS_RANGE_t)val;
    return HALIF_OK;
}

/**
 * @brief  Set the shunt_milliohm field.
 */
halif_status_t INA219_SetShuntMilliohm(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_SHUNT_MILLIOHM_t value
) {
    if ((int64_t)value < (int64_t)1 || (int64_t)value > (int64_t)255) {
        return HALIF_ERROR;
    }
    // Not register-backed; nothing to write on chip
    (void)h_i2c; (void)addr7bit; (void)value;
    return HALIF_OK;}


/**
 * @brief  Set the current_lsb_uA field.
 */
halif_status_t INA219_SetCurrentLsbUa(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_CURRENT_LSB_UA_t value
) {
    if ((int64_t)value < (int64_t)1 || (int64_t)value > (int64_t)255) {
        return HALIF_ERROR;
    }
    // Not register-backed; nothing to write on chip
    (void)h_i2c; (void)addr7bit; (void)value;
    return HALIF_OK;}


/**
 * @brief  Set the calibration field.
 */
halif_status_t INA219_SetCalibration(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_CALIBRATION_t value
) {
    if ((int64_t)value < (int64_t)1 || (int64_t)value > (int64_t)65535) {
        return HALIF_ERROR;
    }
    // Read current register
    uint8_t cmd = 0x05;
    uint8_t data_buf[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data_buf, sizeof(data_buf), 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint64_t reg = be_assemble(data_buf, 2);
    // Clear bits for this field
    reg &= ~(0xFFFF);
    // Insert new value shifted
    reg |= ((uint64_t)value << 0) & 0xFFFF;
    // Prepare write buffer: [reg_addr, big-endian bytes of reg]
    uint8_t write_buf[3];
    write_buf[0] = 0x05;
    write_be(&write_buf[1], reg, 2);
    return halif_i2c_write(h_i2c, addr7bit, write_buf, sizeof(write_buf), 100);}

/**
 * @brief  Read back the calibration field.
 */
halif_status_t INA219_ReadCalibration(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_CALIBRATION_t *out
) {
    uint8_t cmd = 0x05;
    uint8_t data_buf[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data_buf, sizeof(data_buf), 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint64_t reg = be_assemble(data_buf, 2);
    uint64_t val = (reg & 0xFFFF) >> 0;
    *out = (INA219_CALIBRATION_t)val;
    return HALIF_OK;
}

/* Payload-field Read functions */

halif_status_t INA219_ReadBusVoltageMv(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_BUS_VOLTAGE_MV_t *out
) {
    uint8_t cmd  = REG_BUS_VOLTAGE_MV;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) return HALIF_ERROR;
    if (halif_i2c_read(h_i2c, addr7bit, data, sizeof(data), 100) != HALIF_OK) return HALIF_ERROR;

    uint64_t uval = be_assemble(data, 2);
    uval >>= 3;
    uval &= 0x1FFF;
    *out = (INA219_BUS_VOLTAGE_MV_t)(uval * 4);
    return HALIF_OK;
}

halif_status_t INA219_ReadShuntVoltageUv(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_SHUNT_VOLTAGE_UV_t *out
) {
    uint8_t cmd  = REG_SHUNT_VOLTAGE_UV;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) return HALIF_ERROR;
    if (halif_i2c_read(h_i2c, addr7bit, data, sizeof(data), 100) != HALIF_OK) return HALIF_ERROR;

    uint64_t uval = be_assemble(data, 2);
    uval &= 0xFFFF;
    *out = (INA219_SHUNT_VOLTAGE_UV_t)(uval * 10);
    return HALIF_OK;
}

halif_status_t INA219_ReadCurrentUa(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_CURRENT_UA_t *out
) {
    uint8_t cmd  = REG_CURRENT_UA;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) return HALIF_ERROR;
    if (halif_i2c_read(h_i2c, addr7bit, data, sizeof(data), 100) != HALIF_OK) return HALIF_ERROR;

    uint64_t uval = be_assemble(data, 2);
    uval &= 0xFFFF;
    *out = (INA219_CURRENT_UA_t)(uval * 1);
    return HALIF_OK;
}

halif_status_t INA219_ReadPowerMw(
    halif_handle_t            h_i2c,
    uint8_t                   addr7bit,
    INA219_POWER_MW_t *out
) {
    uint8_t cmd  = REG_POWER_MW;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) return HALIF_ERROR;
    if (halif_i2c_read(h_i2c, addr7bit, data, sizeof(data), 100) != HALIF_OK) return HALIF_ERROR;

    uint64_t uval = be_assemble(data, 2);
    uval &= 0xFFFF;
    *out = (INA219_POWER_MW_t)(uval * 20);
    return HALIF_OK;
}

#ifdef __cplusplus
}
#endif