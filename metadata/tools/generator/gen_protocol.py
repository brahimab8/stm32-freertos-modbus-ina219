#!/usr/bin/env python3
from pathlib import Path
from .common import render_template, write_file, CTYPE

def gen_protocol(proto: dict, out_dir: Path):
    """
    Generate protocol.h from the given protocol dictionary.
    - proto: dict loaded from protocol.json (caller is responsible for loading JSON).
    - out_dir: Path to firmware root; we will write to out_dir/Inc/config/protocol.h.
    """
    # Build Jinja2 context from proto dict
    ctx = {
        "constants":      proto.get("constants", {}),
        "status_codes":   proto.get("status_codes", {}),
        "commands":       proto.get("commands", {}),
        "command_ranges": proto.get("command_ranges", {}),
        "sensors":        proto.get("sensors", {}),
        "frames":         proto.get("frames", {}),
        "ctype_map":      CTYPE,
    }

    # Determine output path
    out_path = Path(out_dir) / "Inc" / "config" / "protocol.h"

    # Ensure parent directories exist
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Render template named "protocol.h.j2"
    content = render_template("protocol.h.j2", ctx)

    # Write file
    write_file(out_path, content)

    print(f"Wrote {out_path}")
