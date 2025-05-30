# Add / Integrate a new sensor
*Step-by-step instructions to integrate a new sensor to the stm32-i2c-sensor-hub system.*
---

## 1. Write the metadata JSON

**File:** `metadata/sensors/<sensor>.json`
**Example:** `metadata/sensors/bmp280.json`

```json
{
  "name": "bmp280",
  "config_defaults": {
    "mode":        "BMP280_MODE_NORMAL",
    "oversample":  "BMP280_OS_4X",
    "filter":      "BMP280_FILTER_OFF"
  },
  "payload_fields": [
    { "name": "pressure_Pa",   "type": "uint32", "size": 4 },
    { "name": "temperature_C", "type": "int16",  "size": 2 }
  ]
}
```

* **`name`** → used to name `bmp280_config.h/.c` and driver files.
* **`config_defaults`** → fields in the generated `<name>_config.h/.c`.
* **`payload_fields`** → drives packing order and sample size.

---

## 2. Assign a new sensor code

Edit **`metadata/protocol.json`** under `"sensors"`:

```diff
  "sensors": {
-   "INA219": 1
+   "INA219": 1,
+   "BMP280": 2
  }
```

Now `protocol.h`’s `SENSOR_TYPE_BMP280` will be generated.

---

## 3. Regenerate the headers

```bash
python scripts/generate_headers.py \
  --meta metadata \
  --out firmware/stm32-i2c-sensor-hub/Core
```

This will create:

* `Core/Inc/config/bmp280_config.h`
* `Core/Src/config/bmp280_config.c`
* updated `Core/Inc/config/protocol.h` with your new `SENSOR_TYPE_BMP280` and any new commands.

---

## 4. Implement the low-level HAL driver

Create **`Drivers/bmp280.h`** & **`.c`** mirroring the INA219 HAL wrapper:

* `bmp280.h` declares functions like:

  ```c
  HAL_StatusTypeDef BMP280_Init(I2C_HandleTypeDef *hi2c, uint8_t addr8);
  HAL_StatusTypeDef BMP280_ReadPressure(I2C_HandleTypeDef*, uint8_t, uint32_t*);
  HAL_StatusTypeDef BMP280_ReadTemperature(I2C_HandleTypeDef*, uint8_t, int16_t*);
  ```
* `bmp280.c` implements those over I²C.

---

## 5. Implement the SensorDriver adapter

Create **`Drivers/bmp280_driver.h`** & **`.c`**:

* **Header** (`bmp280_driver.h`):

  ```c
  #ifndef BMP280_DRIVER_H
  #define BMP280_DRIVER_H
  #include "task/sensor_task.h"
  const SensorDriver_t *BMP280_GetDriver(void);
  #endif
  ```
* **Source** (`bmp280_driver.c`):

  ```c
  #include "bmp280_driver.h"
  #include "config/bmp280_config.h"
  #include "drivers/bmp280.h"

  static HAL_StatusTypeDef init_fn(void *ctx) {
    BMP280_Ctx_t *c = ctx;
    // apply defaults from bmp280_config
    return BMP280_Init(c->hi2c, c->addr8);
  }

  static HAL_StatusTypeDef read_fn(void *ctx, uint8_t *buf, uint8_t *len) {
    BMP280_Ctx_t *c = ctx;
    uint32_t p; int16_t t;
    if (BMP280_ReadPressure(c->hi2c, c->addr8, &p) != HAL_OK
     || BMP280_ReadTemperature(c->hi2c, c->addr8, &t) != HAL_OK) {
      *len = 0; return HAL_ERROR;
    }
    // pack big-endian: 4B pressure + 2B temp
    buf[0]=p>>24; buf[1]=p>>16; buf[2]=p>>8; buf[3]=p;
    buf[4]=t>>8;  buf[5]=t;
    *len = 6;
    return HAL_OK;
  }

  static const SensorDriver_t bmp280_driver = {
    .init        = init_fn,
    .read        = read_fn,
    .sample_size = 6
  };

  const SensorDriver_t *BMP280_GetDriver(void) {
    return &bmp280_driver;
  }
  ```

And define `BMP280_Ctx_t` in `bmp280_driver.h` with an I²C handle and address.

---

## 6. Register in the driver registry

Edit **`firmware/.../DriverRegistry/driver_registry.c`**:

```c
extern void bmp280_init_ctx(void*, I2C_HandleTypeDef*, uint8_t);
extern const SensorDriver_t *BMP280_GetDriver(void);
extern SM_Status_t bmp280_configure(void*, uint8_t, uint8_t);

static const SensorDriverInfo_t sensor_driver_registry[] = {
  {
    .type_code  = SENSOR_TYPE_BMP280,
    .ctx_size   = sizeof(BMP280_Ctx_t),
    .init_ctx   = bmp280_init_ctx,
    .get_driver= BMP280_GetDriver,
    .configure  = bmp280_configure
  },
  /* … existing entries … */
  DRIVER_REGISTRY_END
};
```

Implement `bmp280_init_ctx()` to populate `ctx->hi2c` and `ctx->addr8`, and optionally `bmp280_configure()` if you want to support gain/period commands.

---

## 7. Build & verify

1. **Rebuild firmware** in STM32CubeIDE or via `make`.
2. **Flash** your device.
3. On your PC:

   ```bash
   sensor-cli add    --board 1 --addr 0x76 --sensor bmp280
   sensor-cli read   --board 1 --addr 0x76
   ```
4. **Watch** the USART2 debug console for stack/heap logs.

---

You’re now fully integrated. All layers—from JSON metadata through framing, HAL, RTOS tasks, up to the Python CLI—will automatically handle your new sensor.

---
[Home](index.md) • [Return (Resource Usage)](ressource-usage.md)
