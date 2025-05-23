# STM32 FreeRTOS Modbus RTU Slave

---

## Description

This project integrates FreeModbus RTU with STM32Cube HAL and FreeRTOS on a Nucleo-L432KC:

* Reads voltage/current from an INA219 via I²C
* Exposes readings in Modbus holding registers
* Controls a GPIO (LED or relay) via Modbus coil writes

---

## Features

* FreeRTOS-based Modbus-RTU port on STM32Cube HAL
* RS-485 slave on **USART1** (optional DE control)
* INA219 I²C driver
* GPIO control for LED/relay
* Optional debug console on USART2

---

## Dependencies

* **FreeModbus v1.5.2** (BSD-2-Clause)
* **STM32Cube HAL & CMSIS**
* **FreeRTOS (CMSIS-RTOS2)**

---

## Setup

For step-by-step configuration (GPIO, I²C1, USART1, FreeRTOS, NVIC, timebase, etc.), see [Setup](docs/01-setup.md)

---

## Build & Flash

### STM32CubeIDE

git clone [https://github.com/brahimab8/stm32-freertos-modbus-ina219.git](https://github.com/brahimab8/stm32-freertos-modbus-ina219.git)
cd stm32-freertos-modbus-ina219
Open the .ioc in CubeIDE, generate code, then Build & Debug

### Command-Line

make        # Build
make flash  # Flash via ST-LINK

---

## License

* **Project:** MIT
* **FreeModbus:** BSD-2-Clause
* **FreeRTOS (CMSIS-RTOS2):** MIT
