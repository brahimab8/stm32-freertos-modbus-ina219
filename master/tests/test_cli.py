import pytest
from click.testing import CliRunner
from sensor_master.protocol import protocol
from sensor_master.cli.click import cli 

class DummyMgr:
    def select(self, board_id):
        return self
    def add_sensor(self, addr, sensor):
        return protocol.status_codes['STATUS_OK']
    def ping(self, board_id):
        return protocol.status_codes['STATUS_NOT_FOUND']

@pytest.fixture(autouse=True)
def patch_mgr(monkeypatch):
    # Patch BoardManager in the click module to use our DummyMgr
    monkeypatch.setattr(
        "sensor_master.cli.click.BoardManager",
        lambda port, baud: DummyMgr()
    )

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
