import importlib.util
import sys
from pathlib import Path
import pytest
import types

SCRIPTS_DIR = (
    Path(__file__).parent
    / ".."
    / "firmware"
    / "stm32-i2c-sensor-hub"
    / "scripts"
).resolve()


@pytest.fixture(scope="module")
def generator_modules():
    """
    Dynamically load config_generator, hal_generator, and generate_sensor_driver modules.
    """
    # 1) Ensure the parent of “scripts/” is on sys.path
    package_root = SCRIPTS_DIR.parent
    sys.path.insert(0, str(package_root))

    mod_map = {}
    for fname, modname in [
        ("config_generator.py", "scripts.config_generator"),
        ("hal_generator.py", "scripts.hal_generator"),
        ("generate_sensor_driver.py", "scripts.generate_sensor_driver"),
    ]:
        path = SCRIPTS_DIR / fname
        spec = importlib.util.spec_from_file_location(modname, str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)
        mod_map[modname.split(".")[-1]] = module

    return (
        mod_map["config_generator"],
        mod_map["hal_generator"],
        mod_map["generate_sensor_driver"],
    )


@pytest.fixture
def toy_sensor_meta():
    """
    A minimal sensor‐metadata dictionary for “TestSensor”.
    """
    return {
        "name": "TestSensor",
        "config_defaults": {
            "gain": 2
        },
        "config_fields": [
            {
                "name":        "gain",
                "getter_cmd":  "CMD_GET_GAIN",
                "setter_cmd":  "CMD_SET_GAIN",
                "type":        "uint8",
                "size":        1,
                "reg_addr":    0x00,
                "mask":        "0xFF",
                "shift":       0,
                "endian":      "big",
                "driver_side": True
            }
        ],
        "payload_fields": [
            {
                "name":         "measurement",
                "type":         "uint16",
                "size":         2,
                "reg_addr":     0x01,
                "mask":         "0xFFFF",
                "shift":        0,
                "scale_factor": 1,
                "endian":       "big"
            }
        ],
        "default_payload_bits": [0]
    }


def test_gen_sensor_config_creates_expected(tmp_path, toy_sensor_meta, generator_modules):
    config_mod, _, _ = generator_modules

    # Prepare output directories
    out_dir = tmp_path / "out"
    (out_dir / "Inc" / "config").mkdir(parents=True, exist_ok=True)
    (out_dir / "Src" / "config").mkdir(parents=True, exist_ok=True)

    # Run config generation
    config_mod.gen_sensor_config(toy_sensor_meta, str(out_dir))

    sc = "testsensor"  # snake_case("TestSensor")
    # Check header + source
    hdr = out_dir / "Inc" / "config" / f"{sc}_config.h"
    src = out_dir / "Src" / "config" / f"{sc}_config.c"
    assert hdr.exists(), f"{hdr} not created"
    assert src.exists(), f"{src} not created"

    hdr_text = hdr.read_text()
    # The header should contain “TESTSENSOR_config_defaults_t” somewhere
    assert "TESTSENSOR_config_defaults_t" in hdr_text
    # And it should emit exactly “2” as the payload size (because default_payload_bits=[0])
    assert "#define SENSOR_PAYLOAD_SIZE_TESTSENSOR 2" in hdr_text
    # And it should declare the extern defaults variable
    assert "extern TESTSENSOR_config_defaults_t testsensor_defaults;" in hdr_text

    src_text = src.read_text()
    # The source should define that defaults struct with gain = 2
    assert "TESTSENSOR_config_defaults_t testsensor_defaults = {" in src_text
    assert ".gain = 2" in src_text


def test_gen_sensor_hal_wrapper_creates_hal(tmp_path, toy_sensor_meta, generator_modules):
    _, hal_mod, _ = generator_modules

    # Prepare output dirs
    out_dir = tmp_path / "out"
    (out_dir / "Inc" / "drivers").mkdir(parents=True, exist_ok=True)
    (out_dir / "Src" / "drivers").mkdir(parents=True, exist_ok=True)

    # Run HAL-wrapper generation
    hal_mod.gen_sensor_hal_wrapper(toy_sensor_meta, str(out_dir))

    sc = "testsensor"
    upper = "TESTSENSOR"

    # HAL‐wrapper header + source
    hal_hdr = out_dir / "Inc" / "drivers" / f"{sc}.h"
    hal_src = out_dir / "Src" / "drivers" / f"{sc}.c"
    assert hal_hdr.exists(), f"{hal_hdr} not created"
    assert hal_src.exists(), f"{hal_src} not created"

    hal_hdr_text = hal_hdr.read_text()
    # The HAL header must declare a prototype for reading “measurement”
    assert f"{upper}_ReadMeasurement" in hal_hdr_text

    hal_src_text = hal_src.read_text()
    # The HAL source must define the function “TESTSENSOR_ReadMeasurement(...)”
    assert f"{upper}_ReadMeasurement" in hal_src_text


def test_gen_sensor_driver_files_creates_driver(tmp_path, toy_sensor_meta, generator_modules):
    _, _, driver_mod = generator_modules

    # Prepare output dirs
    out_dir = tmp_path / "out"
    (out_dir / "Inc" / "drivers").mkdir(parents=True, exist_ok=True)
    (out_dir / "Src" / "drivers").mkdir(parents=True, exist_ok=True)

    # Run full driver generation (HAL + driver layer)
    driver_mod.gen_sensor_driver_files(toy_sensor_meta, str(out_dir))

    sc = "testsensor"
    upper = "TESTSENSOR"

    # 1) HAL‐wrapper header + source
    hal_hdr = out_dir / "Inc" / "drivers" / f"{sc}.h"
    hal_src = out_dir / "Src" / "drivers" / f"{sc}.c"
    assert hal_hdr.exists(), f"{hal_hdr} not created"
    assert hal_src.exists(), f"{hal_src} not created"

    # 2) Driver‐layer header + source
    drv_hdr = out_dir / "Inc" / "drivers" / f"{sc}_driver.h"
    drv_src = out_dir / "Src" / "drivers" / f"{sc}_driver.c"
    assert drv_hdr.exists(), f"{drv_hdr} not created"
    assert drv_src.exists(), f"{drv_src} not created"

    drv_hdr_text = drv_hdr.read_text()
    # The driver header should at least declare init_ctx and read_config
    assert "void testsensor_init_ctx" in drv_hdr_text
    assert "bool testsensor_read_config" in drv_hdr_text

    drv_src_text = drv_src.read_text()
    # The driver source should include the public init_ctx() and read_config() functions
    assert "void testsensor_init_ctx" in drv_src_text
    assert "bool testsensor_read_config" in drv_src_text
    # And it should pack exactly default_payload_bits into rd():
    assert "if (mask & BIT_MEASUREMENT)" in drv_src_text
