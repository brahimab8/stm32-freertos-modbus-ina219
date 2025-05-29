#!/usr/bin/env python3
import os
import sys
import json
import serial
import struct
import time

# ————————————————————————————————————————————————————————————————————————————
#  “print usage” helper
def print_usage_and_exit():
    print("Usage: sensor_master.py <tty> <board_id> <addr7> "
          "<ping|read|add|rmv|period|gain|range|cal> [value_or_type]\n")
    print("  <ping>            no extra parameter, check board liveness (unused addr)")
    print("  <read>            no extra parameter, just dump samples")
    print("  <add>             value_or_type = sensor type (e.g. ina219)")
    print("  <rmv>             no extra parameter, just remove by addr")
    print("  <period>          value_or_type = new poll period in ms")
    print("  <gain>            value_or_type = gain setting code (driver-specific)")
    print("  <range>           value_or_type = input range code (driver-specific)")
    print("  <cal>             value_or_type = calibration code (driver-specific)\n")

    # print out each sensor’s defaults from its JSON
    print("Default sensor configs:")
    for fn in os.listdir(SENSORS_DIR):
        if not fn.endswith(".json"):
            continue
        meta = json.load(open(os.path.join(SENSORS_DIR, fn)))
        cd   = meta.get("config_defaults", {})
        name = meta.get("name", fn[:-5])
        print(f"  {name}: gain={cd.get('gain')}, "
              f"bus_range={cd.get('bus_range')}, "
              f"calibration={cd.get('calibration')}")
    print()

    print("Examples:")
    print("  python scripts/get_sensor_readings.py COM3 1 0x40 ping")
    print("  python scripts/get_sensor_readings.py COM3 1 0x40 read")
    print("  python scripts/get_sensor_readings.py COM3 1 0x40 add ina219")
    print("  python scripts/get_sensor_readings.py COM3 1 0x40 period 500")
    print("  python scripts/get_sensor_readings.py COM3 1 0x40 gain 2")
    sys.exit(1)

# ———————————————————————————————————————————————————————————————————————————
#  “--info” handler
if len(sys.argv) == 2 and sys.argv[1] in ("--info", "-i"):
    print_usage_and_exit()

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

# Constants
SOF_MARKER      = proto["constants"]["SOF_MARKER"]
TICK_BYTES      = proto["constants"]["TICK_BYTES"]
QUEUE_DEPTH     = proto["constants"]["QUEUE_DEPTH"]
CHECKSUM_LENGTH = proto["constants"]["CHECKSUM_LENGTH"]


# Commands
CMD_READ_SAMPLES = proto["commands"]["CMD_READ_SAMPLES"]
CMD_ADD_SENSOR   = proto["commands"]["CMD_ADD_SENSOR"]
CMD_REMOVE_SENSOR= proto["commands"]["CMD_REMOVE_SENSOR"]
CMD_SET_PERIOD = proto["commands"]["CMD_SET_PERIOD"]
CMD_SET_GAIN   = proto["commands"]["CMD_SET_GAIN"]
CMD_SET_RANGE  = proto["commands"]["CMD_SET_RANGE"]
CMD_SET_CAL    = proto["commands"]["CMD_SET_CAL"]
CMD_PING         = proto["commands"]["CMD_PING"]

# Status codes
STATUS_OK       = proto["status_codes"]["STATUS_OK"]
STATUS_ERROR    = proto["status_codes"]["STATUS_ERROR"]
STATUS_NOT_FOUND    = proto["status_codes"]["STATUS_NOT_FOUND"]
STATUS_UNKNOWN_CMD  = proto["status_codes"]["STATUS_UNKNOWN_CMD"]

# human-readable names for printing
STATUS_NAMES = {
    STATUS_OK:          "OK",
    STATUS_ERROR:       "ERROR",
    STATUS_NOT_FOUND:   "NOT_FOUND",
    STATUS_UNKNOWN_CMD: "UNKNOWN_CMD",
}

# sensor name → payload size
SENSOR_PAYLOAD_SIZES = {}
for fn in os.listdir(SENSORS_DIR):
    if not fn.endswith(".json"): continue
    meta = json.load(open(os.path.join(SENSORS_DIR, fn)))
    SENSOR_PAYLOAD_SIZES[meta["name"].lower()] = sum(f["size"] for f in meta["payload_fields"])

# sensor name → type code (for ADD)
SENSOR_TYPE_CODES = { name.lower(): code for name, code in proto["sensors"].items() }

# ————————————————————————————————————————————————————————————————————————————
def open_port(port="COM3", baud=115200, timeout=1):
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
def main():
    # Check command-line arguments
    if not (5 <= len(sys.argv) <= 6):
        print_usage_and_exit()

    port      = sys.argv[1]
    board_id  = int(sys.argv[2], 0)
    addr7     = parse_hex_arg(sys.argv[3])
    cmd_str   = sys.argv[4].lower()
    sensor_ty = sys.argv[5].lower() if len(sys.argv)==6 else "ina219"

    # decide which command and param
    if cmd_str == "add":
        cmd, param = CMD_ADD_SENSOR, SENSOR_TYPE_CODES[sensor_ty]
    elif cmd_str == "rmv":
        cmd, param = CMD_REMOVE_SENSOR, 0
    elif cmd_str == "period":
        cmd = CMD_SET_PERIOD
        raw_ms = int(sys.argv[5], 0)
        if raw_ms % 100 != 0:
            print("Error: period must be a multiple of 100 ms")
            sys.exit(1)
        param = raw_ms // 100
        cmd   = CMD_SET_PERIOD

    elif cmd_str == "gain":
        cmd = CMD_SET_GAIN
        param = int(sys.argv[5], 0)
    elif cmd_str == "range":
        cmd = CMD_SET_RANGE
        param = int(sys.argv[5], 0)
    elif cmd_str == "cal":
        cmd = CMD_SET_CAL
        param = int(sys.argv[5], 0)
    elif cmd_str == "ping":
        cmd, param = CMD_PING, 0

    else:  # default to read
        cmd, param = CMD_READ_SAMPLES, 0

    ser = open_port(port)
    time.sleep(0.1)

    print(f"{cmd_str.upper()} @0x{addr7:02X}, param={param}")
    send_command(ser, board_id, addr7, cmd, param)
    resp = recv_packet(ser)

    if cmd == CMD_READ_SAMPLES:
        if resp["status"] != STATUS_OK:
            name = STATUS_NAMES.get(resp["status"], str(resp["status"]))
            print(f"READ failed, status {name}")
            return
        size = SENSOR_PAYLOAD_SIZES.get(sensor_ty, next(iter(SENSOR_PAYLOAD_SIZES.values())))
        for i, (t, pl) in enumerate(parse_samples(resp, size)):
            voltage = (pl[0]<<8)|pl[1] if size>=2 else None
            current = struct.unpack(">i", pl[2:6])[0] if size>=6 else None
            print(f"Sample {i}: tick={t} ms, V={voltage} mV, I={current} µA")
    else:
        name = STATUS_NAMES.get(resp["status"], str(resp["status"]))
        print(f"{cmd_str.upper()} → status {name}")

if __name__ == "__main__":
    main()
