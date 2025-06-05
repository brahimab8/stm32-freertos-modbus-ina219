/* Manually edited ina219.c */
#include "drivers/ina219.h"
#include <stdint.h>

halif_status_t INA219_SetGain(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    INA219_GAIN_t  value
) {
    uint8_t buf[2] = { 0x00, (uint8_t)value };
    return halif_i2c_write(h_i2c, addr7bit, buf, 2, 100);
}

halif_status_t INA219_SetBusRange(
    halif_handle_t    h_i2c,
    uint8_t           addr7bit,
    INA219_BUS_RANGE_t value
) {
    uint8_t buf[2] = { 0x00, (uint8_t)value };
    return halif_i2c_write(h_i2c, addr7bit, buf, 2, 100);
}

halif_status_t INA219_SetCalibration(
    halif_handle_t       h_i2c,
    uint8_t              addr7bit,
    INA219_CALIBRATION_t value
) {
    uint8_t buf[3] = {
        0x05,
        (uint8_t)(value >> 8),
        (uint8_t)(value & 0xFF)
    };
    return halif_i2c_write(h_i2c, addr7bit, buf, 3, 100);
}

halif_status_t INA219_SetPeriod(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    INA219_PERIOD_t  value
) {
    (void)h_i2c;
    (void)addr7bit;
    (void)value;
    return HALIF_OK;  // Period is handled internally
}

halif_status_t INA219_ReadGain(
    halif_handle_t h_i2c,
    uint8_t        addr7bit,
    uint8_t       *out
) {
    uint8_t cmd  = 0x00;
    uint8_t data = 0;
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, &data, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    *out = data;
    return HALIF_OK;
}

halif_status_t INA219_ReadBusRange(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    uint8_t         *out
) {
    uint8_t cmd  = 0x00;
    uint8_t data = 0;
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, &data, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    *out = data;
    return HALIF_OK;
}

halif_status_t INA219_ReadCalibration(
    halif_handle_t       h_i2c,
    uint8_t              addr7bit,
    uint16_t            *out
) {
    uint8_t cmd  = 0x05;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data, 2, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint16_t raw = ((uint16_t)data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw;
    return HALIF_OK;
}

halif_status_t INA219_ReadBusVoltageMv(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    uint16_t         *out
) {
    uint8_t cmd  = REG_BUS_VOLTAGE_MV;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data, 2, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint16_t raw = ((uint16_t)data[0] << 8) | data[1];
    raw = raw >> 3;
    raw = raw & 0x1FFF;
    *out = raw * 4;
    return HALIF_OK;
}

halif_status_t INA219_ReadShuntVoltageUv(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    int16_t          *out
) {
    uint8_t cmd  = REG_SHUNT_VOLTAGE_UV;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data, 2, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint16_t raw = ((uint16_t)data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw * 10;
    return HALIF_OK;
}

halif_status_t INA219_ReadCurrentUa(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    int16_t          *out
) {
    uint8_t cmd  = REG_CURRENT_UA;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data, 2, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint16_t raw = ((uint16_t)data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw * 1;
    return HALIF_OK;
}

halif_status_t INA219_ReadPowerMw(
    halif_handle_t   h_i2c,
    uint8_t          addr7bit,
    uint16_t         *out
) {
    uint8_t cmd  = REG_POWER_MW;
    uint8_t data[2];
    if (halif_i2c_write(h_i2c, addr7bit, &cmd, 1, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    if (halif_i2c_read(h_i2c, addr7bit, data, 2, 100) != HALIF_OK) {
        return HALIF_ERROR;
    }
    uint16_t raw = ((uint16_t)data[0] << 8) | data[1];
    raw = raw & 0xFFFF;
    *out = raw * 20;
    return HALIF_OK;
}
