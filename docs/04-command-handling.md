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

**API** (in `utils/response_builder.h`):

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

* **Queue**: `cmdQueue = xQueueCreate(8, sizeof(COMMAND_t));`
* **Task**: `osThreadNew(CommandTask, mgr, &attrs);`

```c
void CommandTask(void *arg) {
  COMMAND_t cmd;
  while (xQueueReceive(cmdQueue, &cmd, portMAX_DELAY) == pdPASS) {
    switch (cmd.cmd) {
      case CMD_READ_SAMPLES:
        // read via SensorManager_GetTask, call BuildSamples
        break;
      case CMD_ADD_SENSOR:
      case CMD_REMOVE_SENSOR:
      case CMD_SET_PERIOD:
      case CMD_SET_GAIN:
      case CMD_SET_RANGE:
      case CMD_SET_CAL:
        // call SensorManager_* routines and send status
        break;
      default:
        // send STATUS_UNKNOWN_CMD
        break;
    }
  }
}
```

* Keeps all business logic out of the ISR.
* Easily extendable for new commands.

---

### 3. Integration in `main.c`

1. **Kick off RX** in `USER CODE BEGIN 2` (after queue & task are ready):

   ```c
   HAL_UART_Receive_IT(&huart1, &rx_temp, 1);
   ```
2. **Create queue & task**:

   ```c
   cmdQueue = xQueueCreate(8, sizeof(COMMAND_t));
   osThreadNew(CommandTask, mgr, &cmdTaskAttr);
   ```
3. **Initial sensors** remain static for now:

   ```c
   for (int i = 0; i < NUM_INITIAL_SENSORS; ++i)
     SensorManager_AddByType(mgr, SENSOR_TYPE_INA219, initial_addrs[i], SENSOR_DEFAULT_POLL_PERIOD);
   ```
4. **ISR** enqueues into `cmdQueue`; `CommandTask` dequeues and calls the Response Builder.

---

### 4. Error Handling & Asserts

* **Enable full-assert** in `.ioc` → **Code Generator** → **Use full assert** → regenerate.

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

* Use `assert_param()` in application code to catch bad inputs at runtime.

---

### 5. Client Usage

Run the CLI wrapper to exercise the full get­-sensor-readings flow over UART:

```bash
python tools/sensor_master.py COM3 1 0x40 ina219
```

Under the hood it calls your framed `send_command(...)`, then `recv_packet(...)` and `parse_samples(...)` to print each tick+payload.

### Next Steps

* **Dynamic sensor list**: Replace the static `initial_addrs[]` with runtime `ADD`/`REMOVE` support in `CommandTask`.
* **Full command coverage**: Implement and test all `CMD_*` cases end-to-end.
