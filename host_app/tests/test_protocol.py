import os
import json
import pytest
from sensor_master.protocol import protocol, PROTO_FILE

def test_protocol_file_exists():
    assert os.path.isfile(PROTO_FILE), f"protocol.json not found at {PROTO_FILE}"

def test_protocol_consistency():
    # raw JSON
    with open(PROTO_FILE) as f:
        data = json.load(f)

    # JSON ↔ object
    assert protocol.constants == data["constants"]
    assert protocol.commands  == data["commands"]
    assert protocol.status_codes == data["status_codes"]

    # sensors lower-case + values match
    for raw_name, raw_code in data["sensors"].items():
        lc = raw_name.lower()
        assert lc in protocol.sensors
        assert protocol.sensors[lc] == raw_code

def test_protocol_roundtrip_keys():
    # load the raw JSON so we can compare
    with open(PROTO_FILE, 'r') as f:
        data = json.load(f)

    # top‐level sections
    for section in ('constants','commands','status_codes','sensors'):
        assert section in data, f"Missing '{section}' in protocol.json"

    # protocol object has same keys
    assert set(protocol.constants) == set(data['constants'])
    assert set(protocol.commands) == set(data['commands'])
    assert set(protocol.status_codes) == set(data['status_codes'])

    # sensors keys should be lower‐cased
    raw_sensors = data['sensors']
    assert all(k == k.lower() for k in protocol.sensors)
    # and the mapping should be identical values
    for name, code in raw_sensors.items():
        assert protocol.sensors[name.lower()] == code

def test_no_duplicate_command_or_status_values():
    # make sure no two commands share the same numeric code
    vals = list(protocol.commands.values())
    assert len(vals) == len(set(vals)), "Duplicate value in commands"
    vals = list(protocol.status_codes.values())
    assert len(vals) == len(set(vals)), "Duplicate value in status_codes"
