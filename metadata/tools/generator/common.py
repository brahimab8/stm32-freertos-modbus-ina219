from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader

CTYPE = {
    "uint8":  "uint8_t",
    "uint16": "uint16_t",
    "int16":  "int16_t",
    "uint32": "uint32_t",
    "int32":  "int32_t",
}

# Path to the templates folder
HERE = Path(__file__).parent
TEMPLATES = HERE.parent / "templates"

# Jinja2 environment
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    trim_blocks=True,
    lstrip_blocks=True,
)

# --- Custom filters ---
def sanitize_label(lbl: str) -> str:
    import re
    return re.sub(r'[^A-Z0-9]', '_', str(lbl).upper())

env.filters["sanitize_label"] = sanitize_label

import re as _re
def regex_search(s: str, pattern: str):
    """
    Return a match object if `pattern` (a Python regex) matches somewhere in `s`, else None.
    Example use in template:
      {% set m = cf.type | regex_search("\\[(\\d+)\\]$") %}
      {% if m %} ... {% endif %}
    """
    return _re.search(pattern, s)

env.filters["regex_search"] = regex_search
# --- end filter registration ---

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def render_template(name: str, ctx: dict) -> str:
    tpl = env.get_template(name)
    return tpl.render(**ctx)

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {path}")

def snake_case(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower())
