#!/usr/bin/env python3
"""
validate_sensor.py

Loads a JSON‐schema (sensor_schema.json) and verifies that every
sensor JSON in the metadata/sensors/ directory is compliant.
Exits with nonzero if any file is invalid.
"""

import os
import sys
import json
from jsonschema import Draft7Validator

def load_schema(schema_path: str) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_one(sensor_json_path: str, schema: dict) -> bool:
    """
    Returns True if <sensor_json_path> is valid according to the schema.
    If invalid, prints errors and returns False.
    """
    with open(sensor_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if not errors:
        return True

    print(f"\nERROR: {sensor_json_path} failed schema validation:")
    for err in errors:
        # err.path is a deque of JSON keys/indexes; join them into dot notation
        location = ".".join(str(p) for p in err.path)
        print(f"  - {location}: {err.message}")
    return False

def validate_all(sensors_dir: str, schema_path: str) -> None:
    schema = load_schema(schema_path)
    success = True

    for fn in sorted(os.listdir(sensors_dir)):
        if not fn.endswith(".json"):
            continue
        full = os.path.join(sensors_dir, fn)
        ok = validate_one(full, schema)
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
    validate_all(args.sensors, args.schema)
    print("All sensor JSON files validated successfully.")
