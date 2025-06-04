## Sensor Configuration & Driver Generation Overview (v1.4.0)

This guide describes a JSON-driven pipeline for configuring I²C sensors, generating HAL wrappers, driver layers, and building a central driver registry. 

*It corresponds to [version 1.4.0 of the repository](https://github.com/brahimab8/stm32-i2c-sensor-hub/tree/v1.4.0).*

---

### 1. Sensor Metadata & JSON Schema

* **Location**: Each sensor’s description lives in `metadata/sensors/<sensor>.json`. All JSON files conform to `metadata/sensor_schema.json`.
* **Key Sections of `<sensor>.json`**:

  1. **`name`**: Canonical sensor name.
  2. **`config_defaults`**: Default values for configurable parameters.
  3. **`config_fields[]`**: Runtime‐configurable fields. Each entry includes:

     * `name`, `getter_cmd`, `setter_cmd` (or `null`), `type`, `size`
     * Optional register details (`reg_addr`, `mask`, `shift`, `endian`)
     * `driver_side` (hardware vs. software)
  4. **`payload_fields[]`**: Measurable outputs (e.g., temperature, voltage). Each entry provides:

     * `name`, `type`, `size`
     * Optional hardware mapping (`reg_addr`, `mask`, `shift`, `endian`)
     * `scale_factor`
  5. **`default_payload_fields[]`**: Subset of `payload_fields` enabled by default.

> **Note**: Some `config_fields` map directly to registers (using mask/shift); others are purely software‐level. `payload_fields` describe the format and filtering of runtime data.

---

### 2. Generator Scripts

Three Python scripts automate C code generation from JSON metadata:

1. **`generate_protocol.py`**

   * Reads `protocol.json`
   * Produces `Core/Inc/config/protocol.h`, defining:

     * All command/status codes
     * Shared data structures for CLI and firmware

2. **`generate_sensor_driver.py`**

   * For each `<sensor>.json`, generates:

     1. **Config Headers/Sources**

        * `Core/Inc/config/<sensor>_config.h/.c`: Default values and macros (e.g., `SENSOR_PAYLOAD_SIZE_<SENSOR>`).
     2. **HAL Abstraction Wrappers**

        * `Core/Inc/drivers/<sensor>.h/.c`: Low‐level I²C register read/write based on JSON.
     3. **Driver Layer**

        * `Core/Inc/drivers/<sensor>_driver.h/.c`: High‐level API exposing:

          * `ini()`, `rd()`, `configure()`, `read_config()`, `sample_size(ctx)`
          * Vtable and `RegisterDriver()` glue.

3. **`generate_firmware_sources.py`**

   * Orchestrates the above two.
   * Generates a central `driver_registry.h/.c` so every sensor driver registers itself automatically—no manual includes required.

**Pre‐build step for CubeIDE**

```bash
cd "${ProjDirPath}"
python3 -m scripts.generate_firmware_sources \
    --meta "${ProjDirPath}/../../metadata" \
    --out  "${ProjDirPath}/Core"
```

---

### 3. Overview of Generated Files

| Path                                 | Purpose                                                                |
| ------------------------------------ | ---------------------------------------------------------------------- |
| `Core/Inc/config/protocol.h`         | Central command/status codes and shared structs                        |
| `Core/Inc/config/<sensor>_config.h`  | Default values + `SENSOR_PAYLOAD_SIZE_<SENSOR>` macros                 |
| `Core/Src/config/<sensor>_config.c`  | Code to initialize defaults from JSON                                  |
| `Core/Inc/drivers/<sensor>.h`        | Prototypes for low‐level HAL I²C read/write                            |
| `Core/Src/drivers/<sensor>.c`        | Implementations of HAL register‐access routines                        |
| `Core/Inc/drivers/<sensor>_driver.h` | Public driver API, context struct (including `payload_mask`)           |
| `Core/Src/drivers/<sensor>_driver.c` | `ini()`, `rd()`, `configure()`, `read_config()`, `sample_size()`, etc. |

---

### 4. Runtime Payload Masking & Sample Size

1. **`payload_mask`**

   * Each driver context (`<sensor>_Ctx_t`) has a `payload_mask` bitfield controlling which `payload_fields[]` are active.
   * CLI commands set/get this mask (`CMD_SET_PAYLOAD_MASK` / `CMD_GET_PAYLOAD_MASK`).
   * `rd()` only packs and returns the enabled fields.

2. **`sample_size(ctx)`**

   * Computes the exact byte count based on the `payload_mask`.
   * `SensorTask_GetSampleSize()` uses this at runtime so DMA/queues allocate exactly the needed size—no over‐reads or wasted bandwidth.

---

### 5. Build Procedure & CLI Workflow

1. **Generate All Sources**

   ```bash
   cd firmware
   python3 scripts/generate_firmware_sources.py --meta ../metadata --out Core
   ```

   In CubeIDE, set the same command as a Pre‐build step.

2. **Common CLI Commands**

   ```bash
   sensor-cli scan
   sensor-cli add --board 1 --addr 0x40 --sensor ina219
   sensor-cli setmask 0x07   # enable payload bits 0,1,2
   sensor-cli read           # reads and prints those fields
   sensor-cli setmask 0x02   # now only payload bit 1 is enabled
   sensor-cli read           # reads only that field
   ```

   * **scan**: Enumerate I²C boards
   * **add**: Register a sensor instance (board, address, type)
   * **setmask**: Update `payload_mask` for that sensor
   * **read**: Fetch a single batch of samples (exactly as many bytes as `sample_size()`)

---

### 6. Python Environment & Automated Tests

1. **Set up a Virtual Environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # or Windows equivalent
   ```

2. **Install & Run Tests**

   ```bash
   pip install -e master
   pip install -r master/requirements.txt
   pytest
   ```

   * Validates JSON schema, generator outputs, and HAL/driver consistency.

---

### 7. Master‐Side Improvements in v1.4.0

In addition to the driver‐side enhancements above, version 1.4.0 enhances the "master" layer in Python to automate discovery, configuration, and streaming:

* **StreamScheduler**

  * Periodically scans for all active boards and sensors, then schedules reads at each sensor’s default or configured interval.
  * Uses the standard `sched` module under the hood, running in its own thread to ensure continuous polling without blocking the main thread.

* **SensorBackend**

  * Wraps the existing `BoardManager` and `StreamScheduler`.
  * Manages modes: **IDLE**, **DISCOVERY**, and **STREAM**.

    * In **DISCOVERY**, it caches sensor configurations so CLI commands can read/write settings without re‐scanning every time.
    * In **STREAM**, it populates `StreamScheduler.subscriptions` based on each sensor’s `period` config (in 100 ms units → converted to seconds), then starts continuous polling.
  * Exposes high‐level methods:

    * `set_config(board, addr, sensor, field, value)` and `get_config_field(...)`
    * `get_all_configs(...)` to retrieve every config field at once
    * `set_payload_mask(board, addr, mask)` and `get_payload_mask(...)`
    * `read_samples(...)` that automatically uses the cached or retrieved mask.
  * Ensures thread safety with an internal lock around mode changes and subscription updates.

* **`stream` Command (in both `shell.py` and `click.py`)**

  * When invoked, triggers `SensorBackend.start_stream(callback)`.
  * The callback receives `(board, addr, sensor, records)` each time a batch is read.
  * Users can supply an interval to control how often summary prints occur, while the scheduler handles per‐sensor timing.

---

### 8. What’s New in v1.4.0

| Feature                               | Benefit                                                             |
| ------------------------------------- | ------------------------------------------------------------------- |
| **Runtime-selectable `payload_mask`** | Dynamically enable/disable any combination of measurements.         |
| **`sample_size(ctx)` Function**       | Computes exact byte count per sample, eliminating over-reads.       |
| **Auto-initialized Driver Registry**  | All sensors register themselves via “glue” code—no manual includes. |
| **StreamScheduler & SensorBackend**   | Automatic, thread‐safe scanning and polling of all sensors.         |
| **Cleaner Generator Split**           | Separation of protocol generation vs. sensor driver generation.     |
| **INA219 Voltage Interpretation Fix** | Correct 13-bit scaling → \~16,000 mV full scale.                    |
| **Stricter JSON Schema Enforcement**  | Early detection of metadata errors; fewer surprises.                |
| **Generator Test Suite**              | Verifies every major output class: protocol, drivers, registry.     |
| **Zero-edit “Add-a-Sensor” Flow**     | Drop a new sensor JSON, re-run, rebuild firmware—no manual edits.   |

> **Note**: v1.4.0 stores each sensor’s polling period in two places (driver context vs. task manager). This works but may be consolidated later to avoid divergence.

---

## Future Steps

1. **Refactor C Code for Testability**

   * Encapsulate all HAL/FreeRTOS calls behind interfaces so we can substitute mocks.
   * Move bit-manipulation and payload-packing logic into standalone functions (no hardware dependencies).

2. **Implement C Unit Tests**

   * Validate pure logic (bitmasks, sample\_size, scaling) in isolation (e.g., via Ceedling or CMock/CUnity).
   * Use a mock HAL layer to test driver‐API calls (`configure()`, `read()`, etc.) without real hardware.

3. **CI Pipeline Enhancements**

   * Automate JSON linting, generator invocation, build checks, and unit tests on every push/PR (e.g., GitHub Actions).
   * Optionally add hardware‐in‐loop tests if a rig is available.

4. **Documentation & Examples**

   * Flesh out a “How to Add a New Sensor” walkthrough:

     1. Write `<sensor>.json`
     2. Rebuild firmware
     3. Demonstrate CLI interaction for that sensor
   * Embed Doxygen comments in generated C code for easier browsing of API functions.

5. **Consolidate Polling Period Storage**

   * Move the authoritative period value into a single location (e.g., driver context) so that the task manager queries it directly, avoiding possible mismatches.

