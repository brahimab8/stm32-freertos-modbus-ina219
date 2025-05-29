import json
import os
from .protocol import protocol

# locate metadata folder at repo root
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir, os.pardir))
SENSORS_DIR = os.path.join(REPO_ROOT, 'metadata', 'sensors')

class SensorRegistry:
    def __init__(self):
        self._load()

    def _load(self):
        self._types = {}           # name → type code
        self._reverse_types = {}   # type code → name   ← add this
        self._payload_sizes = {}   # name → total payload size
        self._metadata = {}        # name → full JSON metadata
        for fn in os.listdir(SENSORS_DIR):
            if not fn.endswith('.json'):
                continue
            path = os.path.join(SENSORS_DIR, fn)
            meta = json.load(open(path))
            name = meta['name'].lower()
            self._metadata[name] = meta
            type_code = protocol.sensors[name]
            self._types[name] = type_code
            self._reverse_types[type_code] = name
            size = sum(f['size'] for f in meta['payload_fields'])
            self._payload_sizes[name] = size

    def type_code(self, name: str) -> int:
        return self._types[name.lower()]

    def payload_size(self, name: str) -> int:
        return self._payload_sizes[name.lower()]

    def metadata(self, name: str) -> dict:
        """Return the raw JSON metadata for sensor `name`."""
        return self._metadata[name.lower()]

    def name_from_type(self, type_code: int) -> str:
        return self._reverse_types.get(type_code, f"unknown({type_code})")

    def available(self):
        """List all known sensor type names."""
        return list(self._metadata.keys())

    def parse_payload(self, name: str, raw: bytes) -> dict:
        """
        Given raw payload bytes for sensor `name`, return a dict
        mapping each field name to its integer (or hex) value.
        """
        md = self.metadata(name)
        out = {}
        offset = 0
        for fld in md['payload_fields']:
            chunk = raw[offset:offset + fld['size']]
            offset += fld['size']

            t = fld['type']
            if t.startswith('uint'):
                val = int.from_bytes(chunk, 'big', signed=False)
            elif t.startswith('int'):
                val = int.from_bytes(chunk, 'big', signed=True)
            else:
                val = chunk.hex()

            out[fld['name']] = val

        return out

registry = SensorRegistry()
