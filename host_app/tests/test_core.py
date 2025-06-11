import struct
import pytest
import sensor_master.core as core_mod
from sensor_master.protocol import protocol
from sensor_master.sensors import registry

# DummySerial to intercept reads/writes
class DummySerial:
    def __init__(self, port, baud, timeout):
        self.port = port
        self.baudrate = baud
        self.timeout = timeout
        self._write_buffer = bytearray()
        self._read_buffer = bytearray()

    def write(self, data):
        self._write_buffer += data

    def read(self, n):
        if not self._read_buffer:
            return b''
        data = self._read_buffer[:n]
        self._read_buffer = self._read_buffer[n:]
        return data

    def inject(self, data: bytes):
        self._read_buffer += data

@pytest.fixture(autouse=True)
def patch_serial(monkeypatch):
    import serial
    monkeypatch.setattr(serial, "Serial", DummySerial)
    yield

# helper to build a framed packet
def make_packet(board, addr, cmd, status, payload):
    sof = protocol.constants['SOF_MARKER']
    hdr = bytes([board, addr, cmd, status, len(payload)])
    chk = 0
    for b in hdr + payload:
        chk ^= b
    return bytes([sof]) + hdr + payload + bytes([chk])

# — tests — 

def test_send_and_recv_frame_ok():
    m = core_mod.SensorMaster(port="COM1", baud=9600, timeout=0.1)
    # When we _send(1, 2, 3, 4), we expect:
    # [ SOF, board=1, addr=2, cmd=3, param=4, checksum=(1^2^3^4) ] written to serial.
    m._send(1, 2, 3, 4)
    expected = bytearray([
        protocol.constants['SOF_MARKER'], 1, 2, 3, 4
    ])
    expected.append(1 ^ 2 ^ 3 ^ 4)
    assert m.ser._write_buffer == expected

    # Now inject a well-formed response frame and verify _recv().
    payload = b"\x10\x20"
    frame = make_packet(
        board=1,
        addr=2,
        cmd=3,
        status=protocol.status_codes['STATUS_OK'],
        payload=payload
    )
    m.ser.inject(frame)
    b, a, c, s, p = m._recv()
    assert (b, a, c, s, p) == (
        1,
        2,
        3,
        protocol.status_codes['STATUS_OK'],
        payload
    )


def test_recv_checksum_mismatch():
    m = core_mod.SensorMaster(port="COM2", baud=115200, timeout=0.1)
    # Build a valid payload, then flip the last checksum byte so that _recv() fails.
    payload = b"\x01"
    raw = bytearray(make_packet(
        board=1,
        addr=2,
        cmd=3,
        status=protocol.status_codes['STATUS_OK'],
        payload=payload
    ))
    raw[-1] ^= 0xFF  # Corrupt checksum
    m.ser.inject(raw)
    with pytest.raises(ValueError):
        m._recv()


def test_read_samples_parsing(monkeypatch):
    m = core_mod.SensorMaster(port="X", baud=1, timeout=0.1)
    tick = 5
    # build payload = 4-byte tick + 2-byte data
    payload = struct.pack(">I", tick) + b"\xAA\xBB"

    # stub out registry.metadata to match a 2-byte uint field named 'foo'
    monkeypatch.setattr(registry, "metadata", lambda name: {
        'payload_fields': [
            {'name': 'foo', 'type': 'uint16', 'size': 2}
        ]
    })

    # Stub registry.parse_payload(...) so that it only unpacks a record when chunk is long enough:
    def fake_parse_payload(sensor_name, chunk, mask):
        # We expect at least 4 bytes of tick + 2 bytes of foo = 6 total.
        if len(chunk) < 6:
            return {}  # “not a full record” → stop parsing
        t = struct.unpack(">I", chunk[:4])[0]
        f = struct.unpack(">H", chunk[4:6])[0]
        return {'tick': t, 'foo': f}

    monkeypatch.setattr(registry, "parse_payload", fake_parse_payload)

    # Stub _execute(...) so that read_samples(...) sees STATUS_OK + our payload:
    monkeypatch.setattr(
        m, "_execute",
        lambda bid, addr, cmd, param=0: (
            None, None, None,
            protocol.status_codes['STATUS_OK'],
            payload
        )
    )

    recs = m.read_samples(board_id=7, addr=0x40, sensor_name="foo")
    # Expect exactly one record: tick=5, foo=0xAABB
    assert recs == [{'tick': tick, 'foo': 0xAABB}]


def test_property_setters_reopen_and_update(monkeypatch):
    calls = []
    class CountSerial(DummySerial):
        def __init__(self, port, baud, timeout):
            calls.append((port, baud, timeout))
            super().__init__(port, baud, timeout)

    monkeypatch.setattr(core_mod, "serial", type("S", (), {"Serial": CountSerial}))

    m = core_mod.SensorMaster(port="P1", baud=100, timeout=0.5)
    # __init__ opened once
    assert calls == [("P1", 100, 0.5)]

    # port setter reopens
    m.port = "P2"
    assert calls[-1] == ("P2", 100, 0.5)

    # baudrate setter updates existing ser
    m.baudrate = 200
    assert m.ser.baudrate == 200

    # timeout setter updates existing ser
    m.timeout = 0.9
    assert m.ser.timeout == 0.9


def test_ping_returns_status(monkeypatch):
    m = core_mod.SensorMaster(port="P3", baud=200, timeout=0.2)

    # stub _execute to simulate ping returning UNKNOWN_CMD
    monkeypatch.setattr(
        m, "_execute",
        lambda b, a, cmd, param=0: (
            None, None, None,
            protocol.status_codes['STATUS_UNKNOWN_CMD'],
            b''
        )
    )

    status = m.ping(5)
    assert status == protocol.status_codes['STATUS_UNKNOWN_CMD']

def test_list_sensors(monkeypatch):
    m = core_mod.SensorMaster(port="P4", baud=9600, timeout=0.1)

    # Simulate payload of interleaved type_code and addr bytes
    payload = bytes([0x01, 0x10, 0x02, 0x20, 0x03, 0x30])  # (type_code, addr) pairs

    # Stub _execute(...) so that list_sensors(...) sees STATUS_OK + our payload
    monkeypatch.setattr(
        m, "_execute",
        lambda board_id, addr, cmd, param=0: (
            board_id, addr, cmd,
            protocol.status_codes['STATUS_OK'],
            payload
        )
    )

    # Stub registry.name_from_type(...) to map type_code → sensor_name
    monkeypatch.setattr(
        core_mod.registry, "name_from_type",
        lambda t: {
            0x01: "ina219",
            0x02: "bme280",
            0x03: "tmp102"
        }[t]
    )

    result = m.list_sensors(board_id=1)

    # Expect names and hex addresses
    expected = [
        ("ina219", "0x10"),
        ("bme280", "0x20"),
        ("tmp102", "0x30")
    ]

    assert result == expected
