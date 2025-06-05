#!/usr/bin/env python3
"""
Top‐level “umbrella” script.  Steps:

  1) Validate each sensor JSON against the JSON schema.
  2) Generate protocol.h from protocol.json.
  3) For each valid <sensor>.json to generate config + driver files.
  4) Generate driver_registry includes + calls.
"""

import os
import sys
import json
import argparse

from .validate_sensor import validate_all
from .generate_protocol import gen_protocol
from .config_generator import gen_sensor_config
from .generate_sensor_driver import gen_sensor_driver_files
from .driver_registry_helpers import write_driver_registry_includes, write_driver_registry_calls

def main(meta_dir: str, out_dir: str):
    # 1) Validate sensor JSONs
    schema_path  = os.path.join(meta_dir, "sensor_schema.json")
    sensors_path = os.path.join(meta_dir, "sensors")
    print(f"Validating sensor JSON files against {schema_path} …")
    validate_all(sensors_path, schema_path)
    print("... OK All sensor JSON files are valid.")

    # 2) Generate protocol.h
    proto_path = os.path.join(meta_dir, "protocol.json")
    with open(proto_path, "r", encoding="utf-8") as f:
        protocol = json.load(f)
    gen_protocol(protocol, out_dir)

    # 3) Loop over each <sensor>.json to generate files
    all_sensors = []
    for fn in sorted(os.listdir(sensors_path)):
        if not fn.endswith(".json"):
            continue

        path = os.path.join(sensors_path, fn)
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        print(f"\nGenerating for sensor: {meta['name']}")
        gen_sensor_config(meta, out_dir)
        gen_sensor_driver_files(meta, out_dir)

        # Build snake_case key for driver registry
        SC = "".join(ch if ch.isalnum() or ch=='_' else '_' for ch in meta["name"].lower())
        all_sensors.append((SC, meta["name"]))

    # 4) Generate driver_registry snippets
    write_driver_registry_includes(all_sensors, out_dir)
    write_driver_registry_calls(all_sensors, out_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate all C headers/source from protocol.json + sensor metadata"
    )
    parser.add_argument(
        "--meta", required=True,
        help="Metadata root (contains: protocol.json, sensor_schema.json, sensors/)"
    )
    parser.add_argument(
        "--out", required=True,
        help="Firmware root (e.g. the Core/ directory) where .h/.c will be written"
    )
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    try:
        main(args.meta, args.out)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
