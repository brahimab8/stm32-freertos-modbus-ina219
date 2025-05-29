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
    m._send(1, 2, 3, 4)
    expected = bytearray([
        protocol.constants['SOF_MARKER'], 1, 2, 3, 4
    ])
    expected.append(1 ^ 2 ^ 3 ^ 4)
    assert m.ser._write_buffer == expected

    payload = b"\x10\x20"
    frame = make_packet(1, 2, 3, protocol.status_codes['STATUS_OK'], payload)
    m.ser.inject(frame)
    b, a, c, s, p = m._recv()
    assert (b, a, c, s, p) == (1, 2, 3, protocol.status_codes['STATUS_OK'], payload)


def test_recv_checksum_mismatch():
    m = core_mod.SensorMaster(port="COM2", baud=115200, timeout=0.1)
    payload = b"\x01"
    raw = bytearray(make_packet(1, 2, 3, protocol.status_codes['STATUS_OK'], payload))
    raw[-1] ^= 0xFF
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

    # stub _execute to return OK + our payload
    monkeypatch.setattr(
        m, "_execute",
        lambda bid, addr, cmd, param=0: (None, None, None,
                                        protocol.status_codes['STATUS_OK'],
                                        payload)
    )

    recs = m.read_samples(board_id=7, addr=0x40, sensor_name="foo")
    # should get a list of one dict
    assert recs == [{'tick': tick, 'foo': (0xAA << 8) | 0xBB}]


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
        lambda b, a, cmd, param=0: (None, None, None,
                                    protocol.status_codes['STATUS_UNKNOWN_CMD'],
                                    b'')
    )

    # new signature is ping(board_id)
    status = m.ping(5)
    assert status == protocol.status_codes['STATUS_UNKNOWN_CMD']
