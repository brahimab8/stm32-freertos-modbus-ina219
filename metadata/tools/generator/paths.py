from pathlib import Path

def get_paths(metadata_root: Path):
    """
    Resolve important paths under the given `metadata/` root directory.
    """
    metadata_root = metadata_root.resolve()
    definitions_dir = metadata_root / "definitions"

    return {
        "METADATA_ROOT": metadata_root,
        "DEFINITIONS_DIR": definitions_dir,
        "SENSOR_SCHEMA": definitions_dir / "sensor_schema.json",
        "SENSORS_DIR": definitions_dir / "sensors",
        "PROTO_FILE": definitions_dir / "protocol.json",
    }

