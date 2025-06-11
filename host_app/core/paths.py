from pathlib import Path

# Repo root is two levels up from this file
REPO_ROOT = Path(__file__).resolve().parents[2]

# Where our JSON lives
DEFINITIONS_DIR = REPO_ROOT / "metadata" / "definitions"
PROTO_FILE      = DEFINITIONS_DIR / "protocol.json"
SENSORS_DIR     = DEFINITIONS_DIR / "sensors"
