## Sensor Tasks Manager

*Introduce a Sensor Tasks Manager, simplifying the management of multiple sensors, providing better modularity and scalability.*

*This tutorial matches [v1.1.0 of the code](https://github.com/brahimab8/stm32-i2c-sensor-hub/tree/v1.1.0).*

---

### Integration Overview

Previously, each sensor was initialized manually in `main.c`, creating tasks explicitly. This approach became cumbersome as the number of sensors increased.

The new implementation includes:

* `main.c`: Initializes and uses the Sensor Manager.
* `Sensor Manager`: Coordinates sensors via the Driver Registry.
* `Driver Registry`: Provides metadata and functions for each sensor type.
* Individual sensor drivers (e.g., INA219).

---

### Driver Registry

The Driver Registry centralizes definitions of supported sensors, providing essential metadata and functions for each sensor type:

* Sensor type ID (`SENSOR_TYPE_INA219`)
* Context initialization function (`init_ctx`)
* Configuration function (`configure`)
* Driver retrieval function (`get_driver`)

**Example (driver\_registry.c):**

```c
static const SensorDriverInfo_t sensor_driver_registry[] = {
    {
        .type_code = SENSOR_TYPE_INA219,
        .ctx_size  = sizeof(INA219_Ctx_t),
        .init_ctx  = ina219_init_ctx,
        .get_driver= INA219_GetDriver,
        .configure = ina219_configure
    },
    { 0 } // terminator
};
```

**Benefits:**

* Easier integration of new sensor types.
* Unified initialization and configuration logic.

---

### Sensor Manager

The Sensor Manager handles the lifecycle (creation, deletion, and configuration) of sensors using the Driver Registry. It simplifies sensor handling within `main.c`.

**Comparison (manual vs. managed initialization):**

* **Manual (previous approach):**

```c
INA219_Ctx_t *ctx = pvPortMalloc(sizeof(*ctx));
ctx->hi2c = &hi2c1;
ctx->addr8 = (0x40 << 1);

SensorTaskHandle_t *task = SensorTask_Create(
    INA219_GetDriver(), ctx, 1000, busMutex, QUEUE_DEPTH
);
```

* **Using Sensor Manager (new approach):**

```c
SensorManager_AddByType(mgr, SENSOR_TYPE_INA219, 0x40, 1000);
```

The Sensor Manager internally:

* Allocates contexts
* Retrieves appropriate drivers
* Creates and manages sensor tasks automatically

---

### Main Wiring Changes

With the new Sensor Manager implementation, `main.c` is now simplified:

**Initialization:**

```c
busMutex = osMutexNew(NULL);
mgr = SensorManager_Create(busMutex, &hi2c1);

SensorManager_AddByType(mgr, SENSOR_TYPE_INA219, 0x40, SENSOR_DEFAULT_POLL_PERIOD);
SensorManager_AddByType(mgr, SENSOR_TYPE_INA219, 0x41, SENSOR_DEFAULT_POLL_PERIOD);
```

**Reading sensor data example:**

```c
SensorTaskHandle_t *task = SensorManager_GetTask(mgr, addr7);
if (task) {
    send_all_samples(&huart1, BOARD_ID, addr7, task);
}
```

### Memory Usage Notes

The Sensor Manager increases heap usage due to dynamic allocation of sensor contexts, tasks, and queues. To support this, the heap size in `FreeRTOSConfig.h` was raised from **3000** to **8192 bytes**.

> 📌 **Persistent change:**
> Open the `.ioc` in CubeIDE → **Middleware → FREERTOS → FREERTOS** → **Config parameters** tab → find **`configTOTAL_HEAP_SIZE`** (default `3000`) → set to `8192` → **Generate Code**.

* **Baseline (no sensors):** \~7192 bytes free
* **Each INA219 sensor:** \~1050 bytes used

| Sensors | Free Heap    | Notes                                 |
| ------- | ------------ | ------------------------------------- |
| 0       | \~7192 bytes | Baseline system + Sensor Manager only |
| 1       | \~6168 bytes |                                       |
| 2       | \~5088 bytes |                                       |
| 6       | \~768 bytes  | Near limit with 8 KB heap             |
| 8       | –            | overflow                              |

> 💡 You can increase the heap to **10 KB or more** if needed to support additional sensors.

---

### Monitoring Heap Usage via UART

To monitor heap usage during runtime, free heap size is printed every second over **USART2**:

```c
size_t freeHeap = xPortGetFreeHeapSize();
snprintf(buf, sizeof(buf), "Free heap: %u bytes\r\n", (unsigned int)freeHeap);
HAL_UART_Transmit(&huart2, (uint8_t*)buf, strlen(buf), HAL_MAX_DELAY);
```

This helps track memory trends and detect issues early during sensor scaling or tuning.

---

### Recommendations for Optimization

* Reduce individual sensor task stack sizes (`stack_size`).
* Lower the `QUEUE_DEPTH` per sensor.
* Share common resources or contexts across multiple tasks.

---

### Benefits of the New Implementation

* **Scalability**: Quickly add and manage multiple sensors.
* **Maintainability**: Cleaner and more readable `main.c`.
* **Modularity**: Clear separation of sensor management logic.

---

### Next Steps

* **Implement runtime commands (via UART):**
  The system currently defines a command structure (e.g., `CMD_READ_SAMPLES`, `RESPONSE_HEADER_t`), but command handling logic is not yet implemented. This should be developed to allow dynamic configuration, querying, or control of sensor tasks at runtime.

* **Wire and test command processing:**
  Integrate the command parsing layer with `SensorManager` and `SensorTask` logic. Ensure full round-trip functionality (receive command, dispatch, respond) is tested using the defined protocol over `USART1`.

* **Optimize memory usage:**
  Continue profiling heap usage to enable larger sensor networks. Consider reducing task stack sizes, sharing contexts, or batching samples.

* **Expand sensor support:**
  Add new sensor types by extending the `Driver Registry` and creating corresponding driver implementations.
