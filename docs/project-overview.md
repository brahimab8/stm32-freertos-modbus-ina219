# Project Overview

This document provides a high-level introduction to the **STM32 I²C Sensor Hub** project, its goals, and its architecture.

## Purpose

The STM32 I²C Sensor Hub is designed as a scalable gateway for managing multiple I²C sensors across many STM32-based nodes over an RS-485 bus. It consists of two main domains:

1. **Firmware (`firmware/`)**

   * Runs on STM32 microcontrollers under FreeRTOS/CMSIS-RTOS2.
   * Auto-generates framing protocol headers and sensor-default code from JSON metadata (`protocol.json` and `sensors/*.json`).
   * Implements a robust RS-485 framing layer (SOF + XOR checksum) in a dedicated CommandTask.
   * Manages per-sensor tasks via a SensorManager under a shared I²C mutex, each queuing sampled data.
   * Supports dynamic add/remove/configure of INA219 sensors at runtime; extendable to other sensor types or buses.
   * Optional debug console on USART2 for heap and stack monitoring.

2. **Master (`master/`)**

   * A Python-based CLI tool (`sensor-cli`) for PC/host interaction.
   * Discovers nodes (`scan`, `boards`, `ping`), manages sensors (`sensors`, `add`, `remove`, `set-*`), and retrieves data (`read`, `session`).
   * Designed for extensibility: scheduling, persistent storage, GUI/web interface.

## Technical Features

* **JSON-driven code generation** for protocol and sensor-default headers
* **Robust RS-485 framing** with SOF marker + XOR checksum
* **FreeRTOS-based architecture**: per-sensor tasks with FIFO queues and shared I²C mutex
* **Modular split**: independent `firmware/` and `master/` domains
* **Extensible protocol**: variable payload lengths and dynamic commands (Full protocol spec in [docs/protocol.md](docs/protocol.md)).
* **Python CLI**: full end-to-end control, including interactive sessions.

## Key Benefits

* **Scalable**: up to 31 nodes and multiple sensors per node (limited by heap and bus capacity).
* **Maintainable**: JSON-driven generation ensures consistency across firmware and CLI.
* **Extensible**: easy to add new sensors, commands, or microcontroller families.
* **Portable**: clear separation of embedded and host codebases.

## Architecture

A detailed overview of modules, data flows, and RTOS task structure is available in [docs/architecture.md](docs/architecture.md).

## Repository Structure

```
/docs               # Markdown tutorials and architecture overview
/firmware           # STM32CubeIDE project and scripts
  /stm32-i2c-sensor-hub
    /Core           # Auto-generated and source code
    /Drivers        # HAL and CMSIS code
    /Middlewares    # FreeRTOS sources
    /scripts        # Code-generation scripts
/metadata           # protocol.json and sensor metadata
/master             # Python CLI package and docs
.gitignore
LICENSE
README.md           # Top-level quickstart and links
```

---

[Home](index.md) • [Next (Architecture)](architecture.md)
