/* Auto-generated ina219_driver.c; do not edit! */
#include "drivers/ina219_driver.h"
#include "config/ina219_config.h"
#include "config/protocol.h"
#include <string.h>
#include <stdbool.h>

static halif_status_t ini(void *ctx) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
    if (INA219_SetPeriod(c->h_i2c, c->addr7, ina219_defaults.period) != HALIF_OK) return HALIF_ERROR;
    if (INA219_SetGain(c->h_i2c, c->addr7, ina219_defaults.gain) != HALIF_OK) return HALIF_ERROR;
    if (INA219_SetBusRange(c->h_i2c, c->addr7, ina219_defaults.bus_range) != HALIF_OK) return HALIF_ERROR;
    if (INA219_SetCalibration(c->h_i2c, c->addr7, ina219_defaults.calibration) != HALIF_OK) return HALIF_ERROR;
    c->period = ina219_defaults.period;
    c->gain = ina219_defaults.gain;
    c->bus_range = ina219_defaults.bus_range;
    c->calibration = ina219_defaults.calibration;
    c->payload_mask = 0x03;  /* default mask */
    return HALIF_OK;
}

static halif_status_t rd(void *ctx, uint8_t out_buf[], uint8_t *out_len) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
    uint8_t *cursor = out_buf;
    uint8_t mask = c->payload_mask;
    int total_bytes = 0;

    if (mask & BIT_BUS_VOLTAGE_MV) {
        uint16_t var_bus_voltage_mV;
        if (INA219_ReadBusVoltageMv(c->h_i2c, c->addr7, &var_bus_voltage_mV) != HALIF_OK) {
            *out_len = 0;
            return HALIF_ERROR;
        }
        *cursor++ = (uint8_t)(var_bus_voltage_mV >> 8);
        *cursor++ = (uint8_t)(var_bus_voltage_mV & 0xFF);
        total_bytes += 2;
    }

    if (mask & BIT_SHUNT_VOLTAGE_UV) {
        int16_t var_shunt_voltage_uV;
        if (INA219_ReadShuntVoltageUv(c->h_i2c, c->addr7, &var_shunt_voltage_uV) != HALIF_OK) {
            *out_len = 0;
            return HALIF_ERROR;
        }
        *cursor++ = (uint8_t)(var_shunt_voltage_uV >> 8);
        *cursor++ = (uint8_t)(var_shunt_voltage_uV & 0xFF);
        total_bytes += 2;
    }

    if (mask & BIT_CURRENT_UA) {
        int16_t var_current_uA;
        if (INA219_ReadCurrentUa(c->h_i2c, c->addr7, &var_current_uA) != HALIF_OK) {
            *out_len = 0;
            return HALIF_ERROR;
        }
        *cursor++ = (uint8_t)(var_current_uA >> 8);
        *cursor++ = (uint8_t)(var_current_uA & 0xFF);
        total_bytes += 2;
    }

    if (mask & BIT_POWER_MW) {
        uint16_t var_power_mW;
        if (INA219_ReadPowerMw(c->h_i2c, c->addr7, &var_power_mW) != HALIF_OK) {
            *out_len = 0;
            return HALIF_ERROR;
        }
        *cursor++ = (uint8_t)(var_power_mW >> 8);
        *cursor++ = (uint8_t)(var_power_mW & 0xFF);
        total_bytes += 2;
    }

    *out_len = total_bytes;
    return HALIF_OK;
}

bool ina219_read_config(void *vctx, uint8_t field, uint8_t *out) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    switch (field) {
      case CMD_GET_PERIOD:
        *out = (uint8_t)c->period;
        return true;

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

static const uint8_t ina219_config_fields[] = {
    CMD_GET_PERIOD,
    CMD_GET_GAIN,
    CMD_GET_RANGE,
    CMD_GET_CAL,
};

const uint8_t *ina219_get_config_fields(size_t *count) {
    if (count) *count = sizeof(ina219_config_fields) / sizeof(ina219_config_fields[0]);
    return ina219_config_fields;
}

static uint8_t get_sample_size(void *ctx) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
    uint8_t size = 0;
    if (c->payload_mask & (1 << 0)) size += 2;
    if (c->payload_mask & (1 << 1)) size += 2;
    if (c->payload_mask & (1 << 2)) size += 2;
    if (c->payload_mask & (1 << 3)) size += 2;
    return size;
}

static const SensorDriver_t ina219_driver = {
    .init        = (HAL_StatusTypeDef (*)(void *)) ini,
    .read        = (HAL_StatusTypeDef (*)(void *, uint8_t *, uint8_t *)) rd,
    .sample_size = get_sample_size,
    .read_config = ina219_read_config,
};

const SensorDriver_t *INA219_GetDriver(void) {
    return &ina219_driver;
}

static uint32_t ina219_default_period_ms(void) {
    return 5 * 100;
}

static const SensorDriverInfo_t ina219_info = {
    .type_code            = SENSOR_TYPE_INA219,
    .ctx_size             = sizeof(INA219_Ctx_t),
    .init_ctx             = ina219_init_ctx,
    .get_driver           = INA219_GetDriver,
    .configure            = ina219_configure,
    .read_config          = ina219_read_config,
    .get_config_fields    = ina219_get_config_fields,
    .get_default_period_ms = ina219_default_period_ms,  // 5 * 100ms
};

void ina219_RegisterDriver(void) {
    SensorRegistry_Register(&ina219_info);
}

void ina219_init_ctx(void *vctx, halif_handle_t h_i2c, uint8_t addr7) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    c->h_i2c  = h_i2c;
    c->addr7  = addr7;
}

bool ina219_configure(void *vctx, uint8_t field_id, uint8_t param) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    halif_status_t rc;

    switch (field_id) {
      case CMD_SET_PERIOD:
        rc = INA219_SetPeriod(c->h_i2c, c->addr7, (INA219_PERIOD_t)param);
        if (rc == HALIF_OK) {
            c->period = (INA219_PERIOD_t)param;
            return true;
        } else {
            return false;
        }

      case CMD_SET_GAIN:
        rc = INA219_SetGain(c->h_i2c, c->addr7, (INA219_GAIN_t)param);
        if (rc == HALIF_OK) {
            c->gain = (INA219_GAIN_t)param;
            return true;
        } else {
            return false;
        }

      case CMD_SET_RANGE:
        rc = INA219_SetBusRange(c->h_i2c, c->addr7, (INA219_BUS_RANGE_t)param);
        if (rc == HALIF_OK) {
            c->bus_range = (INA219_BUS_RANGE_t)param;
            return true;
        } else {
            return false;
        }

      case CMD_SET_CAL:
        rc = INA219_SetCalibration(c->h_i2c, c->addr7, (INA219_CALIBRATION_t)param);
        if (rc == HALIF_OK) {
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