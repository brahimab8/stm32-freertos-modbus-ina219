import json
import subprocess
import sys
from pathlib import Path

import pytest

# run “python -m scripts.generate_firmware_sources …”
SCRIPT_MODULE = "scripts.generate_firmware_sources"
PACKAGE_ROOT = Path(__file__).parent.parent / "firmware" / "stm32-i2c-sensor-hub"

PROTO_JSON = {
    "constants": {"FOO": 1},
    "status_codes": {"STATUS_OK": 0},
    "commands": {"CMD_NOOP": 0x10},
    "sensors": {},
    "frames": {}
}


@pytest.fixture
def full_meta(tmp_path):
    """
    Create a minimal metadata folder with just protocol.json and an empty sensors/ subfolder.
    """
    root = tmp_path / "metadata"
    root.mkdir()
    (root / "protocol.json").write_text(json.dumps(PROTO_JSON))

    (root / "sensors").mkdir()
    # No sensor JSON files needed for this smoke test.

    # Copy the real sensor_schema.json into place so the generator’s internal
    # validate_all(...) call (in generate_firmware_sources.py) will see it.
    real_schema = (Path(__file__).parent.parent / "metadata" / "sensor_schema.json")
    (root / "sensor_schema.json").write_bytes(real_schema.read_bytes())

    return root


def test_end_to_end_creates_protocol(tmp_path, full_meta):
    out = tmp_path / "out_Core"
    out.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        SCRIPT_MODULE,
        "--meta",
        str(full_meta),
        "--out",
        str(out),
    ]
    # Run inside PACKAGE_ROOT so that “scripts/…” imports resolve
    proc = subprocess.Popen(
        cmd,
        cwd=str(PACKAGE_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out_txt, err_txt = proc.communicate()
    assert proc.returncode == 0, f"Generator failed:\nSTDOUT:\n{out_txt}\nSTDERR:\n{err_txt}"

    # 1) Check protocol.h was created
    prot_header = out / "Inc" / "config" / "protocol.h"
    assert prot_header.exists(), "protocol.h was not generated"

    # 2) Check driver_registry snippets exist (even though there are no sensors)
    includes = out / "Src" / "driver_registry_sensors_includes.inc"
    calls = out / "Src" / "driver_registry_sensors_calls.inc"
    assert includes.exists(), "driver_registry_sensors_includes.inc was not generated"
    assert calls.exists(), "driver_registry_sensors_calls.inc was not generated"
    # Both may be empty or just contain blank lines when sensors = empty.
