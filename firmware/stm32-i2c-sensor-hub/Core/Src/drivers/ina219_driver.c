/* Auto-generated ina219_driver.c; do not edit! */
#include "drivers/ina219_driver.h"
#include "config/ina219_config.h"
#include "config/protocol.h"
#include <string.h>
#include <stdbool.h>

static HAL_StatusTypeDef ini(void *ctx) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
    if (INA219_SetGain(c->hi2c, c->addr8, ina219_defaults.gain) != HAL_OK) return HAL_ERROR;
    if (INA219_SetBusRange(c->hi2c, c->addr8, ina219_defaults.bus_range) != HAL_OK) return HAL_ERROR;
    if (INA219_SetCalibration(c->hi2c, c->addr8, ina219_defaults.calibration) != HAL_OK) return HAL_ERROR;
    c->gain = ina219_defaults.gain;
    c->bus_range = ina219_defaults.bus_range;
    c->calibration = ina219_defaults.calibration;
    c->payload_mask = 0x03;  /* default mask */
    return HAL_OK;
}

static HAL_StatusTypeDef rd(void *ctx, uint8_t out_buf[], uint8_t *out_len) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
    uint8_t *cursor = out_buf;
    uint8_t mask = c->payload_mask;
    int total_bytes = 0;

    if (mask & BIT_BUS_VOLTAGE_MV) {
        uint16_t var_bus_voltage_mV;
        if (INA219_ReadBusVoltageMv(c->hi2c, c->addr8, &var_bus_voltage_mV) != HAL_OK) {
            *out_len = 0;
            return HAL_ERROR;
        }
        *cursor++ = (uint8_t)(var_bus_voltage_mV >> 8);
        *cursor++ = (uint8_t)(var_bus_voltage_mV & 0xFF);
        total_bytes += 2;
    }

    if (mask & BIT_SHUNT_VOLTAGE_UV) {
        int16_t var_shunt_voltage_uV;
        if (INA219_ReadShuntVoltageUv(c->hi2c, c->addr8, &var_shunt_voltage_uV) != HAL_OK) {
            *out_len = 0;
            return HAL_ERROR;
        }
        *cursor++ = (uint8_t)(var_shunt_voltage_uV >> 8);
        *cursor++ = (uint8_t)(var_shunt_voltage_uV & 0xFF);
        total_bytes += 2;
    }

    if (mask & BIT_CURRENT_UA) {
        int16_t var_current_uA;
        if (INA219_ReadCurrentUa(c->hi2c, c->addr8, &var_current_uA) != HAL_OK) {
            *out_len = 0;
            return HAL_ERROR;
        }
        *cursor++ = (uint8_t)(var_current_uA >> 8);
        *cursor++ = (uint8_t)(var_current_uA & 0xFF);
        total_bytes += 2;
    }

    if (mask & BIT_POWER_MW) {
        uint16_t var_power_mW;
        if (INA219_ReadPowerMw(c->hi2c, c->addr8, &var_power_mW) != HAL_OK) {
            *out_len = 0;
            return HAL_ERROR;
        }
        *cursor++ = (uint8_t)(var_power_mW >> 8);
        *cursor++ = (uint8_t)(var_power_mW & 0xFF);
        total_bytes += 2;
    }

    *out_len = total_bytes;
    return HAL_OK;
}

bool ina219_read_config(void *vctx, uint8_t field, uint8_t *out) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    switch (field) {
      case CMD_GET_GAIN:
        *out = (uint8_t)c->gain;
        return true;

      case CMD_GET_RANGE:
        *out = (uint8_t)c->bus_range;
        return true;

      case CMD_GET_CAL:
        *out = (uint8_t)(c->calibration & 0xFF);
        return true;

      case CMD_GET_PAYLOAD_MASK:
        *out = c->payload_mask;
        return true;

      default:
        return false;
    }
}

static const SensorDriver_t ina219_driver = {
    .init        = ini,
    .read        = rd,
    .sample_size = SENSOR_PAYLOAD_SIZE_INA219,
    .read_config = ina219_read_config,
};

const SensorDriver_t *INA219_GetDriver(void) {
    return &ina219_driver;
}

static const SensorDriverInfo_t ina219_info = {
    .type_code   = SENSOR_TYPE_INA219,
    .ctx_size    = sizeof(INA219_Ctx_t),
    .init_ctx    = ina219_init_ctx,
    .get_driver  = INA219_GetDriver,
    .configure   = ina219_configure,
    .read_config = ina219_read_config,
};

void ina219_RegisterDriver(void) {
    SensorRegistry_Register(&ina219_info);
}

void ina219_init_ctx(void *vctx, I2C_HandleTypeDef *hi2c, uint8_t addr7) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    c->hi2c  = hi2c;
    c->addr8 = addr7 << 1;
}

bool ina219_configure(void *vctx, uint8_t field_id, uint8_t param) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    HAL_StatusTypeDef rc;

    switch (field_id) {
      case CMD_SET_GAIN:
        rc = INA219_SetGain(c->hi2c, c->addr8, (INA219_GAIN_t)param);
        if (rc == HAL_OK) {
            c->gain = (INA219_GAIN_t)param;
            return true;
        } else {
            return false;
        }

      case CMD_SET_RANGE:
        rc = INA219_SetBusRange(c->hi2c, c->addr8, (INA219_BUS_RANGE_t)param);
        if (rc == HAL_OK) {
            c->bus_range = (INA219_BUS_RANGE_t)param;
            return true;
        } else {
            return false;
        }

      case CMD_SET_CAL:
        rc = INA219_SetCalibration(c->hi2c, c->addr8, (INA219_CALIBRATION_t)param);
        if (rc == HAL_OK) {
            c->calibration = (INA219_CALIBRATION_t)param;
            return true;
        } else {
            return false;
        }

      case CMD_SET_PAYLOAD_MASK:
        c->payload_mask = param;
        return true;

      default:
        return false;
    }
}
