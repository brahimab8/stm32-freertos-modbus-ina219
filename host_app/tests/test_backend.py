import pytest

import core.backend as backend_mod
from core.backend import SensorBackend, Mode


class DummyBound:
    def __init__(self, sensors=None, configs=None):
        """
        sensors: list of (name, hex_addr) tuples
        configs: dict mapping (addr, None) → config dict
        """
        self._sensors = sensors or []
        self._configs = configs or {}

    def list_sensors(self):
        return self._sensors
    
    def get_all_config_fields(self, addr, name):
        # Simulate config lookup
        return self._configs.get((addr, name), {})


class DummyStreamScheduler:
    def __init__(self, bm, timeout):
        self.bm = bm
        self.timeout = timeout
        self.subscriptions = []
        self.started = False
        self.stopped = False

    def start(self, callback):
        self.started = True
        # we won't actually spawn a thread

    def stop(self):
        self.stopped = True

    def clear_subscriptions(self):
        self.subscriptions.clear()


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    """
    Always replace the real BoardManager and StreamScheduler in SensorBackend
    with dummy implementations.
    """
    # Dummy BoardManager: we will override attributes per-test as needed
    class DummyBM:
        def __init__(self, port, baud, timeout):
            self.port = port
            self.baud = baud
            self.timeout = timeout

        def scan(self):
            return []  # default; override in tests

        def select(self, bid):
            return DummyBound()

        def list_sensors(self, board):
            return []  # unused here

    monkeypatch.setattr(backend_mod, "BoardManager", DummyBM)
    monkeypatch.setattr(backend_mod, "StreamScheduler", DummyStreamScheduler)
    yield


def test_get_sensor_config_defaults():
    sb = SensorBackend()
    bound = DummyBound(configs={})  # no fields
    cfg = sb._get_sensor_config(bound=bound, board=0, addr=0x10, name="foo")
    assert cfg == {}


def test_get_sensor_config_with_fields():
    sb = SensorBackend()
    config = {
        'period_ms': 1000,
        'gain': 5,
        'range': 8,
        'calib': 12,
        'unused': 999
    }

    bound = DummyBound(
        configs={ (0x20, "foo"): config }
    )

    cfg = sb._get_sensor_config(bound=bound, board=7, addr=0x20, name="foo")
    assert cfg == config


    class DummySM:
        def _execute(self, board, addr, cmd, zero):
            # Return status OK and payload based on cmd_map
            val = cmd_map.get(cmd, 0)
            # Use 2 bytes little-endian for all values
            payload = val.to_bytes(2, 'little')
            return (None, None, None, 0, payload)

    bound = DummyBound(
        sensors=[],
        configs={}
    )
    # Attach a fake state machine to bound
    bound._sm = DummySM()

    # Call _get_sensor_config with our dummy bound and a dummy board ID (e.g., 7)
    cfg = sb._get_sensor_config(bound=bound, board=7, addr=0x20, name="foo")
    # Should collect values for the four known fields and 'unused'
    assert cfg == {
        'period_ms': 1000,
        'gain': 5,
        'range': 8,
        'calib': 12,
        'unused': 999
    }


def test_do_discovery(monkeypatch):
    sb = SensorBackend(port="COMZ", baud=789, timeout=0.3)
    # Stub board_mgr.scan to return boards [7]
    monkeypatch.setattr(sb.board_mgr, "scan", lambda: [7])
    # Stub select(7) to return a DummyBound with one sensor
    sensors = [("foo", "0x10")]
    configs = { (0x10, None): {'period_ms': 200, 'gain':1, 'range':2, 'calib':3 }}
    bound = DummyBound(sensors=sensors, configs=configs)
    monkeypatch.setattr(sb.board_mgr, "select", lambda bid: bound)

    result = sb._do_discovery()
    # Expect one board entry mapping to a list with one sensor dict
    assert set(result.keys()) == {7}
    info = result[7]
    assert isinstance(info, list) and len(info) == 1
    entry = info[0]
    # Since there are no config_fields, config should be empty
    assert entry == {
        'name': 'foo',
        'addr': 0x10,
        'config': {}
    }


