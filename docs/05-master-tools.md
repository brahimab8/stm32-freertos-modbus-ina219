# Master Tools (CLI)

A modular Python backend lives under the new `master/` folder.
It exposes a consistent API for RS-485 board discovery, command framing, and sensor operations—driven today by a command-line tool; GUI or web front-ends will come later.

*This tutorial matches [v1.3.0 of the code](https://github.com/brahimab8/stm32-i2c-sensor-hub/tree/v1.3.0).*

---

## 1. Install & Dev Setup

1. Create and activate a virtualenv.
2. From the repo root run **one** of the following:

   - `pip install -e master`  
     Installs only the runtime CLI (i.e. `pyserial` & `click` deps).
   - `pip install -e master[dev]`  
     Installs the CLI **and** development tools (`pytest`, `pytest-cov`, etc.), to run tests.

## 2. Dependency Management

* Declare runtime deps in `master/requirements.in` (e.g. `pyserial`, `click`).
* Pin with:

  ```
  cd master
  pip install pip-tools
  pip-compile requirements.in
  ```

---

## 3. CLI Usage

* **Scan boards:**
  `sensor-cli scan --port COM3 --baud 115200`
* **Ping a board:**
  `sensor-cli ping --board 2`
* **Add a sensor:**
  `sensor-cli add --board 1 --addr 0x40 --sensor ina219`
* **Read samples:**
  `sensor-cli read --board 1 --addr 0x40 --sensor ina219`
* **Interactive shell:**
  `sensor-cli session`

---

## 4. Testing

Simply run:

```
pytest -v
```

Hardware I/O is fully mocked.

---
## 5. Core Class Diagram

```mermaid
classDiagram
    class Protocol {
        +constants: dict
        +commands: dict
        +status_codes: dict
        +sensors: dict
    }

    class SensorRegistry {
        +_types: dict
        +_payload_sizes: dict
        +_metadata: dict
        +available(): list
        +type_code(name): int
        +payload_size(name): int
        +metadata(name): dict
        +parse_payload(name, raw): dict
    }

    class SensorMaster {
        +port: str
        +baudrate: int
        +timeout: float
        +read_samples(board_id, addr, sensor_name): list~dict~
        +add_sensor(board_id, addr, sensor_name): int
        +remove_sensor(board_id, addr): int
        +set_period(board_id, addr, ms): int
        +set_gain(board_id, addr, code): int
        +set_range(board_id, addr, code): int
        +set_cal(board_id, addr, code): int
        +ping(board_id): int
    }

    class BoardManager {
        +port: str
        +baud: int
        +timeout: float
        +scan(start=1, end=255): list~int~
        +ping(board_id): int
        +select(board_id): BoundMaster
    }

    class BoundMaster {
        +ping(): int
        +read_samples(addr, sensor_name): list~dict~
        +add_sensor(addr, sensor_name): int
        +remove_sensor(addr): int
        +set_period(addr, ms): int
        +set_gain(addr, code): int
        +set_range(addr, code): int
        +set_cal(addr, code): int
    }

    %% relationships
    Protocol <|-- SensorMaster
    Protocol <|-- SensorRegistry
    SensorMaster --> SensorRegistry : uses
    BoardManager --> SensorMaster : holds
    BoardManager --> BoundMaster : creates
    BoundMaster --> SensorMaster : delegates
```

---
## 6. Future improvements

* **GUI:** PyQt-based desktop client
* **Web:** Flask-powered REST API

Both will reuse the same `BoardManager`/`SensorMaster` core so any new interface is compatible.
