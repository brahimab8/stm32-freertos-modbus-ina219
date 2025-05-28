## Command & Response Handling (v1.2.0)

Builds on the Sensor Tasks Manager to add a UART-based command/response layer with:

* **Robust framing** (SOF marker + timeout + XOR checksum)
* **Central dispatch** in a dedicated `CommandTask`
* **Packet formatting** via a reusable Response Builder
* **Debug asserts** and error hooks over UART2

*This tutorial matches [v1.2.0 of the code](https://github.com/brahimab8/stm32-i2c-sensor-hub/tree/v1.2.0).*

---

### 1. Response Builder

A small module to format all outgoing packets:

* **Status-only** (no payload)
* **Sample list** (tick + data\[] repeated)

It lives in `utils/response_builder.{h,c}` and exposes:

```c
size_t ResponseBuilder_BuildStatus(uint8_t *buf,
                                   uint8_t addr7,
                                   uint8_t cmd,
                                   uint8_t status);

size_t ResponseBuilder_BuildSamples(uint8_t *buf,
                                    uint8_t addr7,
                                    const SensorSample_t *samples,
                                    uint32_t count,
                                    uint8_t sample_size);
```

**Usage** in `CommandTask`:

```c
// build status
len = ResponseBuilder_BuildStatus(txbuf, cmd.addr7, cmd.cmd, status);
HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);

// build samples
len = ResponseBuilder_BuildSamples(txbuf, cmd.addr7, samples, count, ssize);
HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
```

---

### 2. Command Task

Centralizes all command handling off the ISR:

* **CMD\_READ\_SAMPLES**: lookup task via `SensorManager_GetTask()`, call `SensorTask_ReadSamples()`, then `BuildSamples()`.
* **CMD\_ADD\_SENSOR**, **CMD\_REMOVE\_SENSOR**, **CMD\_SET\_PERIOD**, **CMD\_SET\_GAIN**, **CMD\_SET\_RANGE**, **CMD\_SET\_CAL**: call the matching `SensorManager_*()` routine, then `BuildStatus()`.
* **default**: send `STATUS_UNKNOWN_CMD`.

* Keeps all logic out of the ISR.
* Easily extendable for new commands.

---

### 3. Integration in `main.c`

1. **Enable full-assert** in the .ioc (**Project → Code Generator → “Use full assert”**) and regenerate.
2. In `main()` (USER CODE blocks):

   * Create the command queue & task:

     ```c
     cmdQueue = xQueueCreate(8, sizeof(COMMAND_t));
     osThreadNew(CommandTask, mgr, &cmdTaskAttr);
     ```
   * Kick off UART RX:

     ```c
     HAL_UART_Receive_IT(&huart1, &rx_temp, 1);
     ```
3. **Removed old manual additions** (`initial_addrs[]`) is removed once we wire ADD/RMV-commands. The `CommandTask` now calls `SensorManager_AddByType()` / `SensorManager_Remove()` at runtime.

---

### 4. Error Handling, Asserts & Runtime Debug

* In `main.c`’s `USER CODE` blocks, print over UART2:

  ```c
  void Error_Handler(void) {
    __disable_irq();
  #ifdef DEBUG
    HAL_UART_Transmit(&huart2,(uint8_t*)"!! ERROR_HANDLER\r\n",18,HAL_MAX_DELAY);
  #endif
    while (1) { }
  }

  #ifdef USE_FULL_ASSERT
  void assert_failed(uint8_t *file, uint32_t line) {
  #ifdef DEBUG
    char buf[64];
    int n = snprintf(buf,sizeof(buf),"ASSERT %s:%lu\r\n",file,(unsigned long)line);
    HAL_UART_Transmit(&huart2,(uint8_t*)buf,n,HAL_MAX_DELAY);
  #endif
    while (1) { }
  }
  #endif
  ```

And in the **defaultTask**, we already print per-task stack watermarks and free‐heap once per second under `#ifdef DEBUG`.  Over the ST-LINK’s virtual COM port (e.g. via PuTTY), you’ll see something like:

```
[Sensor 0] stack left: 200 bytes
[Sensor 1] stack left: 200 bytes
[CmdTask] stack left: 176 bytes
[Sys] Free heap: 4192 bytes
```

---

### 5. Client Usage (CLI Tester)

Run the CLI wrapper to exercise the full get­-sensor-readings flow over UART:

```bash
python scripts/get_sensor_readings.py COM3 1 0x40 read
python scripts/get_sensor_readings.py COM3 1 0x40 add ina219
python scripts/get_sensor_readings.py COM3 1 0x40 period 500
python scripts/get_sensor_readings.py COM3 1 0x40 gain 2
```

Under the hood it calls your framed `send_command(...)`, then `recv_packet(...)` and `parse_samples(...)` to print each tick+payload.

### Next Steps

* **Dynamic sensor list**: your `CommandTask` now implements ADD & RMV—remove the old static array in `main.c`.
* **Full command coverage**: test all `CMD_*` cases end-to-end, confirm gain/range/cal actually change the INA219 readings.
* **Extend to new sensors**: drop additional `*.json` metadata & driver code and the CLI will pick them up automatically.
