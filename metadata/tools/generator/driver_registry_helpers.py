#!/usr/bin/env python3
from pathlib import Path
from .common import render_template, write_file

def gen_driver_registry_snippets(all_sensors: list[tuple[str,str]], out_dir: Path):
    """
    Renders and writes both:
      - Src/driver_registry_sensors_includes.inc
      - Src/driver_registry_sensors_calls.inc
    """
    ctx = {"sensors": all_sensors}
    # Includes
    inc_out = out_dir / "Src" / "driver_registry_sensors_includes.inc"
    inc_text = render_template("driver_registry_includes.inc.j2", ctx)
    write_file(inc_out, inc_text)

    # Calls
    calls_out = out_dir / "Src" / "driver_registry_sensors_calls.inc"
    calls_text = render_template("driver_registry_calls.inc.j2", ctx)
    write_file(calls_out, calls_text)
