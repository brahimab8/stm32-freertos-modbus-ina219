import pytest
from sensor_master.boards import BoardManager
from sensor_master.protocol import protocol


class FakeSM:
    def __init__(self):
        self.calls = []

    def _execute(self, board_id, addr, cmd, param):
        """
        Append a record of (board_id, addr, cmd, param) to self.calls.
        Return a tuple in the format (None, None, None, status, b'') 
        (so as to mimic the low‐level protocol interface).
        For scan/ping: even board_id → STATUS_OK, board_id == 3 → STATUS_NOT_FOUND, else IOError.
        """
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

    def scan(self, start, end):
        """
        Emulate BoardManager.scan(...) by calling ping(...) for each board_id.
        If ping(...) returns either STATUS_OK or STATUS_NOT_FOUND, include that board_id in the returned list.
        If ping(...) raises IOError, skip that board_id.
        """
        found = []
        for bid in range(start, end + 1):
            try:
                st = self.ping(bid)
            except IOError:
                continue
            # include both OK and NOT_FOUND as "detected"
            if st in (
                protocol.status_codes['STATUS_OK'],
                protocol.status_codes['STATUS_NOT_FOUND']
            ):
                found.append(bid)
        return found

    # mirror SensorMaster high-level API
    def add_sensor(self, board_id, addr, sensor_name):
        return self._execute(board_id, addr, protocol.commands['CMD_ADD_SENSOR'], 0)

    def read_samples(self, board_id, addr, sensor_name):
        return self._execute(board_id, addr, protocol.commands['CMD_READ_SAMPLES'], 0)

    def remove_sensor(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_REMOVE_SENSOR'], 0)

    def list_sensors(self, board_id):
        return self._execute(board_id, 0x00, protocol.commands['CMD_LIST_SENSORS'], 0)

    def set_period(self, board_id, addr, ms):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_PERIOD'], ms)

    def set_gain(self, board_id, addr, code):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_GAIN'], code)

    def set_range(self, board_id, addr, code):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_RANGE'], code)

    def set_cal(self, board_id, addr, code):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_CAL'], code)

    def get_period(self, board_id, addr):
        # For simplicity, route through the same _execute pattern
        return self._execute(board_id, addr, protocol.commands['CMD_GET_PERIOD'], 0)

    def get_gain(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_GET_GAIN'], 0)

    def get_range(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_GET_RANGE'], 0)

    def get_cal(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_GET_CAL'], 0)

    def get_config(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_GET_CONFIG'], 0)

    def set_payload_mask(self, board_id, addr, mask):
        return self._execute(board_id, addr, protocol.commands['CMD_SET_PAYLOAD_MASK'], mask)

    def get_payload_mask(self, board_id, addr):
        return self._execute(board_id, addr, protocol.commands['CMD_GET_PAYLOAD_MASK'], 0)


@pytest.fixture(autouse=True)
def patch_sm(monkeypatch):
    """
    Monkeypatch SensorMaster so that BoardManager(...) → FakeSM() underneath.
    We patch 'sensor_master.boards.SensorMaster' because BoardManager does:
        from .core import SensorMaster
    in sensor_master/boards.py.
    """
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
    # The last call should have board_id=4, CMD_PING, addr=0x00, param=0
    bid, addr, cmd, param = fake.calls[-1]
    assert bid == 4
    assert cmd == protocol.commands['CMD_PING']
    assert addr == 0x00 and param == 0


def test_scan_detects_ok_and_not_found():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm

    found = mgr.scan(start=1, end=5)
    # For board_id = 2,4 → STATUS_OK; board_id = 3 → STATUS_NOT_FOUND; 1 and 5 → IOError
    assert found == [2, 3, 4]
    # Confirm that FakeSM.ping was invoked for 1..5
    assert [c[0] for c in fake.calls] == [1, 2, 3, 4, 5]


def test_boundmaster_forwards_all_methods():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm
    bm = mgr.select(8)

    # Call each high‐level method on _BoundMaster
    bm.add_sensor(0x10, 'foo')
    bm.read_samples(0x11, 'bar')
    bm.remove_sensor(0x12)
    bm.set_config(0x13, 'CMD_SET_PERIOD', 500)
    bm.set_config(0x14, 'CMD_SET_GAIN', 3)
    bm.set_config(0x15, 'CMD_SET_RANGE', 7)
    bm.set_config(0x16, 'CMD_SET_CAL', 42)

    # We should have exactly 7 calls in FakeSM.calls
    assert len(fake.calls) == 7
    # Every call's first element must be the bound board_id=8
    assert all(call[0] == 8 for call in fake.calls)
    # Collect the set of forwarded command IDs
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


def test_boundmaster_forwards_new_getters_and_payload_mask_methods():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm
    bm = mgr.select(8)

    # Invoke each of the newly‐added methods on _BoundMaster:
    bm.get_config(0x20, 'CMD_GET_PERIOD')
    bm.get_config(0x21, 'CMD_GET_GAIN')
    bm.get_config(0x22, 'CMD_GET_RANGE')
    bm.get_config(0x23, 'CMD_GET_CAL')
    bm.get_config(0x24, 'CMD_GET_CONFIG')
    bm.set_payload_mask(0x25, 0x0F)
    bm.get_payload_mask(0x26)

    # That should be 7 new calls
    assert len(fake.calls) == 7
    # Every call uses board_id = 8
    assert all(call[0] == 8 for call in fake.calls)

    seen_cmds = {c[2] for c in fake.calls}
    expected_commands = {
        protocol.commands['CMD_GET_PERIOD'],
        protocol.commands['CMD_GET_GAIN'],
        protocol.commands['CMD_GET_RANGE'],
        protocol.commands['CMD_GET_CAL'],
        protocol.commands['CMD_GET_CONFIG'],
        protocol.commands['CMD_SET_PAYLOAD_MASK'],
        protocol.commands['CMD_GET_PAYLOAD_MASK'],
    }
    assert seen_cmds == expected_commands


def test_boardmanager_list_sensors_forwards():
    mgr = BoardManager(port="X", baud=1, timeout=1)
    fake = mgr._sm

    # simulate a successful list_sensors call
    result = mgr.list_sensors(6)
    # FakeSM.list_sensors returns a 5‐tuple (None, None, None, status, b'')
    assert result == (None, None, None, protocol.status_codes['STATUS_OK'], b'')
    assert fake.calls[-1] == (6, 0x00, protocol.commands['CMD_LIST_SENSORS'], 0)
