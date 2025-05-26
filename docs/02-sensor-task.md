# 02 – SensorTask Tutorial

*Polling of one or more I²C sensors via FreeRTOS with raw data exposure over UART, employing an auto-generated framing protocol.*<br>
*This tutorial matches [v1.0.0 of the code](https://github.com/brahimab8/stm32-i2c-sensor-hub/tree/v1.0.0).*

---

## Prerequisites

* The project from **01 – Setup** (FreeRTOS + UART echo on USART1/PA8) must be compilable.
* Directory layout:

  ```
  scripts/
    generate_headers.py     # JSON → .h/.c code generator
  metadata/
    protocol.json
    sensors/
      ina219.json
  Core/
    Inc/
      config/
        protocol.h
        ina219_config.h
      drivers/
        ina219.h
        ina219_driver.h
      task/
        sensor_task.h
      other headers       # STM32Cube HAL & FreeRTOS headers
    Src/
      config/
        ina219_config.c
      drivers/
        ina219.c
        ina219_driver.c
      task/
        sensor_task.c
      main.c
     other sources       # STM32Cube HAL & FreeRTOS sources
  ```

---

## 1. Auto‐Generation of Protocol & Sensor Defaults

Auto‐Generation of Protocol & Sensor Defaults

A script (**`scripts/generate_headers.py`**) transforms JSON metadata into the following layout under the `Core` folder:

* Headers (`.h`) are written into **`Core/Inc/config`**
* Source files (`.c`) are written into **`Core/Src/config`**

Specifically:

* **`Core/Inc/config/protocol.h`** – SOF marker, command codes, `RESPONSE_t`/`COMMAND_t` structures and constant macros.
* **`Core/Inc/config/ina219_config.h`** – Default configuration struct `ina219_config_defaults_t`, macro `SENSOR_PAYLOAD_SIZE_INA219`, and extern declaration `ina219_defaults`.
* **`Core/Src/config/ina219_config.c`** – Definition of `ina219_defaults` with default values.

A pre-build step is configured in STM32CubeIDE to invoke:

```bash
python "${ProjDirPath}/scripts/generate_headers.py" \
  --meta "${ProjDirPath}/metadata" \
  --out  "${ProjDirPath}/Core"
```

---

## 2. SensorTask API Overview

A FreeRTOS task is created to perform periodic sensor reads under a shared I²C mutex and buffer the results in a FIFO queue.

### Creation

```c
SensorTaskHandle_t *SensorTask_Create(
  const SensorDriver_t *driver,
  void                 *context,
  uint32_t              period_ms,
  osMutexId_t           i2c_mutex,
  uint32_t              queue_depth
);
```

* `driver->init(context)` is called once to apply sensor configuration.
* Every `period_ms` ms, `driver->read(context, buf, &len)` executes under `i2c_mutex` protection.
* Samples (timestamp + payload) are enqueued; overflow drops the oldest sample.

### Data Retrieval

```c
HAL_StatusTypeDef SensorTask_ReadSamples(
  SensorTaskHandle_t *handle,
  SensorSample_t      output[],
  uint32_t            max_samples,
  uint32_t           *retrieved
);
```

* Up to `max_samples` entries are dequeued in FIFO order into `output[]`.
* `retrieved` returns the actual count.
* Additional functions:

  * `SensorTask_Flush(handle)` to clear the queue.
  * `SensorTask_GetQueueDepth(handle)` and `SensorTask_GetSampleSize(handle)` for metadata.

---

## 3. INA219 Driver & Configuration

### Low-Level HAL Wrapper (`drivers/ina219.h` / `.c`)

* Enumerations for gain and bus voltage range.
* Functions for register-level operations:

  ```c
  INA219_SetConfig(...);
  INA219_SetCalibration(...);
  INA219_ReadBusVoltage_mV(...);
  INA219_ReadShuntVoltage_uV(...);
  INA219_ReadCurrent_uA(...);
  ```

### SensorDriver Adapter (`drivers/ina219_driver.h` / `.c`)

A `SensorDriver_t` v-table is provided via `INA219_GetDriver()`, adapting the HAL wrapper to the SensorTask framework:

```c
static const SensorDriver_t ina219_driver = {
  .init        = init_fn,
  .read        = read_fn,
  .sample_size = SENSOR_PAYLOAD_SIZE_INA219
};
const SensorDriver_t *INA219_GetDriver(void) { return &ina219_driver; }
```

* `init_fn` applies defaults from `Core/Src/config/ina219_config.c`.
* `read_fn` packs 2 B voltage + 4 B current in big-endian format.

---

## 4. Integration into `main.c`

1. **Header Inclusions**

  ```c
  #include "config/config.h"
  #include "config/protocol.h"
  #include "task/sensor_task.h"
  #include "drivers/ina219_driver.h"
   ```

2. **Mutex Initialization** (after `osKernelInitialize()`):

   ```c
   osMutexId_t busMutex = osMutexNew(NULL);
   ```

3. **Task Creation** for multiple INA219 devices:

   ```c
   INA219_Ctx_t ctx1 = { .hi2c = &hi2c1, .addr8 = 0x40 << 1 };
   SensorTaskHandle_t *h1 = SensorTask_Create(
     INA219_GetDriver(), &ctx1,
     500,      // ms polling interval
     busMutex,
     10        // sample queue depth
   );
   ```

4. **UART Callback** (`HAL_UART_RxCpltCallback`) selects which task’s data is sent:

   ```c
   send_all_samples(&huart1, BOARD_ID, addr7, handle);
   HAL_UART_Receive_IT(&huart1, &rx_temp, 1);
   ```

5. **Frame Construction** in `send_all_samples()`:

   * Header struct `RESPONSE_t` copied into packet buffer.
   * Consecutive samples appended.
   * XOR checksum calculated over bytes \[1 .. header+payload−1].
   * Packet transmitted via `HAL_UART_Transmit_IT()`.

---

## 5. Debugging

- **On-target debug**  
  - In `send_all_samples()`, the code already prints a hex dump of each packet over `huart2`. This can be used to inspect raw frames in real time.
---

## 6. Master-Side Setup

1. **Create & activate venv**
    ```bash
    python -m venv .venv
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    # macOS/Linux
    source .venv/bin/activate
    ```

2. **Install requirements (pyserial)**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the script**:

    ```bash
    python scripts/get_sensor_readings.py COM3 1
    ```

   Example output:

    ```
    Requesting sensor #1 (ina219): tick=4B + payload=6B...
    Sample 0: tick=2242501 ms, voltage=2980 mV, current=81 µA
    Sample 1: tick=2243001 ms, voltage=2976 mV, current=83 µA
    Sample 2: tick=2243501 ms, voltage=2980 mV, current=83 µA
    Sample 3: tick=2244001 ms, voltage=2984 mV, current=84 µA
    Sample 4: tick=2244501 ms, voltage=2980 mV, current=84 µA
    Sample 5: tick=2245001 ms, voltage=2980 mV, current=81 µA
    Sample 6: tick=2245501 ms, voltage=2980 mV, current=84 µA
    Sample 7: tick=2246001 ms, voltage=2980 mV, current=80 µA
    Sample 8: tick=2246501 ms, voltage=2984 mV, current=83 µA
    Sample 9: tick=2247001 ms, voltage=2980 mV, current=81 µA
    ```

## 7. Adding New Sensors

1. Place a new `metadata/sensors/<name>.json` alongside existing files.
2. Re-run the `generate_headers.py` pre-build step.
3. Implement `<name>_driver.c` and `.h` following the v-table pattern.
4. Implement `<name>.c` and `.h` following the pattern.
5. Instantiate another `SensorTask_Create(...)` in `main.c`.

---

## 8. Next Steps

- **Manager Layer**  
  Build a `SensorManager` to own the I²C mutex, track SensorTask handles, and expose an API for add/remove/configure/get-data.

- **Command Handling**  
  In `HAL_UART_RxCpltCallback`, parse incoming frames (ADD_SENSOR, REMOVE_SENSOR, SET_* commands) and invoke the Manager’s functions.

- **Protocol Commands**  
  Flesh out the master-to-node commands (beyond READ) and test each end-to-end with the Python script.
