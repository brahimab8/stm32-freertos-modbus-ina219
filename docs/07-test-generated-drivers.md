# 07 Test Generated Drivers

## Objective
Make all generated sensor and configuration code testable in a plain C build (PC/CI) without STM32 HAL or FreeRTOS.

## Steps

1. **Add HAL-IF layer**  
   - Create `hal_if.h` (I²C init/read/write signatures).  
   - Provide `hal_if.c` (real HAL) and `hal_if_stub.c` (returns `HALIF_OK`).  
   - TODO: Implement these files.

2. **Update generator to emit HAL-IF calls**  
   - Modify `generate_sensor_driver.py` (and any scripts that produce sensor HAL wrappers) so that each generated driver:  
     - Includes `hal_if.h` instead of unguarded `stm32l4xx_hal.h`.  
     - Replaces any `HAL_I2C_Master_Transmit/Receive` calls with `halif_i2c_write/read()`.  
     - Defines context structs holding `halif_handle_t` instead of `I2C_HandleTypeDef*`.  
   - TODO: Regenerate one driver (e.g., INA219) and verify it compiles under `-DTEST`.

3. **Exclude RTOS/task code from tests**  
   - Ensure `Core/Src/task/` and `sensor_manager.c` are omitted in the test Makefile or build target.  
   - TODO: Adjust Makefile to only include driver and utility files.

4. **Build minimal test harness**  
   - Create `Core/tests/test_main.c` that exercises:  
     - `sample_size()` for various masks.  
     - `read_config()` dispatch logic.  
     - One utility (e.g. `compute_checksum()`).  
   - Add `Core/tests/Makefile` which compiles (with `-DTEST`):  
     - All generated driver sources (`Core/Src/drivers/*.c`).  
     - Utility sources (`Core/Src/utils/*.c`).  
     - `hal_if_stub.c` and `test_main.c`.  
     - Links into a `test_runner` executable.  
   - TODO: Populate tests and confirm `test_runner` passes.

