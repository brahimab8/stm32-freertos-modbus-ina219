#!/usr/bin/env python3
from pathlib import Path
from .common import render_template, write_file, snake_case, CTYPE

def gen_sensor_driver_files(meta: dict, out_dir: Path):
    """
    Emit:
      • Inc/drivers/<sensor>_driver.h
      • Src/drivers/<sensor>_driver.c
    """
    name = meta["name"]
    key = snake_case(name)
    UPPER = name.upper()

    config_fields = meta.get("config_fields", [])
    payload_fields = meta.get("payload_fields", [])
    config_defaults = meta.get("config_defaults", {})
    default_payload_bits = meta.get("default_payload_bits", [])
    default_payload_mask = sum(1 << bit for bit in default_payload_bits)

    # Annotate each field using JSON 'count', 'width', and 'signed'
    for field in config_fields + payload_fields:
        # JSON already contains 'count', 'width', 'signed'
        field['count'] = field.get('count', 1)
        field['width'] = field.get('width', 1)
        field['signed'] = field.get('signed', False)
        field["width_bytes"] = field.get("width", 1) * field.get("count", 1)

        # Map to C type or typedef
        base = field['type']
        field['base_ctype'] = CTYPE.get(base, base)
        # For arrays use C array syntax, else use typedef name
        if field['count'] > 1:
            field['ctype'] = f"{field['base_ctype']}[{field['count']}]"
        else:
            field['ctype'] = f"{UPPER}_{field['name'].upper()}_t"

    # Pre-compute config field IDs (for get_config_fields implementation)
    field_ids = [cf['getter_cmd'] for cf in config_fields
                 if cf['name'] != 'all' and cf.get('getter_cmd') and cf.get('setter_cmd')]

    ctx = {
        'name': name,
        'key': key,
        'config_fields': config_fields,
        'payload_fields': payload_fields,
        'config_defaults': config_defaults,
        'default_payload_bits': default_payload_bits,
        'default_payload_mask': default_payload_mask,
        'ctype_map': CTYPE,
        'field_ids': field_ids,
    }

    inc_dir = out_dir / 'Inc' / 'drivers'
    src_dir = out_dir / 'Src' / 'drivers'
    inc_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)

    hdr_out = inc_dir / f"{key}_driver.h"
    write_file(hdr_out, render_template('sensor_driver.h.j2', ctx))

    src_out = src_dir / f"{key}_driver.c"
    write_file(src_out, render_template('sensor_driver.c.j2', ctx))
