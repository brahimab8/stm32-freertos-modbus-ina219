#!/usr/bin/env python3
from pathlib import Path
from .common import render_template, write_file, snake_case


def gen_sensor_config(meta: dict, out_dir: Path):
    """
    Emit:
      • Inc/config/<sensor>_config.h
      • Src/config/<sensor>_config.c
    using Jinja2 templates.
    """
    name = meta.get("name")
    if not name:
        raise ValueError("Sensor metadata missing 'name' field")
    key = snake_case(name)
    UPPER = name.upper()

    # Prepare output directories
    inc_cfg_dir = Path(out_dir) / "Inc" / "config"
    src_cfg_dir = Path(out_dir) / "Src" / "config"
    inc_cfg_dir.mkdir(parents=True, exist_ok=True)
    src_cfg_dir.mkdir(parents=True, exist_ok=True)

    config_defaults = meta.get("config_defaults", {})
    config_fields = meta.get("config_fields", [])
    payload_fields = meta.get("payload_fields", [])
    default_payload_bits = meta.get("default_payload_bits", [])

    # JSON now includes 'count', 'width', and 'signed'
    for pf in payload_fields:
        pf['count'] = pf.get('count', 1)
        pf['width'] = pf.get('width', 1)
        pf['signed'] = pf.get('signed', False)
        # total bytes for each payload field
        pf['total_bytes'] = pf['count'] * pf['width']

    # Compute default_payload_size
    if default_payload_bits:
        try:
            default_payload_size = sum(
                payload_fields[i]['total_bytes']
                for i in default_payload_bits
            )
        except (IndexError, KeyError):
            raise ValueError(
                f"Invalid default_payload_bits index for sensor {name}"
            )
    else:
        default_payload_size = sum(
            pf['total_bytes'] for pf in payload_fields
        )

    # Map config_fields by name for lookup
    config_fields_map = { cf['name']: cf for cf in config_fields }

    ctx = {
        'name': name,
        'key': key,
        'UPPER': UPPER,
        'config_fields': config_fields,
        'config_fields_map': config_fields_map,
        'config_defaults': config_defaults,
        'payload_fields': payload_fields,
        'default_payload_bits': default_payload_bits,
        'default_payload_size': default_payload_size,
    }

    # Render and write
    hdr_out = inc_cfg_dir / f"{key}_config.h"
    write_file(hdr_out, render_template('sensor_config.h.j2', ctx))

    src_out = src_cfg_dir / f"{key}_config.c"
    write_file(src_out, render_template('sensor_config.c.j2', ctx))
