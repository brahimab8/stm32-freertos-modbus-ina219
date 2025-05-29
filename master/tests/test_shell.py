import pytest
from sensor_master.protocol import protocol
from sensor_master.cli.shell import SensorShell
from sensor_master.core import serial as sm_serial

# DummySerial to prevent actual COM-port access
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
        return self
    def add_sensor(self, addr, name):
        self.calls.append(('add', addr, name))
        return protocol.status_codes['STATUS_OK']
    def ping(self, bid):
        self.calls.append(('ping', bid))
        return protocol.status_codes['STATUS_OK']

@pytest.fixture(autouse=True)
def patch_serial(monkeypatch):
    # Prevent real serial.Serial from opening ports
    monkeypatch.setattr(sm_serial, 'Serial', DummySerial)
    yield

@pytest.fixture
def shell(monkeypatch):
    dummy = DummyMgr()
    monkeypatch.setattr(
        'sensor_master.cli.shell.BoardManager',
        lambda port, baud: dummy
    )
    return SensorShell('P', 1)

def test_scan_command(shell, capsys):
    shell.onecmd('scan')
    out = capsys.readouterr().out
    assert 'Boards found: 1, 2, 3' in out
    assert ('scan',) in shell.manager.calls

def test_ping_command(shell, capsys):
    shell.current_board = 5
    shell.onecmd('ping')
    out = capsys.readouterr().out
    assert 'PING → STATUS_OK' in out
    assert ('ping', 5) in shell.manager.calls
