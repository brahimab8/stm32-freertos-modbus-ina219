#!/usr/bin/env python3
from pathlib import Path
from .common import render_template, write_file, snake_case, CTYPE


def gen_sensor_hal_wrapper(meta: dict, out_dir: Path):
    """
    Generate HAL wrapper files (.h and .c) for a single sensor.
    """
    name = meta["name"]
    key = snake_case(name)
    UPPER = name.upper()

    config_fields = meta.get("config_fields", [])
    payload_fields = meta.get("payload_fields", [])

    for field in config_fields + payload_fields:
        field['count'] = field.get('count', 1)
        field['width'] = field.get('width', 1)
        field['signed'] = field.get('signed', False)
        # Map raw type to C type
        base = field['type']
        field['base_ctype'] = CTYPE.get(base, base)
        # Build ctype for template: array or scalar
        if field['count'] > 1:
            field['ctype'] = f"{field['base_ctype']}[{field['count']}]"
        else:
            # scalar fields map to typedef names in sensor.h
            field['ctype'] = f"{UPPER}_{field['name'].upper()}_t"
        # Compute total byte width
        field['total_bytes'] = field['count'] * field['width']
        

    ctx = {
        "name": name,
        "key": key,
        "config_fields": config_fields,
        "payload_fields": payload_fields,
    }

    inc_dir = out_dir / "Inc" / "drivers"
    src_dir = out_dir / "Src" / "drivers"
    inc_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)

    hdr_out = inc_dir / f"{key}.h"
    write_file(hdr_out, render_template("sensor.h.j2", ctx))

    src_out = src_dir / f"{key}.c"
    write_file(src_out, render_template("sensor.c.j2", ctx))
