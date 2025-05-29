# STM32 I²C Sensor Hub

---

## Description

A generic FreeRTOS/CMSIS‐RTOS2 framework for managing multiple I²C sensors on STM32, with:

- **Dynamic add/remove** of sensors at runtime  
- **Plugin drivers** (e.g. INA219, BMP280, HTU21D…) each in its own source file  
- **Per‐sensor configuration** (sampling period, measurement mask, gain/range, calibration)  
- **UART-command UI** for reading sensor data, raw register access, and runtime control  
- **GPIO outputs** (LEDs, relays) controllable via UART commands  

---

## Features

- **FreeRTOS-based SensorTask** per device, with fixed-rate sampling  
- **Bus arbitration** via a shared CMSIS mutex around all I²C traffic  
- **SensorManager** for high-level add/remove, configure, and read APIs  
- **UART command interface** on USART1 (6-byte packets)  
- **Raw register read/write** primitives for any managed device  
- **Optional debug console** on USART2  


---

## Dependencies

* **FreeRTOS (CMSIS-RTOS2)**
* **STM32Cube HAL & CMSIS**

---

## Architecture

For a high-level overview of modules, data flows, and RTOS tasks, see [docs/architecture.md](docs/architecture.md).

---

## Setup

Detailed peripheral and setup steps are in [docs/01-setup.md].

---
## Build & Flash

### STM32CubeIDE

```bash
git clone https://github.com/brahimab8/stm32-i2c-sensor-hub.git
cd stm32-i2c-sensor-hub
```

1. Open the `.ioc` file in STM32CubeIDE
2. Let CubeIDE generate code
3. Click **Build** then **Debug**

### Command-Line

```bash
make        # Build the project
make flash  # Flash via ST-LINK
```

---

## Usage (Python CLI)

A cross-platform Python interface lives in the `master/` folder:

* Scans RS-485 boards
* Adds/removes/configures I²C sensors
* Reads sensor data
* Offers both **scriptable commands** and an **interactive shell**

More in [`docs/05-master-tools.md`](docs/05-master-tools.md)

---

## License

* **Project:** [MIT](LICENSE)
* **FreeRTOS (CMSIS-RTOS2):** MIT
