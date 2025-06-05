# 07 Test Generated Drivers

*Corresponds to [version 1.4.1 of the repository](https://github.com/brahimab8/stm32-i2c-sensor-hub/tree/v1.4.1).*

## Objective
Make all generated sensor and configuration code testable in a plain C build (PC/CI) without STM32 HAL or FreeRTOS.

## Steps

1. **Add HAL-IF layer**  
   - Created `hal_if.h` (I²C init/read/write signatures).  
   * Provided a real `hal_if.c` for STM32 and a stub (`hal_if_stub.c`) that returns success and zero-fills reads.

2. **Update generator to emit HAL-IF calls**

   * Modified `generate_sensor_driver.py`.
   * Included `hal_if.h` instead of unguarded `stm32l4xx_hal.h`.
   * Swapped all `HAL_I2C_Master_…` calls for `halif_i2c_write/read()`.
   * Context structs now hold `halif_handle_t` instead of `I2C_HandleTypeDef*`.

3. **Exclude RTOS/task code from tests**

   * Test Makefile omits any FreeRTOS/CMSIS or `Core/Src/task/` files.
   * Only utility and driver sources are compiled under `-DTEST`.

4. **Build minimal test harness**

   * Wrote two test runners:

     1. **Response+Checksum tests** (`test_response.c` → `test_response_runner`) exercise `checksum.c` and `response_builder.c`.
     2. **Generated-driver tests** (`test_generated_drivers.c` → `test_drivers_runner`) exercise the INA219 code (initialization, sample-size/read/configure logic) via the registry and `hal_if_stub.c`.
   * Created a single Makefile that compiles each set under coverage flags (`-fprofile-arcs -ftest-coverage`) into two binaries: `test_response_runner` and `test_drivers_runner`.

5. **Generate coverage report**

   * Added a `coverage-html` target that zeroes counters, runs both test binaries, captures coverage data with `lcov`, and generates an HTML report via `genhtml`.

## Usage

On Linux (or using WSL), navigate to the `tests/` folder, then use `make` to build and run the tests:

```sh
make all
./test_response_runner
./test_drivers_runner
make coverage-html
```
Example output (open generated HTML-file for more detailed coverage stats):

```
Overall coverage rate:
  lines......: 65.6% (296 of 451 lines)
  functions..: 69.2% (27 of 39 functions)
```
