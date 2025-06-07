[![Build Status](https://github.com/brahimab8/stm32-i2c-sensor-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/brahimab8/stm32-i2c-sensor-hub/actions)
[![Coverage](https://codecov.io/gh/brahimab8/stm32-i2c-sensor-hub/branch/main/graph/badge.svg)](https://codecov.io/gh/brahimab8/stm32-i2c-sensor-hub)

# STM32 I²C Sensor Hub

**Centralized I²C sensor management over RS-485: STM32-based firmware with a Python CLI.**

---

## Quick Start

### Firmware (STM32)

```bash
git clone https://github.com/brahimab8/stm32-i2c-sensor-hub.git
cd stm32-i2c-sensor-hub/firmware/stm32-i2c-sensor-hub
```

1. **Pre-build step** (Project → Properties → Build → Pre-build):

   ```bash
   python "${ProjDirPath}/scripts/generate_headers.py" \
     --meta "${ProjDirPath}/../../metadata" \
     --out  "${ProjDirPath}/Core"
   ```
2. Open `<project>.ioc` in STM32CubeIDE and generate code
3. Build and Debug

Or command-line:

```bash
make      # build
make flash  # flash via ST-LINK
```

### Master (Python CLI)

```bash
cd stm32-i2c-sensor-hub/master
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -e .[dev]
sensor-cli --help
```

---

## Documentation

* [Project overview](docs/project-overview.md)  
* [Architecture](docs/architecture.md)  
* [Protocol](docs/protocol.md)  
* [Resource Usage & Debug Output](docs/resource-usage.md)  

### Tutorials
1. [Quick Setup](docs/01-setup.md)  
2. [Sensor Task](docs/02-sensor-task.md)  
3. [Sensor Tasks Manager](docs/03-sensor-manager.md)  
4. [Command & Response Handling](docs/04-command-handling.md)  
5. [Master Tools (CLI)](docs/05-master-tools.md)  
6. [Sensor-Config Generator](docs/06-sensor-config-generator.md)  
7. [Test Generated Drivers](docs/07-test-generated-drivers.md)  

---

## Next Steps

- **Qt GUI frontend** for a desktop monitoring/control app  
- **Support additional sensor types** (SPI, analog, digital) beyond I²C  
- **Persistent storage**: log data on master (e.g. SQLite)  

---

## License

* **Project:** [MIT](LICENSE)
* **FreeRTOS (CMSIS-RTOS2):** MIT

```

