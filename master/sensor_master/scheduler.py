import threading
import time
import sched

from .boards import BoardManager
from .sensors import registry

class StreamScheduler:
    """
    Periodically reads all sensors discovered on the bus.
    Scans with a short timeout, then streams with a longer one.
    """
    def __init__(self,
                 bm: BoardManager = None,
                 port: str = 'COM3',
                 baud: int = 115200,
                 timeout: float = 0.05):
        # allow injection of an existing manager, or build one for scanning
        if bm is not None:
            self._bm = bm
        else:
            self._bm = BoardManager(port, baud, timeout)

        self.timeout   = timeout

        self._running      = False
        self._stop         = threading.Event()
        self._thread       = None
        self.subscriptions = []  # list of (board, addr, name, interval)
        self.system_info   = {}  # { board_id: { 'sensors': [...] } }

    def setup_stream(self):
        """
        Scan the bus and populate:
          - self.system_info with metadata
          - self.subscriptions with all sensors & their default intervals
        """
        self._bm.timeout = self.timeout

        boards = self._bm.scan()
        self.system_info.clear()
        self.subscriptions.clear()

        for board_id in boards:
            bound = self._bm.select(board_id)
            sensors = []
            for name, hex_addr in bound.list_sensors():
                addr = int(hex_addr, 16)
                md   = registry.metadata(name)
                period_ms = md.get('default_period_ms') or 1000

                sensors.append({
                    'name': name,
                    'addr': addr,
                    'default_period_ms': period_ms,
                    'default_gain':     md.get('default_gain'),
                    'default_range':    md.get('default_range'),
                    'default_calib':    md.get('default_calib'),
                })

                # schedule this sensor at its default rate
                interval = period_ms / 1000.0
                self.subscriptions.append((board_id, addr, name, interval))

            self.system_info[board_id] = {'sensors': sensors}

        return self.system_info

    def clear_subscriptions(self):
        """Remove all pending subscriptions."""
        self.subscriptions.clear()

    def start(self, callback):
        """
        Begin streaming. callback(board, addr, name, records) is invoked
        periodically for each sensor. Raises if already running.
        """
        if self._running:
            raise RuntimeError("Already streaming")

        # if we haven't scanned yet, do so (and auto-subscribe)
        if not self.subscriptions:
            self.setup_stream()

        # switch to a longer timeout so reads can complete
        self._bm.timeout = self.timeout

        self._running = True
        self._stop.clear()

        def _loop():
            scheduler = sched.scheduler(time.time, time.sleep)

            def make_job(b, a, name, interval):
                def job():
                    if self._stop.is_set():
                        return
                    try:
                        recs = self._bm.select(b).read_samples(a, name)
                        callback(b, a, name, recs)
                    except Exception as e:
                        # never let one error kill the thread
                        print(f"[Stream error] board {b} sensor {name}@0x{a:02X}: {e}")
                    finally:
                        # re-schedule regardless of success/failure
                        scheduler.enter(interval, 1, job)
                return job

            # enqueue initial jobs
            for b, a, name, interval in self.subscriptions:
                scheduler.enter(0, 1, make_job(b, a, name, interval))

            # this will block until .stop() is called
            scheduler.run()

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the thread to exit, then wait for it to finish."""
        self._stop.set()
        if self._thread:
            self._thread.join()
        self._running = False
