import pytest
from core.protocol import protocol
from cli.shell import SensorShell
from core.backend import SensorBackend

# DummySerial to prevent actual COM-port access in SensorBackend
class DummySerial:
    def __init__(self, port, baud, timeout=None):
        self.port = port
        self.baudrate = baud
        self.timeout = timeout
        self._write_buf = bytearray()
        self._read_buf = bytearray()
    def write(self, data):
        self._write_buf += data
    def read(self, n):
        if not self._read_buf:
            return b''
        data, self._read_buf = self._read_buf[:n], self._read_buf[n:]
        return data
    def inject(self, data: bytes):
        self._read_buf += data

# Dummy manager to intercept calls
class DummyMgr:
    def __init__(self):
        self.calls = []
        self.port = "P"
        self.baud = 1
    def scan(self):
        self.calls.append(('scan',))
        return [1,2,3]
    def select(self, bid):
        self.calls.append(('select', bid))
        # Return a bound object that has list_sensors, add_sensor, and ping
        class Bound:
            def list_sensors(self_inner):
                return []  # no sensors

            def add_sensor(self_inner, addr, name):
                return protocol.status_codes['STATUS_OK']

            def ping(self_inner):
                return protocol.status_codes['STATUS_OK']
        return Bound()

    def add_sensor(self, addr, name):
        self.calls.append(('add', addr, name))
        return protocol.status_codes['STATUS_OK']
    def ping(self, bid):
        self.calls.append(('ping', bid))
        return protocol.status_codes['STATUS_OK']

@pytest.fixture(autouse=True)
def patch_serial(monkeypatch):
    import core.core as core_mod
    monkeypatch.setattr(core_mod.serial, 'Serial', DummySerial)
    yield

@pytest.fixture
def shell(monkeypatch):
    dummy_mgr = DummyMgr()
    fake_backend = SensorBackend(port="X", baud=1, timeout=0.1)
    fake_backend.board_mgr = dummy_mgr
    return SensorShell(fake_backend)

def test_scan_command(shell, capsys):
    shell.onecmd('scan')
    out = capsys.readouterr().out

    expected = (
        "Board 1: <no sensors>\n"
        "Board 2: <no sensors>\n"
        "Board 3: <no sensors>\n"
    )
    assert out == expected

    assert ('scan',) in shell.backend.board_mgr.calls

def test_add_command(shell, capsys):
    shell.current_board = 5
    shell.current_sensor = 'foo'
    shell.current_addr = 0x10

    shell.onecmd('add')
    out = capsys.readouterr().out.strip()
    assert out == "ADD → STATUS_OK"
    calls = shell.backend.board_mgr.calls
    assert ('select', 5) in calls

def test_ping_command(shell, capsys):
    shell.current_board = 4
    shell.onecmd('ping')
    out = capsys.readouterr().out.strip()
    assert out == "PING → STATUS_OK"
    calls = shell.backend.board_mgr.calls
    assert ('ping', 4) in calls
