import threading
import pytest
import time

import sensor_master.scheduler as scheduler_mod
from sensor_master.scheduler import StreamScheduler
from sensor_master.boards import BoardManager
from sensor_master.sensors import registry as sensor_registry


class DummyBound:
    def __init__(self, sensors=None, samples=None):
        """
        sensors: list of (name, hex_addr) tuples
        samples: dict mapping (addr, name) → list of sample dicts
        """
        self._sensors = sensors or []
        self._samples = samples or {}

    def list_sensors(self):
        return self._sensors

    def read_samples(self, addr, name, mask_val=None):
        # Return the list of samples for that (addr, name), or empty list
        return self._samples.get((addr, name), [])


class DummyBM:
    def __init__(self, boards=None, bound_map=None):
        """
        boards: list of board IDs to return on scan()
        bound_map: dict mapping board_id → DummyBound instance
        """
        self._boards = boards or []
        self._bound_map = bound_map or {}

    def scan(self):
        return list(self._boards)

    def select(self, board_id):
        return self._bound_map.get(board_id, DummyBound())

    @property
    def timeout(self):
        return None

    @timeout.setter
    def timeout(self, t):
        pass


class FakeScheduler:
    """
    A fake replacement for sched.scheduler that runs each job exactly once.
    Any rescheduled jobs are collected but not rerun in the same cycle.
    """
    def __init__(self, timefunc, sleepfunc):
        self.jobs = []

    def enter(self, delay, priority, action):
        # Queue the action, but do not execute immediately
        self.jobs.append(action)

    def run(self):
        # Execute all queued jobs once
        current_jobs = list(self.jobs)
        self.jobs.clear()
        for job in current_jobs:
            job()


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    """
    - Replace BoardManager in StreamScheduler with a dummy
    - Replace registry.metadata to return a fixed metadata dict
    - Replace sched.scheduler with FakeScheduler
    """
    # Patch sched.scheduler
    monkeypatch.setattr(
        scheduler_mod.sched, "scheduler",
        lambda timefunc, sleepfunc: FakeScheduler(timefunc, sleepfunc)
    )

    # Provide a dummy registry.metadata that returns default_period_ms, default_gain, default_range, default_calib
    dummy_meta = {
        "payload_fields": [{"name": "f1", "size": 2}, {"name": "f2", "size": 1}],
        "default_period_ms": 250,
        "default_gain": 5,
        "default_range": 3,
        "default_calib": 7,
    }
    monkeypatch.setattr(sensor_registry, "metadata", lambda name: dummy_meta)

    yield


def test_setup_stream_populates_system_info_and_subscriptions(monkeypatch):
    # Create DummyBM that reports one board (42) with two sensors
    sensors = [("sensorA", "0x10"), ("sensorB", "0x20")]
    dummy_bound = DummyBound(sensors=sensors)
    dummy_bm = DummyBM(boards=[42], bound_map={42: dummy_bound})

    # Instantiate StreamScheduler with our DummyBM
    ss = StreamScheduler(bm=dummy_bm, timeout=0.1)

    info = ss.setup_stream()

    # system_info should have key 42 with two sensor entries
    assert 42 in info
    board_info = info[42]
    assert "sensors" in board_info
    assert isinstance(board_info["sensors"], list)
    assert len(board_info["sensors"]) == 2

    # Each sensor dict should contain expected fields
    entryA = next(s for s in board_info["sensors"] if s["name"] == "sensorA")
    assert entryA["addr"] == 0x10
    assert entryA["default_period_ms"] == 250
    assert entryA["default_gain"] == 5
    assert entryA["default_range"] == 3
    assert entryA["default_calib"] == 7

    # subscriptions should include two entries: (board, addr, name, interval)
    subs = ss.subscriptions
    assert len(subs) == 2
    assert (42, 0x10, "sensorA", 250 / 1000.0) in subs
    assert (42, 0x20, "sensorB", 250 / 1000.0) in subs


def test_start_runs_callbacks_and_stop_stops(monkeypatch):
    # Create DummyBM that reports one board (7) with one sensor and one sample
    sensors = [("temp", "0x30")]
    samples = {(0x30, "temp"): [{"value": 123}]}
    dummy_bound = DummyBound(sensors=sensors, samples=samples)
    dummy_bm = DummyBM(boards=[7], bound_map={7: dummy_bound})

    ss = StreamScheduler(bm=dummy_bm, timeout=0.05)
    # Manually populate subscriptions for one sensor with a small interval
    ss.subscriptions = [(7, 0x30, "temp", 0.01)]

    # Collect callback invocations
    callback_calls = []

    def callback(board_id, addr, name, records):
        callback_calls.append((board_id, addr, name, records))

    # Start streaming (FakeScheduler will run jobs exactly once)
    ss.start(callback)
    # Allow a brief moment for the thread to start
    time.sleep(0.01)
    # Stop should join the thread and set _running = False
    ss.stop()

    # Ensure that callback was called at least once with expected args
    assert callback_calls, "Callback was never invoked"
    # Expect the first call to be (7, 0x30, "temp", samples_list)
    assert callback_calls[0] == (7, 0x30, "temp", [{"value": 123}])
    # After stop, _running must be False
    assert not ss._running

    # Calling start again after stop should work (no exception) and invoke callback again
    callback_calls.clear()
    ss.start(callback)
    time.sleep(0.01)
    ss.stop()
    assert callback_calls, "Callback was never invoked on second start"


def test_start_raises_if_already_running():
    ss = StreamScheduler(bm=DummyBM(), timeout=0.1)
    ss._running = True
    with pytest.raises(RuntimeError):
        ss.start(lambda *args: None)
