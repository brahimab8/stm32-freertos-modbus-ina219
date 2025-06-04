# generate_protocol.py

import os
import json

# Map our JSON types (e.g. "uint8", "int16") → C types
CTYPE = {
    "uint8": "uint8_t",
    "uint16": "uint16_t",
    "int16": "int16_t",
    "uint32": "uint32_t",
    "int32": "int32_t",
}

def gen_protocol(proto: dict, out_dir: str):
    """
    Generate Core/Inc/config/protocol.h from protocol.json
    """
    lines = [
        "/* Auto-generated from protocol.json; do not edit! */",
        "#pragma once",
        "#include <stdint.h>",
        "#include <stddef.h>",
        "",
    ]

    # 1) Simple constants
    lines.append("// Simple #defines")
    for k, v in proto.get("constants", {}).items():
        lines.append(f"#define {k:<20} {v}")
    lines.append("")
    lines.append("#define RESPONSE_HEADER_LENGTH  offsetof(RESPONSE_HEADER_t, length) + 1")
    lines.append("#define CMD_FRAME_SIZE sizeof(COMMAND_t)")
    lines.append("")

    # 2) Status codes
    lines.append("// Status codes")
    for k, v in proto.get("status_codes", {}).items():
        lines.append(f"#define {k:<20} {v}")
    lines.append("")

    # 3) Commands
    lines.append("// Command codes")
    for k, v in proto.get("commands", {}).items():
        lines.append(f"#define {k:<20} {v}")
    lines.append("")

    # 3.1) Command ranges
    ranges = proto.get("command_ranges", {})
    if ranges:
        lines.append("// Command ID ranges")
        for name, bounds in ranges.items():
            start_macro = f"CMD_{name.upper()}_START"
            end_macro   = f"CMD_{name.upper()}_END"
            lines.append(f"#define {start_macro:<30} {bounds[0]}")
            lines.append(f"#define {end_macro:<30} {bounds[1]}")
        lines.append("")

    # 4) Sensor-type codes (if any)
    sensors = proto.get("sensors", {})
    if sensors:
        lines.append("// Sensor type codes")
        for name, code in sensors.items():
            macro = f"SENSOR_TYPE_{name.upper()}"
            lines.append(f"#define {macro:<20} {code}")
        lines.append("")

    # 5) Frame structs
    for fname, frm in proto.get("frames", {}).items():
        struct = fname.upper()
        lines.append(f"// {frm.get('description','')}")
        lines.append("typedef struct {")
        for fld in frm.get("fields", []):
            t = fld["type"]
            nm = fld["name"]
            if t == "bytes":
                lines.append(f"    uint8_t {nm}[];")
            else:
                c = CTYPE.get(t, "uint8_t")
                lines.append(f"    {c} {nm};")
        lines.append(f"}} {struct}_t;")
        lines.append("")

    # Write out
    inc_dir = os.path.join(out_dir, "Inc", "config")
    os.makedirs(inc_dir, exist_ok=True)
    out_h = os.path.join(inc_dir, "protocol.h")
    with open(out_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_h}")
