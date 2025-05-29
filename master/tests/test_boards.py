import pytest
from sensor_master.boards import BoardManager
from sensor_master.protocol import protocol

class FakeSM:
    def __init__(self):
        self.calls = []

    def _execute(self, board_id, addr, cmd, param):
        self.calls.append((board_id, addr, cmd, param))
        if board_id % 2 == 0:
            status = protocol.status_codes['STATUS_OK']
        elif board_id == 3:
            status = protocol.status_codes['STATUS_NOT_FOUND']
        else:
            raise IOError()
        return (None, None, None, status, b'')

    def ping(self, board_id, addr=0x00):
        _, _, _, status, _ = self._execute(
            board_id, addr, protocol.commands['CMD_PING'], 0
        )
        return status

    # mirror SensorMaster high-level API
    def add_sensor(self, board_id, addr, sensor_name):
        return self._execute(board_id, addr, protocol.commands['CMD_ADD_SENSOR'], 0)

    def read_samples(self, board_id, addr, sensor_name):
        return self._execute(board_id, addr, protocol.commands['CMD_READ_SAMPLES'], 0)

    def remove_sensor(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_REMOVE_SENSOR'], 0)

    def set_period(self, board_id, addr, ms):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_PERIOD'], ms)

    def set_gain(self, board_id, addr, code):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_GAIN'], code)

    def set_range(self, board_id, addr, code):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_RANGE'], code)

    def set_cal(self, board_id, addr, code):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_CAL'], code)

@pytest.fixture(autouse=True)
def patch_sm(monkeypatch):
    fake = FakeSM()
    monkeypatch.setattr(
        'sensor_master.boards.SensorMaster',
        lambda *args, **kw: fake
    )
    return fake

def test_manager_ping_forwards_to_execute():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm

    # successful ping
    status = mgr.ping(2)
    assert status == protocol.status_codes['STATUS_OK']
    assert fake.calls[0] == (2, 0x00, protocol.commands['CMD_PING'], 0)

    # failed ping raises
    with pytest.raises(IOError):
        mgr.ping(1)
    assert fake.calls[1] == (1, 0x00, protocol.commands['CMD_PING'], 0)

def test_boundmaster_ping_forwards():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm
    bm = mgr.select(4)

    status = bm.ping()
    assert status == protocol.status_codes['STATUS_OK']
    bid, addr, cmd, param = fake.calls[-1]
    assert bid == 4
    assert cmd == protocol.commands['CMD_PING']
    assert addr == 0x00 and param == 0

def test_scan_detects_ok_and_not_found():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm

    found = mgr.scan(start=1, end=5)
    assert found == [2, 3, 4]
    assert [c[0] for c in fake.calls] == [1, 2, 3, 4, 5]

def test_boundmaster_forwards_all_methods():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm
    bm = mgr.select(8)

    bm.add_sensor(0x10, 'foo')
    bm.read_samples(0x11, 'bar')
    bm.remove_sensor(0x12)
    bm.set_period(0x13, 500)
    bm.set_gain(0x14, 3)
    bm.set_range(0x15, 7)
    bm.set_cal(0x16, 42)

    assert len(fake.calls) == 7
    assert all(call[0] == 8 for call in fake.calls)
    seen_cmds = {c[2] for c in fake.calls}
    expected = {
        protocol.commands['CMD_ADD_SENSOR'],
        protocol.commands['CMD_READ_SAMPLES'],
        protocol.commands['CMD_REMOVE_SENSOR'],
        protocol.commands['CMD_SET_PERIOD'],
        protocol.commands['CMD_SET_GAIN'],
        protocol.commands['CMD_SET_RANGE'],
        protocol.commands['CMD_SET_CAL'],
    }
    assert seen_cmds == expected