def test_set_mode_transitions(monkeypatch):
    sb = SensorBackend()

    # Stub _do_discovery to return a known dict
    monkeypatch.setattr(sb, "_do_discovery", lambda: {'x': []})

    # Initially in IDLE. Switching to IDLE again → no-op (None)
    assert sb.mode == Mode.IDLE
    assert sb.set_mode(Mode.IDLE) is None

    # Switch to DISCOVERY → returns discovery info, mode changes
    disc = sb.set_mode(Mode.DISCOVERY)
    assert disc == {'x': []}
    assert sb.mode == Mode.DISCOVERY

    # Calling DISCOVERY again re-runs and returns same stub
    disc2 = sb.set_mode(Mode.DISCOVERY)
    assert disc2 == {'x': []}
    assert sb.mode == Mode.DISCOVERY

    # Switch to STREAM: should stop any existing stream (none), mode changes
    assert sb.set_mode(Mode.STREAM) is None
    assert sb.mode == Mode.STREAM

    # Stub stream_scheduler.stop to record calls
    sb.stream_scheduler.stopped = False
    sb.set_mode(Mode.IDLE)
    assert sb.stream_scheduler.stopped
    assert sb.mode == Mode.IDLE


def test_start_and_stop_stream(monkeypatch):
    sb = SensorBackend()
    # Prepare _do_discovery to return one board with two sensors; now using 'period' (in 100ms units)
    discovery_map = {
        5: [
            {'name': 's1', 'addr': 0x10, 'config': {'period': 3, 'gain':0, 'range':0, 'calib':0}},
            {'name': 's2', 'addr': 0x20, 'config': {'period': 7, 'gain':0, 'range':0, 'calib':0}}
        ]
    }
    monkeypatch.setattr(sb, "_do_discovery", lambda: discovery_map)

    # Ensure stream_scheduler starts with empty subscriptions
    assert sb.stream_scheduler.subscriptions == []
    sb.start_stream(callback=lambda *args: None)

    # After starting: mode == STREAM, subscriptions populated, scheduler started
    assert sb.mode == Mode.STREAM
    subs = sb.stream_scheduler.subscriptions
    # Two sensors → two entries: (board, addr, name, interval)
    assert len(subs) == 2
    assert (5, 0x10, 's1', 3 * 0.1) in subs
    assert (5, 0x20, 's2', 7 * 0.1) in subs
    assert sb.stream_scheduler.started

    # Calling start_stream again (already STREAM) should do nothing
    sb.stream_scheduler.started = False
    prev_subs = list(sb.stream_scheduler.subscriptions)
    sb.start_stream(callback=lambda *args: None)
    assert sb.stream_scheduler.started is False
    assert sb.stream_scheduler.subscriptions == prev_subs

    # Now test stop_stream: mode must revert to IDLE and stop() called
    sb.stream_scheduler.stopped = False
    sb.stop_stream()
    assert sb.mode == Mode.IDLE
    assert sb.stream_scheduler.stopped

    # Calling stop_stream when not STREAM does nothing
    sb.stream_scheduler.stopped = False
    sb.stop_stream()
    assert sb.stream_scheduler.stopped is False


def test_facade_methods(monkeypatch):
    sb = SensorBackend()

    # Replace board_mgr with an object whose methods return sentinel values
    class FakeBM2:
        def scan(self):
            return [9]

        def list_sensors(self, board):
            return [('foo', '0x10')]

        def select(self, board):
            # Return an object whose _sm is itself, and which implements the needed methods
            class B:
                def __init__(self):
                    self._sm = self

                def add_sensor(self, addr, name):
                    return 'add_ok'

                def remove_sensor(self, addr):
                    return 'remove_ok'

                def set_payload_mask(self, addr, mask):
                    return 'mask_set'

                def get_payload_mask(self, addr):
                    return 0xFF

                def read_samples(self, board, addr, sensor, mask_val):
                    return [{'dummy': 1}]

            return B()

    sb.board_mgr = FakeBM2()

    # scan_boards
    assert sb.scan_boards() == [9]
    # list_sensors façade
    assert sb.list_sensors(9) == [('foo', '0x10')]
    # add/remove sensor façades
    assert sb.add_sensor(9, 0x10, 'foo') == 'add_ok'
    assert sb.remove_sensor(9, 0x10) == 'remove_ok'
    # read_samples façade (uses get_payload_mask and read_samples in _sm)
    assert sb.read_samples(9, 0x10, 'foo') == [{'dummy': 1}]
    # payload-mask façades
    assert sb.set_payload_mask(9, 0x10, 0xAA) == 'mask_set'
    assert sb.get_payload_mask(9, 0x10) == 0xFF
