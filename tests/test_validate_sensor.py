import json
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).parent.parent / "firmware" / "stm32-i2c-sensor-hub"
VALIDATOR_MODULE = "scripts.validate_sensor"


@pytest.fixture
def temp_metadata(tmp_path):
    """
    Creates a temporary metadata folder structure:
      metadata/
        sensor_schema.json
        sensors/
          good.json
          bad.json
    """
    root = tmp_path / "metadata"
    root.mkdir()
    sensors_dir = root / "sensors"
    sensors_dir.mkdir()

    # Copy over the real schema so validator can find it:
    real_schema = Path(__file__).parent.parent / "metadata" / "sensor_schema.json"
    assert real_schema.exists(), "Cannot find your real sensor_schema.json"
    (root / "sensor_schema.json").write_bytes(real_schema.read_bytes())

    # 1) Good sensor JSON (fits schema exactly)
    good = {
        "name": "example",
        "config_defaults": {"gain": 1},
        "config_fields": [
            {
                "name": "gain",
                "getter_cmd": "CMD_GET_GAIN",
                "setter_cmd": "CMD_SET_GAIN",
                "type": "uint8",
                "size": 1,
                "reg_addr": 0,
                "mask": "0xFF",
                "shift": 0,
                "endian": "big",
                "driver_side": True
            }
        ],
        "payload_fields": [
            {
                "name": "value",
                "type": "uint16",
                "size": 2,
                "reg_addr": 0x10,
                "mask": "0xFFFF",
                "shift": 0,
                "endian": "big",
                "scale_factor": 1
            }
        ],
        "default_payload_bits": [0]
    }
    (sensors_dir / "good.json").write_text(json.dumps(good, indent=2))

    # 2) Bad sensor JSON (extra "$schema" property not allowed)
    bad = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "name": "invalid",
        "config_defaults": {},
        "config_fields": [],
        "payload_fields": [],
        "default_payload_bits": []
    }
    (sensors_dir / "bad.json").write_text(json.dumps(bad, indent=2))

    return root


def run_validator(meta_dir):
    """
    Helper to run the validator script via “python -m scripts.validate_sensor …”
    Returns (exitcode, stdout, stderr).
    """
    cmd = [
        sys.executable,
        "-m",
        VALIDATOR_MODULE,
        "--schema",
        str(meta_dir / "sensor_schema.json"),
        "--sensors",
        str(meta_dir / "sensors"),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(PACKAGE_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate()
    return proc.returncode, out, err


def test_validator_accepts_good(temp_metadata):
    # Remove bad.json so only good.json remains
    (temp_metadata / "sensors" / "bad.json").unlink()

    rc, out, err = run_validator(temp_metadata)
    assert rc == 0, f"Validator should accept good.json, but failed:\nSTDOUT:\n{out}\nSTDERR:\n{err}"
    # Updated success message
    assert "All sensor JSON files validated successfully." in out


def test_validator_rejects_bad(temp_metadata):
    # Remove good.json, leaving only bad.json
    (temp_metadata / "sensors" / "good.json").unlink()

    rc, out, err = run_validator(temp_metadata)
    assert rc != 0, "Validator should fail for JSON with extra properties"
    combined = (out or "") + (err or "")
    assert "failed schema validation" in combined.lower() or "error" in combined.lower()
