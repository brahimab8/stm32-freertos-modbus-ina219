import json
import os
import struct
from .protocol import protocol

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir, os.pardir))
SENSORS_DIR = os.path.join(REPO_ROOT, 'metadata', 'sensors')


class SensorRegistry:
    """
    Loads all `<sensor_name>.json` files from metadata/sensors/ and
    provides:
      • type_code(name)           → numeric sensor type
      • name_from_type(type_code) → reverse mapping
      • payload_size(name)        → how many bytes the streaming payload is
      • metadata(name)            → the full JSON dict (including config_fields)
      • available()               → list of all sensor‐names
      • parse_payload(name, raw, mask)  → splits a raw-bytes payload into a dict
    """
    def __init__(self):
        self._load()

    def _load(self):
        self._types = {}           # name → type code
        self._reverse_types = {}   # type code → name
        self._payload_sizes = {}   # name → total payload size
        self._metadata = {}        # name → full JSON metadata
        for fn in os.listdir(SENSORS_DIR):
            if not fn.endswith('.json'):
                continue
            path = os.path.join(SENSORS_DIR, fn)
            meta = json.load(open(path, 'r', encoding='utf-8'))
            name = meta['name'].lower()

            # store raw JSON under registry
            self._metadata[name] = meta

            # look up the numeric type code from protocol.sensors[name]
            type_code = protocol.sensors[name]
            self._types[name] = type_code
            self._reverse_types[type_code] = name

            # compute “payload size”
            default_bits = meta.get('default_payload_bits', [])
            if default_bits:
                size = sum(meta['payload_fields'][i]['size']
                           for i in default_bits)
            else:
                size = sum(f['size'] for f in meta['payload_fields'])
            
            self._payload_sizes[name] = size

    def type_code(self, name: str) -> int:
        """Given a sensor‐name (e.g. "ina219"), return its numeric type code."""
        return self._types[name.lower()]

    def payload_size(self, name: str) -> int:
        """Return total streaming payload length (sum of that sensor’s payload_fields[].size)."""
        return self._payload_sizes[name.lower()]

    def metadata(self, name: str) -> dict:
        """
        Return the raw JSON metadata (as a Python dict) for sensor `name`.
        You can then inspect fields like:
          md['payload_fields']   (list of streaming‐payload descriptors)
          md['config_fields']    (list of config getter descriptors, if present)
          md['config_defaults']  (dictionary of default values)
          md['default_payload_bits']  (list of bit‐indices)
        """
        return self._metadata[name.lower()]

    def name_from_type(self, type_code: int) -> str:
        """
        Reverse lookup: given a numeric type_code, return the sensor‐name.
        If not found, returns e.g. "unknown(17)".
        """
        return self._reverse_types.get(type_code, f"unknown({type_code})")

    def available(self) -> list[str]:
        """List all known sensor type names (e.g. ["ina219", "mpu6050", …])."""
        return list(self._metadata.keys())

    def parse_payload(self, name: str, raw: bytes, mask: int) -> dict:
        """
        Given a raw payload (the bytes from CMD_READ_SAMPLES) AND a one-byte mask,
        split it according to that sensor’s `payload_fields` and return a dict.

        - 'mask' is a single byte: if bit k is set, then the k-th entry in
          payload_fields[] is present in this packet (in the same order).
        """
        md = self.metadata(name.lower())
        out = {}
        offset = 0

        # 1) First 4 bytes are always the tick (big‐endian uint32)
        if len(raw) < 4:
            # not enough data
            return {}
        out['tick'] = struct.unpack_from('>I', raw, offset)[0]
        offset += 4

        # 2) For each payload_field, only consume bytes if its bit is set
        for idx, fld in enumerate(md['payload_fields']):
            if not (mask & (1 << idx)):
                # skip this field entirely
                continue

            size = fld['size']
            if offset + size > len(raw):
                # incomplete packet
                return out
            chunk = raw[offset : offset + size]
            offset += size

            t = fld['type']
            if t.startswith('uint'):
                val = int.from_bytes(chunk, byteorder='big', signed=False)
            elif t.startswith('int'):
                val = int.from_bytes(chunk, byteorder='big', signed=True)
            else:
                # fallback: return hex string
                val = chunk.hex()

            out[fld['name']] = val

        return out

# single global registry instance
registry = SensorRegistry()
