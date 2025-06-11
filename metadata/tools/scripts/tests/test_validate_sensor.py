import json
from pathlib import Path
import pytest

from scripts.validate_sensor import validate_all

@ pytest.fixture
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
    repo_root = Path(__file__).parents[4]
    real_schema = repo_root / "metadata" / "sensor_schema.json"
    assert real_schema.exists(), "Cannot find sensor_schema.json"
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


def test_validator_accepts_good(temp_metadata):
    # Remove bad.json so only good.json remains
    (temp_metadata / "sensors" / "bad.json").unlink()

    # Should not raise and return None
    result = validate_all(
        str(temp_metadata / "sensors"),
        str(temp_metadata / "sensor_schema.json")
    )
    assert result is None


def test_validator_rejects_bad(temp_metadata):
    # Remove good.json, leaving only bad.json
    (temp_metadata / "sensors" / "good.json").unlink()

    # Now expect a SystemExit
    with pytest.raises(SystemExit) as excinfo:
        validate_all(
            str(temp_metadata / "sensors"),
            str(temp_metadata / "sensor_schema.json")
        )
    # exit code should be non-zero
    assert excinfo.value.code != 0
