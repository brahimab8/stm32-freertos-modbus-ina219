#!/usr/bin/env python3
"""
Top‐level “umbrella” script.  Steps:
  1) Validate each sensor JSON against the JSON schema.
  2) Generate protocol.h from protocol.json.
  3) For each valid <sensor>.json, generate config, driver, and HAL files.
  4) Generate driver_registry includes + calls.
"""

import sys
import json
import argparse
from pathlib import Path
import traceback

from .paths import get_paths
from .validate_sensor import validate_all
from .gen_protocol import gen_protocol
from .gen_sensor_config import gen_sensor_config
from .gen_sensor_driver import gen_sensor_driver_files
from .gen_sensor_hal import gen_sensor_hal_wrapper
from .driver_registry_helpers import gen_driver_registry_snippets


def main(metadata_root: Path, out_dir: Path):
    paths = get_paths(metadata_root)
    sensor_schema = paths["SENSOR_SCHEMA"]
    sensors_dir = paths["SENSORS_DIR"]
    proto_file = paths["PROTO_FILE"]
    # 1) Validate sensor JSONs
    print(f"Validating sensor JSON files against {sensor_schema} …")
    validate_all(str(sensors_dir), str(sensor_schema))
    print("... OK. All sensor JSON files are valid.")

    # 2) Generate protocol.h
    with proto_file.open("r", encoding="utf-8") as f:
        protocol = json.load(f)
    gen_protocol(protocol, out_dir)

    # 3) Loop over each <sensor>.json to generate files
    all_sensors = []
    for json_file in sorted(sensors_dir.glob("*.json")):
        try:
            meta = json.loads(json_file.read_text(encoding="utf-8"))
            print(f"\nGenerating for sensor: {meta.get('name', json_file.stem)}")

            gen_sensor_config(meta, out_dir)
            gen_sensor_driver_files(meta, out_dir)
            gen_sensor_hal_wrapper(meta, out_dir)

            key = "".join(ch if ch.isalnum() or ch == '_' else '_' for ch in meta.get("name", json_file.stem).lower())
            all_sensors.append((key, meta.get("name", json_file.stem)))
        except Exception:
            print(f"[ERROR] Failed processing {json_file.name}")
            traceback.print_exc()

    # 4) Generate driver_registry
    gen_driver_registry_snippets(all_sensors, out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate all C headers/source from metadata/definitions"
    )
    parser.add_argument("--meta", default="metadata", type=str,
                        help="Path to metadata/ folder (contains definitions/)")
    parser.add_argument("--out", required=True, type=str,
                        help="Output directory for generated firmware sources")
    args = parser.parse_args()

    metadata_root = Path(args.meta).resolve()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)

    try:
        main(metadata_root, output)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
