#!/usr/bin/env python3
"""
validate_sensor.py

Loads a JSON‐schema (sensor_schema.json) and verifies that every
sensor JSON in the metadata/sensors/ directory is compliant.
Exits with nonzero if any file is invalid.
"""

import sys
import json
from pathlib import Path
from jsonschema import Draft7Validator

def load_schema(schema_path) -> dict:
    """
    Load and return the JSON schema from the given path.
    Raises FileNotFoundError if not found or not a file.
    """
    p = Path(schema_path)
    if not p.is_file():
        raise FileNotFoundError(f"Schema file not found: {p}")
    try:
        text = p.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Failed to read or parse schema at {p}: {e}")

def validate_one(sensor_json_path, schema: dict) -> bool:
    """
    Validate a single sensor JSON file against the provided schema.
    Returns True if valid, False otherwise (and prints errors).
    """
    p = Path(sensor_json_path)
    if not p.is_file():
        print(f"WARNING: {p} is not a file; skipping", file=sys.stderr)
        return True

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"\nERROR: Failed to load JSON from {p}: {e}", file=sys.stderr)
        return False

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if not errors:
        return True

    print(f"\nERROR: {p} failed schema validation:", file=sys.stderr)
    for err in errors:
        # err.path is a deque; join into dot notation or show <root> if empty
        location = ".".join(str(elem) for elem in err.path) or "<root>"
        print(f"  - {location}: {err.message}", file=sys.stderr)
    return False

def validate_all(sensors_dir, schema_path) -> None:
    """
    Validate every `.json` file in sensors_dir against the JSON schema at schema_path.
    Exits with sys.exit(1) if any validation fails.
    """
    sensors_dir = Path(sensors_dir)
    schema = load_schema(schema_path)
    success = True

    if not sensors_dir.is_dir():
        raise NotADirectoryError(f"Sensors directory not found or not a directory: {sensors_dir}")

    # Iterate over .json files in sorted order
    for p in sorted(sensors_dir.iterdir()):
        if p.suffix.lower() != ".json":
            continue
        ok = validate_one(p, schema)
        if not ok:
            success = False

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate all sensor JSON files against sensor_schema.json"
    )
    parser.add_argument(
        "--schema", required=True,
        help="Path to sensor_schema.json"
    )
    parser.add_argument(
        "--sensors", required=True,
        help="Directory containing individual <sensor>.json files"
    )
    args = parser.parse_args()

    try:
        validate_all(args.sensors, args.schema)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("All sensor JSON files validated successfully.")
