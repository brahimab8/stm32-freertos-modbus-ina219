#!/usr/bin/env python3
"""
generate_headers.py

Reads protocol.json plus per-sensor JSON metadata from a directory and
auto-generates C headers and sensor-defaults C files.

Usage:
    python generate_headers.py --meta <metadata_dir> --out <project_core_dir>

Arguments:
    --meta    Path to a folder containing:
                • protocol.json
                • sensors/<sensor>.json
    --out     Destination directory for generated .h/.c files

Example:
    python3 scripts/generate_headers.py --meta metadata --out Core
"""
import os
import json
import argparse
import re

# map our JSON types to C types
CTYPE = {
    "uint8":  "uint8_t",
    "uint16": "uint16_t",
    "int16":  "int16_t",
    "uint32": "uint32_t",
    "int32":  "int32_t",
}

def snake_case(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower())

def gen_protocol(proto, out_dir):
    lines = [
        "/* Auto-generated from protocol.json; do not edit! */",
        "#pragma once",
        "#include <stdint.h>",
        "#include <stddef.h>",
        ""
    ]
    # constants
    lines.append("// Simple #defines")
    for k, v in proto.get("constants", {}).items():
        lines.append(f"#define {k:<20} {v}")
    lines.append("")
    lines.append("#define RESPONSE_HEADER_LENGTH  offsetof(RESPONSE_HEADER_t, length) + 1")
    lines.append(f"#define CMD_FRAME_SIZE sizeof(COMMAND_t)")
    lines.append("")

    # status_codes
    lines.append("// Status codes")
    for k, v in proto.get("status_codes", {}).items():
        lines.append(f"#define {k:<20} {v}")
    lines.append("")

    # commands
    lines.append("// Command codes")
    for k, v in proto.get("commands", {}).items():
        lines.append(f"#define {k:<20} {v}")
    lines.append("")

    # sensor‐type codes
    sensors = proto.get("sensors", {})
    if sensors:
        lines.append("// Sensor type codes")
        for name, code in sensors.items():
            # e.g. SENSOR_TYPE_INA219 1
            macro = f"SENSOR_TYPE_{name.upper()}"
            lines.append(f"#define {macro:<20} {code}")
        lines.append("")

    # frame structs
    for fname, frm in proto.get("frames", {}).items():
        struct = fname.upper()
        lines.append(f"// {frm.get('description','')}")
        lines.append(f"typedef struct {{")
        for fld in frm.get("fields", []):
            t = fld["type"]
            nm = fld["name"]
            if t == "bytes":
                # variable-length payload whose size is in the preceding “length” field
                lines.append(f"    uint8_t {nm}[];")
            else:
                c = CTYPE.get(t, "uint8_t")
                lines.append(f"    {c} {nm};")
        lines.append(f"}} {struct}_t;")
        lines.append("")

    # write out
    inc_dir = os.path.join(out_dir, "Inc", "config")
    os.makedirs(inc_dir, exist_ok=True)
    out_h = os.path.join(inc_dir, "protocol.h")
    with open(out_h, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_h}")

def gen_sensor_config(meta, out_dir):
    name = meta["name"]
    sc   = snake_case(name)
    struct = f"{sc}_config_defaults_t"

    # 1) header
    hdr = [
        f"/* Auto-generated {name} config */",
        "#pragma once",
        "#include <stdint.h>",
        f'#include "drivers/{snake_case(name)}.h"',
        ""
    ]
    # typedef
    hdr.append(f"typedef struct {{")
    for fld, val in meta.get("config_defaults", {}).items():
        if "gain" in fld:
            ctype = "INA219_Gain_t"
        elif "bus_range" in fld:
            ctype = "INA219_BusRange_t"
        else:
            ctype = "uint16_t"
        hdr.append(f"    {ctype} {fld};")
    hdr.append(f"}} {struct};")
    hdr.append("")

    # how many bytes every sample of this sensor produces:
    size = sum(fld["size"] for fld in meta["payload_fields"])
    MAC = snake_case(meta["name"]).upper()
    hdr.append(f"#define SENSOR_PAYLOAD_SIZE_{MAC} {size}")
    hdr.append("")

    # extern
    hdr.append(f"extern {struct} {sc}_defaults;")
    hdr.append("")

    inc_dir = os.path.join(out_dir, "Inc", "config")
    os.makedirs(inc_dir, exist_ok=True)
    out_h = os.path.join(inc_dir, f"{sc}_config.h")
    with open(out_h, "w") as f:
        f.write("\n".join(hdr))
    print(f"Wrote {out_h}")

    # 2) C file with definition
    src = [
        f"/* Auto-generated {name} defaults definition */",
        f'#include "config/{sc}_config.h"',
        ""
    ]
    src.append(f"{struct} {sc}_defaults = {{")
    for fld, val in meta.get("config_defaults", {}).items():
        src.append(f"    .{fld} = {val},")
    src.append("};")
    src.append("")

    src_dir = os.path.join(out_dir, "Src", "config")    
    os.makedirs(src_dir, exist_ok=True)
    out_c = os.path.join(src_dir, f"{sc}_config.c")
    with open(out_c, "w") as f:
        f.write("\n".join(src))
    print(f"Wrote {out_c}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", required=True,
                        help="metadata directory containing protocol.json and sensors/")
    parser.add_argument("--out",  required=True,
                        help="output directory for .h and .c files")
    args = parser.parse_args()

    # ensure output exists
    os.makedirs(args.out, exist_ok=True)

    # protocol.json → protocol.h
    with open(os.path.join(args.meta, "protocol.json"), "r") as f:
        protocol = json.load(f)
    gen_protocol(protocol, args.out)

    # every sensors/*.json → sensor_config.h + .c
    sdir = os.path.join(args.meta, "sensors")
    for fn in os.listdir(sdir):
        if not fn.endswith(".json"):
            continue
        meta = json.load(open(os.path.join(sdir, fn)))
        gen_sensor_config(meta, args.out)
