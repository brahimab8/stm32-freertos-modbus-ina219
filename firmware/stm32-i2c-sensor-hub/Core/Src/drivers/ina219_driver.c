#include "drivers/ina219_driver.h"
#include "config/ina219_config.h"
#include <string.h>

static HAL_StatusTypeDef ini(void *ctx)
{
  INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
  // apply generated defaults:
  HAL_StatusTypeDef rc = INA219_SetConfig(
      c->hi2c,
      c->addr8,
      ina219_defaults.gain,
      ina219_defaults.bus_range
  );
  if (rc != HAL_OK) return rc;

  // optional: set the calibration
  return INA219_SetCalibration(
      c->hi2c,
      c->addr8,
      ina219_defaults.calibration
  );
}

static HAL_StatusTypeDef rd(void *ctx,
                            uint8_t out_buf[SENSOR_MAX_PAYLOAD],
                            uint8_t *out_len)
{
  INA219_Ctx_t *c = (INA219_Ctx_t *)ctx;
  uint16_t mv;
  int32_t  ua;

  // read bus voltage
  if (INA219_ReadBusVoltage_mV(c->hi2c, c->addr8, &mv) != HAL_OK ||
      INA219_ReadCurrent_uA     (c->hi2c, c->addr8, &ua) != HAL_OK)
  {
    *out_len = 0;
    return HAL_ERROR;
  }

  // pack big-endian: 2B mV, then 4B current
  out_buf[0] = (mv >> 8) & 0xFF;
  out_buf[1] = (mv      ) & 0xFF;
  out_buf[2] = (ua >> 24) & 0xFF;
  out_buf[3] = (ua >> 16) & 0xFF;
  out_buf[4] = (ua >> 8 ) & 0xFF;
  out_buf[5] = (ua      ) & 0xFF;
  *out_len   = 6;
  return HAL_OK;
}

static const SensorDriver_t ina219_driver = {
  .init = ini,
  .read = rd,
  .sample_size = SENSOR_PAYLOAD_SIZE_INA219      // 2B voltage + 4B current
};

const SensorDriver_t *INA219_GetDriver(void)
{
  return &ina219_driver;
}
