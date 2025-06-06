#!/usr/bin/env python3
import os
import re

# ——————————————————————————————————————————————————————————————————————
# Shared helpers (CTYPE, ARRAY_TYPE_RE, snake_case, CTYPEDTLS_IF_ARRAY)
# ——————————————————————————————————————————————————————————————————————
CTYPE = {
    "uint8":  "uint8_t",
    "uint16": "uint16_t",
    "int16":  "int16_t",
    "uint32": "uint32_t",
    "int32":  "int32_t",
}
ARRAY_TYPE_RE = re.compile(r"^([a-z0-9]+)\[(\d+)\]$")


def snake_case(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower())


def CTYPEDTLS_IF_ARRAY(type_key: str, typedef: str) -> str:
    """
    If type_key is like "uint8[2]", return the typedef (e.g. "INA219_GAIN_t").
    Otherwise return CTYPE.get(type_key, "uint16_t").
    """
    m = ARRAY_TYPE_RE.match(type_key)
    if m:
        return typedef
    else:
        return CTYPE.get(type_key, "uint16_t")


# ——————————————————————————————————————————————————————————————————————
# “Config” code-generation: header + source
# ——————————————————————————————————————————————————————————————————————
def build_config_header_lines(name: str, meta: dict) -> list[str]:
    """
    Build lines for the config header file.
    """
    SC = snake_case(name)
    UPPER = name.upper()
    struct = f"{UPPER}_config_defaults_t"

    lines = [
        f"/* Auto-generated {name} config */",
        "#pragma once",
        "#include <stdint.h>",
        f"#include \"drivers/{SC}.h\"",
        "",
        "typedef struct {"
    ]

    # struct fields for config_defaults
    for fld_name in meta.get("config_defaults", {}):
        ctype = f"{UPPER}_{fld_name.upper()}_t"
        lines.append(f"    {ctype} {fld_name};")
    lines.append(f"}} {struct};")
    lines.append("")

    # compute default payload size
    payload_fields = meta.get("payload_fields", [])
    default_bits = meta.get("default_payload_bits", [])
    if default_bits:
        size = sum(payload_fields[i]["size"] for i in default_bits)
    else:
        size = sum(fld["size"] for fld in payload_fields)

    lines.append(f"#define SENSOR_PAYLOAD_SIZE_{UPPER} {size}")
    lines.append("")
    lines.append(f"extern {struct} {SC}_defaults;")
    lines.append("")

    return lines


def build_config_source_lines(name: str, meta: dict) -> list[str]:
    """
    Build lines for the config source (.c) file.
    """
    SC = snake_case(name)
    UPPER = name.upper()
    struct = f"{UPPER}_config_defaults_t"

    lines = [
        f"/* Auto-generated {name} defaults definition */",
        f"#include \"config/{SC}_config.h\"",
        ""
    ]
    lines.append(f"{struct} {SC}_defaults = {{")

    for cf in meta.get("config_fields", []):
        if cf.get("setter_cmd") is None:
            # skip any field that has no setter (e.g. “calibration”)
            continue
        fld_name = cf["name"]
        defaults = meta.get("config_defaults", {})
        if fld_name not in defaults:
            continue
        val = defaults[fld_name]
        typedef = f"{UPPER}_{fld_name.upper()}_t"
        label_map = cf.get("enum_labels")
        if label_map and str(val) in label_map:
            enum_suffix = re.sub(r"[^A-Z0-9]+", "_", label_map[str(val)].upper())
            enum_const = f"{UPPER}_{fld_name.upper()}_{enum_suffix}"
            lines.append(f"    .{fld_name} = {enum_const},")
        else:
            lines.append(f"    .{fld_name} = {val},")
    lines.append("};")
    lines.append("")
    return lines


def gen_sensor_config(meta: dict, out_dir: str):
    """
    Emit:
     • Core/Inc/config/<sensor>_config.h
     • Core/Src/config/<sensor>_config.c
    """
    name = meta["name"]
    SC = snake_case(name)

    inc_cfg_dir = os.path.join(out_dir, "Inc", "config")
    src_cfg_dir = os.path.join(out_dir, "Src", "config")
    os.makedirs(inc_cfg_dir, exist_ok=True)
    os.makedirs(src_cfg_dir, exist_ok=True)

    # Write header
    out_h = os.path.join(inc_cfg_dir, f"{SC}_config.h")
    hdr_lines = build_config_header_lines(name, meta)
    with open(out_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hdr_lines))
    print(f"Wrote {out_h}")

    # Write source
    out_c = os.path.join(src_cfg_dir, f"{SC}_config.c")
    src_lines = build_config_source_lines(name, meta)
    with open(out_c, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(src_lines))
    print(f"Wrote {out_c}")
