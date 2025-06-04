#!/usr/bin/env python3
import os

def write_driver_registry_includes(all_sensors, out_dir: str):
    """
    Emit “driver_registry_sensors_includes.inc” containing:
      #include "drivers/<sensor>_driver.h"
      (one line per sensor)
    """
    inc_path = os.path.join(out_dir, "Src", "driver_registry_sensors_includes.inc")
    os.makedirs(os.path.dirname(inc_path), exist_ok=True)

    lines = []
    for sc, orig in all_sensors:
        lines.append(f'#include "drivers/{sc}_driver.h"    // for {orig}_RegisterDriver')
    lines.append("")

    with open(inc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"Wrote {inc_path}")


def write_driver_registry_calls(all_sensors, out_dir: str):
    """
    Emit “driver_registry_sensors_calls.inc” containing:
      <sensor>_RegisterDriver();
      (one line per sensor)
    """
    inc_path = os.path.join(out_dir, "Src", "driver_registry_sensors_calls.inc")
    os.makedirs(os.path.dirname(inc_path), exist_ok=True)

    lines = []
    for sc, orig in all_sensors:
        lines.append(f"    {sc}_RegisterDriver();")
    lines.append("")

    with open(inc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"Wrote {inc_path}")
