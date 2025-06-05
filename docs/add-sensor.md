**Add a New Sensor in Three Simple Steps**

1. **Drop in a single JSON**

   * Create `metadata/sensors/<sensor>.json` with at least:

     ```json
     {
       "name":       "<sensor>",           // lowercase, matches filenames
       "config_defaults": { … },           // default register values
       "config_fields": [ … ],             // each entry needs:
                                           //   "name", "getter_cmd", "setter_cmd",
                                           //   "type", "size", "reg_addr",
                                           //   "mask", "shift", "endian", "driver_side": true
       "payload_fields": [ … ],            // each entry needs:
                                           //   "name", "type", "size", "reg_addr",
                                           //   "mask", "shift", "scale_factor", "endian"
       "default_payload_bits": [ … ]       // (indices into payload_fields), optional
     }
     ```
   * Make sure your JSON validates against `sensor_schema.json`.

2. **Assign a new code in `protocol.json`**

   * Open `metadata/protocol.json` and under `"sensors"` add:

     ```diff
       "sensors": {
         "INA219":  1,
     +   "<SENSOR_UPPER>":  <new_code>
       }
     ```
   * Example:

     ```json
     { "sensors": { "INA219":1, "FOO123":2 } }
     ```

3. **Regenerate & rebuild**

   ```bash
   python3 scripts/generate_firmware_sources.py \
     --meta metadata \
     --out  firmware/stm32-i2c-sensor-hub/Core

   cd firmware/stm32-i2c-sensor-hub
   make clean && make && make flash
   ```

   This single command will:

   * Validate your new JSON.
   * Emit `Core/Inc/config/<sensor>_config.h` and `Core/Src/config/<sensor>_config.c`.
   * Emit `Core/Inc/drivers/<sensor>.h/c` (HAL-IF wrapper).
   * Emit `Core/Inc/drivers/<sensor>_driver.h/c` (driver layer).
   * Update registry includes/calls so `DriverRegistry_InitAll()` finds your sensor.

After that, you can use the Python CLI exactly as before:

```bash
cd master
sensor-cli add  --board 1 --addr 0x42 --sensor <sensor>
sensor-cli read --board 1 --addr 0x42 --sensor <sensor>
```

No manual edits to C files are required—just supply a valid JSON and assign a code in `protocol.json`.
