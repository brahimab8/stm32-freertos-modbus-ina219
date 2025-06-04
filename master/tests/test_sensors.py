import os
import json
import pytest
from sensor_master.sensors import registry, SENSORS_DIR
from sensor_master.protocol import protocol

# Sensor metadata JSON files directory is exported by the sensors module

def get_sensor_files():
    return [f for f in os.listdir(SENSORS_DIR) if f.endswith('.json')]


def test_available_matches_metadata_files():
    files = get_sensor_files()
    names = {os.path.splitext(f)[0].lower() for f in files}
    assert set(registry.available()) == names


@pytest.mark.parametrize("sensor_file", get_sensor_files())
def test_payload_size_and_type_code(sensor_file):
    path = os.path.join(SENSORS_DIR, sensor_file)
    meta = json.load(open(path, 'r', encoding='utf-8'))
    name = meta['name'].lower()

    # type code matches protocol.sensors
    assert registry.type_code(name) == protocol.sensors[name]

    # payload size is computed exactly as in SensorRegistry._load():
    default_bits = meta.get('default_payload_bits', [])
    if default_bits:
        expected_size = sum(meta['payload_fields'][i]['size'] for i in default_bits)
    else:
        expected_size = sum(field['size'] for field in meta['payload_fields'])
    assert registry.payload_size(name) == expected_size

    # metadata returns full JSON
    assert registry.metadata(name) == meta


def test_type_code_unknown_raises():
    with pytest.raises(KeyError):
        registry.type_code('nonexistent_sensor')


def test_payload_size_unknown_raises():
    with pytest.raises(KeyError):
        registry.payload_size('nonexistent_sensor')


def test_metadata_unknown_raises():
    with pytest.raises(KeyError):
        registry.metadata('nonexistent_sensor')
