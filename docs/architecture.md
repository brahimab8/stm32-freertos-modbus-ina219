# Architecture Overview

This document outlines the key modules, data flows, and RTOS task structure of the STM32 I²C Sensor Hub firmware and its integration with the Python master tool.

---

## 1. High-Level Block Diagram

```mermaid
flowchart LR
  subgraph Host - PC
    direction TB
    SM["SensorMaster core<br>(framing, parsing)"]
    CLI["Frontends: sensor-cli / GUI / Web"]
    SM --> CLI
  end

  subgraph MCU - STM32 Node
    direction TB
    CmdTask["CommandTask<br>(UART1/RS-485 framing & dispatch)"]
    SensorMgr["SensorManager<br>(manage sensor tasks sharing an I²C Bus)"]
    subgraph I2C_Bus1["I²C Bus 1"]
      direction TB
      SensorTask["SensorTask<br>(periodic sampling)"]
      ExternalSensor["External Sensor Device"]
      SensorTask -->|I²C read/write| ExternalSensor
    end
    DebugTask["DefaultTask<br>(USART2 debug console)"]
  end

  CLI ---|RS-485 UART1| CmdTask
  CmdTask -->|API calls| SensorMgr
  SensorMgr -->|manage & arbitrate| I2C_Bus1
  DebugTask -->|stack/heap logs| USART2
```

Commands arrive framed over RS-485 into the CommandTask, get dispatched to the I²C Bus Manager, which controls SensorTasks for periodic sampling and reports status via the debug console.

---

## 2. FreeRTOS Task Table

| Task Name       | Purpose                                         | Priority    | Stack (bytes) | Activation             |
| :-------------- | :---------------------------------------------- | :---------- | :-----------: | :--------------------- |
| `CommandTask`   | UART/RS-485 frame parsing, checksum, dispatch   | Normal      |    192 × 4    | on UART1 RX interrupts |
| `SensorTask[i]` | Periodic I²C reads, enqueue samples             | BelowNormal |    128 × 4    | periodic (`period_ms`) |
| `DefaultTask`   | Debug: print heap & stack watermarks via USART2 | Normal      |    128 × 4    | periodic (1s)          |

* **Tip:** Use `uxTaskGetStackHighWaterMark()` and `xPortGetFreeHeapSize()` in debug builds to monitor resource usage.
* **Note:** The default heap size is set via `configTOTAL_HEAP_SIZE` (e.g. 8192 bytes) in `FreeRTOSConfig.h`, which limits the number of sensor tasks.

---

## 3. Data-Flow Sequence

```mermaid
sequenceDiagram
    participant Host as SensorMaster core
    participant CT as CommandTask
    participant SM as I²C Bus Manager
    participant ST as SensorTask
    participant I2C as I²C Bus

    Host->>CT: send [SOF, boardID, addr7, cmd, param, csum]
    CT->>CT: collect frame, verify SOF + XOR checksum
    CT->>SM: enqueue COMMAND_t to manager queue
    CT-->>Host: send STATUS or payload via ResponseBuilder

    alt READ_SAMPLES
      SM->>ST: SensorTask_ReadSamples(addr7)
      ST-->>SM: return SensorSample_t[]
      SM-->>CT: ResponseBuilder_BuildSamples(txbuf...)
      CT-->>Host: transmit framed response
    end

    Note over ST,I2C: SensorManager ensures orderly I²C access under busMutex
```

---

## 4. Python CLI (Master)

For end-to-end testing and control, see the [CLI documentation](docs/05-master-tools.md).

The SensorMaster core library can support multiple frontends: CLI, GUI, or web-based interfaces.

**Functionality**:

* **Board discovery**: `scan`, `boards`, `ping`
* **Sensor management**: `add`, `rmv`, `list`, `sensors`, `period`
* **Data retrieval & config**: `read`, `gain`, `range`, `calib`
* **Interactive mode**: `session`


---

[Home](index.md) • [Return (Overview)](project-overview.md) • [Next (Protocol)](protocol.md)

