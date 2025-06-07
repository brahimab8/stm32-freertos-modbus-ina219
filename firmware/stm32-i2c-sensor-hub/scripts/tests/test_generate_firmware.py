import json
from pathlib import Path

import pytest
from scripts.generate_firmware_sources import main

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

    # Copy the real sensor_schema.json from repo root/metadata
    REPO_ROOT = Path(__file__).parents[4]
    real_schema = REPO_ROOT / "metadata" / "sensor_schema.json"
    (root / "sensor_schema.json").write_bytes(real_schema.read_bytes())

    return root

def test_end_to_end_creates_protocol(tmp_path, full_meta):
    out = tmp_path / "out_Core"
    out.mkdir(parents=True, exist_ok=True)

    # Call in-process instead of via subprocess
    main(str(full_meta), str(out))

    # Check protocol.h was created
    prot_header = out / "Inc" / "config" / "protocol.h"
    assert prot_header.exists(), "protocol.h was not generated"

    # Check driver_registry snippets exist
    includes = out / "Src" / "driver_registry_sensors_includes.inc"
    calls    = out / "Src" / "driver_registry_sensors_calls.inc"
    assert includes.exists(), "driver_registry_sensors_includes.inc was not generated"
    assert calls.exists(),    "driver_registry_sensors_calls.inc was not generated"
