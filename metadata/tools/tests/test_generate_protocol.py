import json
from pathlib import Path
import pytest
from scripts.generate_firmware_sources import gen_protocol

# A minimal protocol dictionary for testing gen_protocol
PROTO_JSON = {
    "constants": {"FOO": 1},
    "status_codes": {"STATUS_OK": 0},
    "commands": {"CMD_NOOP": 0x10},
    "sensors": {},
    "frames": {},
}


def test_gen_protocol_creates_file(tmp_path):
    # Arrange: create metadata folder
    meta = tmp_path / "metadata"
    meta.mkdir()
    (meta / "protocol.json").write_text(json.dumps(PROTO_JSON))
    (meta / "sensors").mkdir()
    # copy schema from repo root
    repo_root = Path(__file__).parents[4]
    schema_src = repo_root / "metadata" / "sensor_schema.json"
    (meta / "sensor_schema.json").write_bytes(schema_src.read_bytes())

    # Arrange: create output directory
    out_dir = tmp_path / "out"
    (out_dir / "Inc" / "config").mkdir(parents=True, exist_ok=True)

    # Act: run the generator
    gen_protocol(PROTO_JSON, str(out_dir))

    # Assert: protocol.h was created and contains expected content
    header = out_dir / "Inc" / "config" / "protocol.h"
    assert header.exists(), "protocol.h was not generated"
    text = header.read_text()
    assert "#define STATUS_OK" in text
    assert "#define CMD_NOOP" in text
    assert "SENSOR_TYPE_" not in text
    assert "typedef struct" not in text
