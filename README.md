# STM32 I²C Sensor Hub

**Centralized I²C sensor management over RS-485: STM32-based firmware with a Python CLI.**

---

## Quick Start

### Firmware (STM32)

```bash
git clone https://github.com/brahimab8/stm32-i2c-sensor-hub.git
cd stm32-i2c-sensor-hub/firmware/stm32-i2c-sensor-hub
````

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

* [Overview](docs/project-overview.md)
* [01 – Quick Setup](docs/01-setup.md)
* [02 – Sensor Task](docs/02-sensor-task.md)
* [03 – Sensor Tasks Manager](docs/03-sensor-manager.md)
* [04 – Command & Response Handling](docs/04-command-handling.md)
* [05 – Master Tools (CLI)](docs/05-master-tools.md)

---

## License

* **Project:** [MIT](LICENSE)
* **FreeRTOS (CMSIS-RTOS2):** MIT

```

