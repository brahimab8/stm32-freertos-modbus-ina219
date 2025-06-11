import pytest
from click.testing import CliRunner
from core.protocol import protocol
from cli.click import cli 
import core.core as core_mod

class DummySerial:
    def __init__(self, port, baud, timeout=None):
        pass
    def write(self, data):
        pass
    def read(self, n):
        return b''

@pytest.fixture(autouse=True)
def patch_serial(monkeypatch):
    # Prevent real Serial port from opening in SensorBackend.__init__
    monkeypatch.setattr(core_mod.serial, 'Serial', DummySerial)
    yield

@pytest.fixture(autouse=True)
def patch_backend(monkeypatch):
    # Stub out add_sensor and ping on SensorBackend so CLI won't try real hardware
    monkeypatch.setattr(
        'core.backend.SensorBackend.add_sensor',
        lambda self, board, addr, sensor: protocol.status_codes['STATUS_OK']
    )
    monkeypatch.setattr(
        'core.backend.SensorBackend.ping',
        lambda self, board: protocol.status_codes['STATUS_NOT_FOUND']
    )
    yield

def test_cli_add():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["add", "--board", "1", "--addr", "0x20", "--sensor", "ina219"]
    )
    assert result.exit_code == 0
    assert "ADD → STATUS_OK" in result.output

def test_cli_ping():
    runner = CliRunner()
    result = runner.invoke(cli, ["ping", "--board", "3"])
    assert result.exit_code == 0
    assert "PING → STATUS_NOT_FOUND" in result.output
