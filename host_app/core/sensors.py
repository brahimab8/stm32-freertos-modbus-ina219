import json
import os
import struct
from .paths import SENSORS_DIR
from .protocol import protocol

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
            with open(path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            name = meta["name"].lower()
            self._metadata[name] = meta

            # numeric type code
            type_code = protocol.sensors[name]
            self._types[name] = type_code
            self._reverse_types[type_code] = name

            # compute payload_size from metadata count*width
            payload_fields = meta.get("payload_fields", [])
            default_bits = meta.get("default_payload_bits", [])

            def field_bytes(f):
                count = f.get("count", 1)
                width = f.get("width", 1)
                return count * width

            if default_bits:
                size = 0
                for idx in default_bits:
                    try:
                        fld = payload_fields[idx]
                    except IndexError:
                        continue
                    size += field_bytes(fld)
            else:
                size = sum(field_bytes(f) for f in payload_fields)

            self._payload_sizes[name] = size

    def type_code(self, name: str) -> int:
        return self._types[name.lower()]

    def payload_size(self, name: str) -> int:
        return self._payload_sizes[name.lower()]

    def metadata(self, name: str) -> dict:
        return self._metadata[name.lower()]

    def name_from_type(self, type_code: int) -> str:
        return self._reverse_types.get(type_code, f"unknown({type_code})")

    def available(self) -> list[str]:
        return list(self._metadata.keys())

    def parse_payload(self, name: str, raw: bytes, mask: int) -> dict:
        md = self.metadata(name)
        out = {}
        offset = 0

        # First 4 bytes: tick (unsigned 32-bit big-endian)
        if len(raw) < 4:
            return {}
        out["tick"] = struct.unpack_from(">I", raw, offset)[0]
        offset += 4

        for idx, fld in enumerate(md.get("payload_fields", [])):
            if not (mask & (1 << idx)):
                continue

            count = fld.get("count", 1)
            width = fld.get("width", 1)
            size = count * width

            if offset + size > len(raw):
                break

            chunk = raw[offset : offset + size]
            offset += size

            signed = fld.get("signed", False)
            reg_mask = int(fld["mask"], 16) if fld.get("mask") else None

            if count == 1:
                if signed:
                    val = int.from_bytes(chunk, "big", signed=True)
                else:
                    val = int.from_bytes(chunk, "big", signed=False)
                    if reg_mask is not None:
                        val &= reg_mask
            else:
                vals = []
                for i in range(0, size, width):
                    sub = chunk[i : i + width]
                    if signed:
                        v = int.from_bytes(sub, "big", signed=True)
                    else:
                        v = int.from_bytes(sub, "big", signed=False)
                        if reg_mask is not None:
                            v &= reg_mask
                    vals.append(v)
                val = vals

            out[fld["name"]] = val

        return out

# single global registry instance
registry = SensorRegistry()
