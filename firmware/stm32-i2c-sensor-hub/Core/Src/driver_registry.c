#include "driver_registry.h"
#include "drivers/ina219.h"
#include "drivers/ina219_driver.h"

// configure callback for INA219
static SM_Status_t ina219_configure(void *vctx, uint8_t cmd_id, uint8_t param) {
  INA219_Ctx_t *c = vctx;
  switch (cmd_id) {
    case CMD_SET_GAIN:
      return (INA219_SetConfig(c->hi2c, c->addr8, (INA219_Gain_t)param, INA219_BVOLTAGERANGE_32V) == HAL_OK)
               ? SM_OK : SM_ERROR;
    case CMD_SET_RANGE:
      return (INA219_SetConfig(c->hi2c, c->addr8, INA219_GAIN_8_320MV, (INA219_BusRange_t)param) == HAL_OK)
               ? SM_OK : SM_ERROR;
    case CMD_SET_CAL:
      return (INA219_SetCalibration(c->hi2c, c->addr8, (uint16_t)param) == HAL_OK)
               ? SM_OK : SM_ERROR;
    default:
      return SM_ERROR;
  }
}

// context initializer
static void ina219_init_ctx(void *vctx, I2C_HandleTypeDef *hi2c, uint8_t addr7) {
  INA219_Ctx_t *c = vctx;
  c->hi2c  = hi2c;
  c->addr8 = addr7 << 1;
}

const SensorDriverInfo_t sensor_driver_registry[] = {
  {
    .type_code  = SENSOR_TYPE_INA219,
    .ctx_size   = sizeof(INA219_Ctx_t),
    .init_ctx   = ina219_init_ctx,
    .get_driver = INA219_GetDriver,
    .configure  = ina219_configure
  },
  DRIVER_REGISTRY_END  // terminator
};
