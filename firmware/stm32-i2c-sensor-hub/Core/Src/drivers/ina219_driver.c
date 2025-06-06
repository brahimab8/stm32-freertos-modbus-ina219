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
    if (INA219_SetShuntMilliohm(c->h_i2c, c->addr7, ina219_defaults.shunt_milliohm) != HALIF_OK) return HALIF_ERROR;
    if (INA219_SetCurrentLsbUa(c->h_i2c, c->addr7, ina219_defaults.current_lsb_uA) != HALIF_OK) return HALIF_ERROR;
    c->period = ina219_defaults.period;
    c->gain = ina219_defaults.gain;
    c->bus_range = ina219_defaults.bus_range;
    c->shunt_milliohm = ina219_defaults.shunt_milliohm;
    c->current_lsb_uA = ina219_defaults.current_lsb_uA;
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

bool ina219_read_config_bytes(void *vctx, uint8_t field, uint8_t *out_buf, size_t *out_len) {
    INA219_Ctx_t *c = (INA219_Ctx_t *)vctx;
    switch (field) {
      case CMD_GET_PERIOD:
        out_buf[0] = (uint8_t)c->period;
        *out_len = 1;
        return true;

      case CMD_GET_GAIN:
        out_buf[0] = (uint8_t)c->gain;
        *out_len = 1;
        return true;

      case CMD_GET_RANGE:
        out_buf[0] = (uint8_t)c->bus_range;
        *out_len = 1;
        return true;

      case CMD_GET_SHUNT:
        out_buf[0] = (uint8_t)c->shunt_milliohm;
        *out_len = 1;
        return true;

      case CMD_GET_CURRENT_LSB:
        out_buf[0] = (uint8_t)c->current_lsb_uA;
        *out_len = 1;
        return true;

      case CMD_GET_CAL:
        // return 2 bytes (big-endian) for field `calibration`
        {
            out_buf[0] = (uint8_t)((c->calibration >> 8) & 0xFF);
            out_buf[1] = (uint8_t)((c->calibration >> 0) & 0xFF);
            *out_len = 2;
            return true;
        }

      case CMD_GET_PAYLOAD_MASK:
        out_buf[0] = c->payload_mask;
        *out_len = 1;
        return true;

      default:
        return false;
    }
}

static const uint8_t ina219_config_fields[] = {
    CMD_GET_PERIOD,
    CMD_GET_GAIN,
    CMD_GET_RANGE,
    CMD_GET_SHUNT,
    CMD_GET_CURRENT_LSB,
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
    .read_config_bytes = ina219_read_config_bytes,
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
    .read_config_bytes    = ina219_read_config_bytes,
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

      case CMD_SET_SHUNT:
        rc = INA219_SetShuntMilliohm(c->h_i2c, c->addr7, (INA219_SHUNT_MILLIOHM_t)param);
        if (rc == HALIF_OK) {
            c->shunt_milliohm = (INA219_SHUNT_MILLIOHM_t)param;

            // Recompute `calibration` because `shunt_milliohm` changed
            c->calibration = ((uint16_t)(0.04096f / (((float)c->current_lsb_uA / 1e6f) * ((float)c->shunt_milliohm / 1000.0f)) + 0.5f));
            INA219_SetCalibration(c->h_i2c, c->addr7, c->calibration);

            return true;
        } else {
            return false;
        }

      case CMD_SET_CURRENT_LSB:
        rc = INA219_SetCurrentLsbUa(c->h_i2c, c->addr7, (INA219_CURRENT_LSB_UA_t)param);
        if (rc == HALIF_OK) {
            c->current_lsb_uA = (INA219_CURRENT_LSB_UA_t)param;

            // Recompute `calibration` because `current_lsb_uA` changed
            c->calibration = ((uint16_t)(0.04096f / (((float)c->current_lsb_uA / 1e6f) * ((float)c->shunt_milliohm / 1000.0f)) + 0.5f));
            INA219_SetCalibration(c->h_i2c, c->addr7, c->calibration);

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
