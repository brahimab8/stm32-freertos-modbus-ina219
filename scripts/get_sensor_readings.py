#!/usr/bin/env python3
import os
import sys
import json
import serial
import struct
import time

# ————————————————————————————————————————————————————————————————————————————
SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
META_DIR     = os.path.join(PROJECT_ROOT, "metadata")
PROTO_FILE   = os.path.join(META_DIR, "protocol.json")
SENSORS_DIR  = os.path.join(META_DIR, "sensors")
# ————————————————————————————————————————————————————————————————————————————

# Load protocol constants and commands
with open(PROTO_FILE, "r") as f:
    proto = json.load(f)

# Extract constants
SOF_MARKER      = proto["constants"]["SOF_MARKER"]
TICK_BYTES      = proto["constants"]["TICK_BYTES"]
QUEUE_DEPTH     = proto["constants"]["QUEUE_DEPTH"]
CHECKSUM_LENGTH = proto["constants"]["CHECKSUM_LENGTH"]
STATUS_OK       = proto["constants"]["STATUS_OK"]
STATUS_ERROR    = proto["constants"]["STATUS_ERROR"]
STATUS_NOT_FOUND    = proto["constants"]["STATUS_NOT_FOUND"]
STATUS_UNKNOWN_CMD  = proto["constants"]["STATUS_UNKNOWN_CMD"]

# Extract commands
CMD_READ_SAMPLES = proto["commands"]["CMD_READ_SAMPLES"]
# CMD_ADD_SENSOR     = proto["commands"]["CMD_ADD_SENSOR"]
# CMD_REMOVE_SENSOR  = proto["commands"]["CMD_REMOVE_SENSOR"] 

# Build sensor → payload-size map from each sensors/<name>.json
SENSOR_PAYLOAD_SIZES = {}
for fn in os.listdir(SENSORS_DIR):
    if not fn.endswith(".json"):
        continue
    meta = json.load(open(os.path.join(SENSORS_DIR, fn)))
    name = meta["name"].lower()
    size = sum(field["size"] for field in meta["payload_fields"])
    SENSOR_PAYLOAD_SIZES[name] = size

# ————————————————————————————————————————————————————————————————————————————
def open_port(port="/dev/ttyUSB0", baud=115200, timeout=1):
    return serial.Serial(port, baud, timeout=timeout)

def read_exact(ser, n):
    data = ser.read(n)
    if len(data) < n:
        raise IOError(f"Timeout: expected {n} bytes, got {len(data)}")
    return data

def send_command(ser, board_id, addr7, cmd, param=0):
    """
    Send a 6-byte framed command:
      [ SOF | board_id | addr7 | cmd | param | checksum ]
    checksum = XOR of board_id, addr7, cmd, param
    """
    frame = bytearray(6)
    frame[0] = SOF_MARKER
    frame[1] = board_id
    frame[2] = addr7
    frame[3] = cmd
    frame[4] = param
    frame[5] = frame[1] ^ frame[2] ^ frame[3] ^ frame[4]
    ser.write(frame)

def recv_packet(ser):
    # Wait for SOF
    while True:
        b = ser.read(1)
        if not b:
            raise IOError("Timeout waiting for SOF")
        if b[0] == SOF_MARKER:
            break

    # Read header: board_id, addr7, cmd, status, length
    hdr = read_exact(ser, 5)
    board_id, addr7, cmd, status, length = struct.unpack("5B", hdr)

    # Read payload + checksum
    payload  = read_exact(ser, length)
    chksum_b = read_exact(ser, CHECKSUM_LENGTH)[0]

    # Verify XOR checksum over header[0..4] + payload
    chk = 0
    for byte in hdr + payload:
        chk ^= byte
    if chk != chksum_b:
        raise ValueError(f"Checksum mismatch: computed 0x{chk:02X}, got 0x{chksum_b:02X}")

    return {"board_id": board_id, "addr7": addr7, "cmd": cmd,
            "status": status, "payload": payload}

def parse_samples(packet, sample_size):
    """
    Split payload into (tick, payload_bytes) records.
    Each record is TICK_BYTES + sample_size long.
    """
    data   = packet["payload"]
    records = []
    offset = 0
    rec_len = TICK_BYTES + sample_size
    while offset + rec_len <= len(data):
        tick = struct.unpack_from(">I", data, offset)[0]
        offset += TICK_BYTES
        pl = data[offset:offset+sample_size]
        offset += sample_size
        records.append((tick, pl))
    if offset != len(data):
        print(f"Warning: {len(data)-offset} leftover bytes")
    return records

def parse_hex_arg(s):
    """
    Accepts “0x40” → 64, or plain “64” → 64.
    """
    s = s.strip().lower()
    if s.startswith("0x"):
        return int(s, 16)
    return int(s, 10)

# ————————————————————————————————————————————————————————————————————————————
def main(port, board_id, sensor_index, sensor_type):
    ser = open_port(port)
    time.sleep(0.1)  # settle

    stype = sensor_type.lower()
    if stype not in SENSOR_PAYLOAD_SIZES:
        print(f"Unknown sensor type '{sensor_type}', default to first")
        stype = next(iter(SENSOR_PAYLOAD_SIZES))
    sample_size = SENSOR_PAYLOAD_SIZES[stype]

    print(f"Request READ_SAMPLES @ addr=0x{sensor_index:02X} ({stype}), "
          f"payload={sample_size}B")

    # Send command frame
    send_command(ser, board_id, sensor_index, CMD_READ_SAMPLES, 0)

    pkt = recv_packet(ser)
    if pkt["status"] != STATUS_OK:
        print(f"Status {pkt['status']}, no data")
        return

    for i, (tick, pl) in enumerate(parse_samples(pkt, sample_size)):
        # Example for INA219: 2B voltage, 4B current
        voltage = (pl[0]<<8)|pl[1] if sample_size>=2 else None
        current = struct.unpack(">i", pl[2:6])[0] if sample_size>=6 else None
        print(f"Sample {i}: tick={tick} ms, voltage={voltage} mV, current={current} µA")

if __name__ == "__main__":
    if not (4 <= len(sys.argv) <= 5):
        print("Usage: python sensor_master.py <tty> <board_id> <addr7> [sensor_type]")
        print("  <board_id>   decimal or 0xNN hex, e.g. 1 or 0x01")
        print("  <addr7>      decimal or 0xNN hex sensor address, e.g. 64 or 0x40")
        print("Example:")
        print("  python sensor_master.py /dev/ttyUSB0 1 0x40 ina219")
        sys.exit(1)

    port         = sys.argv[1]
    board_id     = int(sys.argv[2], 0)
    sensor_index = parse_hex_arg(sys.argv[3])
    sensor_type  = sys.argv[4] if len(sys.argv)==5 else "ina219"
    main(port, board_id, sensor_index, sensor_type)
