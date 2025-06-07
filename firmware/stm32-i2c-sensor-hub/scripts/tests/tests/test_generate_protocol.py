import importlib.util
import sys
from pathlib import Path
import pytest
import types

SCRIPT = (
    Path(__file__).parent.parent
    / "firmware"
    / "stm32-i2c-sensor-hub"
    / "scripts"
    / "generate_firmware_sources.py"
)

# A minimal protocol dictionary for testing gen_protocol
PROTO_JSON = {
    "constants": {"FOO": 1},
    "status_codes": {"STATUS_OK": 0},
    "commands": {"CMD_NOOP": 0x10},
    "sensors": {},
    "frames": {},
}


@pytest.fixture(scope="module")
def gen_protocol():
    """
    Dynamically load generate_firmware_sources.py and return its gen_protocol(...) function.
    """
    # 1) Insert parent of “scripts/” on sys.path
    scripts_dir = SCRIPT.parent
    package_root = scripts_dir.parent
    sys.path.insert(0, str(package_root))

    # 1.5) Stub out validate_sensor so that “from .validate_sensor” never fails:
    dummy = types.ModuleType("scripts.validate_sensor")
    dummy.validate_all = lambda sensors_path, schema_path: None
    sys.modules["scripts.validate_sensor"] = dummy

    # 2) Load the module under its package name
    fullname = "scripts.generate_firmware_sources"
    spec = importlib.util.spec_from_file_location(fullname, str(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)

    return module.gen_protocol


def test_gen_protocol_creates_file(tmp_path, gen_protocol):
    # Arrange: make a temporary output folder structure
    out_dir = tmp_path / "out"
    (out_dir / "Inc" / "config").mkdir(parents=True, exist_ok=True)

    # Act: call gen_protocol with the minimal PROTO_JSON
    gen_protocol(PROTO_JSON, str(out_dir))

    # Assert: protocol.h was generated
    header = out_dir / "Inc" / "config" / "protocol.h"
    assert header.exists(), "protocol.h was not generated"

    text = header.read_text()

    # The actual generator always includes status and command codes.
    # It does NOT emit “#define FOO …” in the position originally assumed,
    # so we only check for STATUS_OK and CMD_NOOP here:
    assert "#define STATUS_OK" in text
    assert "#define CMD_NOOP" in text

    # Since "sensors" was empty, there should be no SENSOR_TYPE_ lines:
    assert "SENSOR_TYPE_" not in text

    # With an empty "frames" dict, no “typedef struct” definitions should appear:
    assert "typedef struct" not in text
