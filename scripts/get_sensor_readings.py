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
SOF_MARKER         = proto["constants"]["SOF_MARKER"]
TICK_BYTES         = proto["constants"]["TICK_BYTES"]
QUEUE_DEPTH        = proto["constants"]["QUEUE_DEPTH"]
CHECKSUM_LENGTH    = proto["constants"]["CHECKSUM_LENGTH"]
STATUS_OK          = proto["constants"]["STATUS_OK"]
STATUS_ERROR       = proto["constants"]["STATUS_ERROR"]

# Extract commands
CMD_READ_SAMPLES   = proto["commands"]["CMD_READ_SAMPLES"]
# CMD_ADD_SENSOR     = proto["commands"]["CMD_ADD_SENSOR"]
# CMD_REMOVE_SENSOR  = proto["commands"]["CMD_REMOVE_SENSOR"] 

# Build sensor → payload-size map from each sensors/<name>.json
SENSOR_PAYLOAD_SIZES = {}
for fn in os.listdir(SENSORS_DIR):
    if not fn.endswith(".json"):
        continue
    meta = json.load(open(os.path.join(SENSORS_DIR, fn)))
    name = meta["name"]
    # sum up the sizes in payload_fields
    size = sum(field["size"] for field in meta["payload_fields"])
    SENSOR_PAYLOAD_SIZES[name.lower()] = size

# ————————————————————————————————————————————————————————————————————————————
def open_port(port="/dev/ttyUSB0", baud=115200, timeout=1):
    return serial.Serial(port, baud, timeout=timeout)

def read_exact(ser, n):
    data = ser.read(n)
    if len(data) < n:
        raise IOError(f"Timeout: expected {n} bytes, got {len(data)}")
    return data

def send_command(ser, sensor_index):
    # sensor_index: integer 1..N → ASCII char '1'.. etc.
    ser.write(str(sensor_index).encode('ascii'))

def recv_packet(ser):
    # Wait for SOF
    while True:
        b = ser.read(1)
        if not b:
            raise IOError("Timeout waiting for SOF")
        if b[0] == SOF_MARKER:
            break

    # Read the rest of the 5-byte header: board_id, addr7, cmd, status, length
    hdr_bytes = read_exact(ser, 5)
    board_id, addr7, cmd, status, length = struct.unpack("5B", hdr_bytes)

    if cmd != CMD_READ_SAMPLES:
        raise ValueError(f"Unexpected command 0x{cmd:02X}, expected READ_SAMPLES")

    # Read payload + checksum
    payload   = read_exact(ser, length)
    chksum_b  = read_exact(ser, CHECKSUM_LENGTH)[0]

    # Verify checksum = XOR over header + payload
    chk = 0
    for byte in hdr_bytes + payload:
        chk ^= byte
    if chk != chksum_b:
        raise ValueError(f"Checksum mismatch: computed 0x{chk:02X}, got 0x{chksum_b:02X}")

    return {"board_id": board_id, "addr7": addr7, "status": status, "payload": payload}

def parse_samples(packet, sample_size):
    """
    Split payload into (tick, payload_bytes) records.
    Each record is TICK_BYTES + sample_size long.
    """
    data       = packet["payload"]
    recs       = []
    offset     = 0
    record_len = TICK_BYTES + sample_size

    while offset + record_len <= len(data):
        # 4-byte BE tick
        tick = struct.unpack_from(">I", data, offset)[0]
        offset += TICK_BYTES
        # sensor payload
        pl = data[offset : offset + sample_size]
        offset += sample_size
        recs.append((tick, pl))

    if offset != len(data):
        rem = len(data) - offset
        print(f"Warning: {rem} leftover bytes in payload")

    return recs

# ————————————————————————————————————————————————————————————————————————————
def main(port, sensor_index, sensor_type):
    ser = open_port(port)
    time.sleep(0.1)  # let UART settle

    stype = sensor_type.lower()
    if stype not in SENSOR_PAYLOAD_SIZES:
        print(f"Unknown sensor type '{sensor_type}', defaulting to first available")
        stype = next(iter(SENSOR_PAYLOAD_SIZES))

    sample_size = SENSOR_PAYLOAD_SIZES[stype]

    print(f"Requesting sensor #{sensor_index} ({stype}): "
          f"tick={TICK_BYTES}B + payload={sample_size}B...")

    send_command(ser, sensor_index)
    pkt = recv_packet(ser)

    if pkt["status"] != STATUS_OK:
        print(f"Sensor returned status {pkt['status']}, no data.")
        return

    records = parse_samples(pkt, sample_size)
    for i, (tick, pl) in enumerate(records):
        # Example for INA219: 2B voltage + 4B current
        voltage = (pl[0] << 8) | pl[1] if sample_size >= 2 else None
        current = struct.unpack(">i", pl[2:6])[0] if sample_size >= 6 else None

        print(f"Sample {i}: tick={tick} ms, voltage={voltage} mV, current={current} µA")

# ————————————————————————————————————————————————————————————————————————————
if __name__ == "__main__":
    if not (3 <= len(sys.argv) <= 4):
        print("Usage: python sensor_master.py <tty> <sensor#> [sensor_type]")
        print("Example: python sensor_master.py /dev/ttyUSB0 1 ina219")
        sys.exit(1)

    port         = sys.argv[1]
    sensor_index = int(sys.argv[2])
    sensor_type  = sys.argv[3] if len(sys.argv) == 4 else "ina219"
    main(port, sensor_index, sensor_type)
