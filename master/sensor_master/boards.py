from .core import SensorMaster
from .protocol import protocol

# Command & status constants
CMD_PING            = protocol.commands['CMD_PING']
CMD_READ_SAMPLES    = protocol.commands['CMD_READ_SAMPLES']
CMD_ADD_SENSOR      = protocol.commands['CMD_ADD_SENSOR']
CMD_REMOVE_SENSOR   = protocol.commands['CMD_REMOVE_SENSOR']
CMD_SET_PERIOD      = protocol.commands['CMD_SET_PERIOD']
CMD_SET_GAIN        = protocol.commands['CMD_SET_GAIN']
CMD_SET_RANGE       = protocol.commands['CMD_SET_RANGE']
CMD_SET_CAL         = protocol.commands['CMD_SET_CAL']

STATUS_OK           = protocol.status_codes['STATUS_OK']
STATUS_NOT_FOUND    = protocol.status_codes['STATUS_NOT_FOUND']


class BoardManager:
    """
    Manages an RS-485 bus with multiple boards.
    Allows scanning for live board IDs and returning
    a board-bound interface.
    """
    def __init__(self,
                 port: str = 'COM3',
                 baud: int = 115200,
                 timeout: float = 1.0):
        self._sm = SensorMaster(port, baud, timeout)

    @property
    def port(self) -> str:
        return self._sm.port

    @port.setter
    def port(self, p: str):
        self._sm.port = p

    @property
    def baud(self) -> int:
        return self._sm.baudrate

    @baud.setter
    def baud(self, b: int):
        self._sm.baudrate = b

    @property
    def timeout(self) -> float:
        return self._sm.timeout

    @timeout.setter
    def timeout(self, t: float):
        self._sm.timeout = t

    def scan(self, start: int = 1, end: int = 255):
        """
        Probe every board_id in [start..end].
        If it replies OK or NOT_FOUND, we assume it's present.
        """
        found = []
        for bid in range(start, end + 1):
            try:
                status = self.select(bid).ping()
            except IOError:
                # no response ⇒ skip
                continue
            if status in (STATUS_OK, STATUS_NOT_FOUND):
                found.append(bid)
        return found

    def ping(self, board_id: int) -> int:
        """
        Send a simple ping (no payload) to the given board_id,
        and return the status code.
        """
        return self.select(board_id).ping()

    def list_sensors(self, board_id: int) -> list[int]:
        """
        Returns all active I²C addresses on the given board.
        """
        return self._sm.list_sensors(board_id)

    def select(self, board_id: int):
        """
        Returns a _BoundMaster for this board_id.
        """
        return _BoundMaster(self._sm, board_id)


class _BoundMaster:
    """
    Wraps SensorMaster with a fixed board_id.
    All calls omit board_id and use the high-level API.
    """
    def __init__(self, sm: SensorMaster, board_id: int):
        self._sm  = sm
        self._bid = board_id

    def ping(self) -> int:
        """
        Send a simple ping to this board_id (no addr),
        and return the status code.
        """
        _, _, _, status, _ = self._sm._execute(self._bid, 0x00, CMD_PING, 0)
        return status

    def read_samples(self, addr: int, sensor_name: str):
        return self._sm.read_samples(self._bid, addr, sensor_name)

    def add_sensor(self, addr: int, sensor_name: str):
        return self._sm.add_sensor(self._bid, addr, sensor_name)

    def remove_sensor(self, addr: int):
        return self._sm.remove_sensor(self._bid, addr)

    def set_period(self, addr: int, ms: int):
        return self._sm.set_period(self._bid, addr, ms)

    def set_gain(self, addr: int, code: int):
        return self._sm.set_gain(self._bid, addr, code)

    def set_range(self, addr: int, code: int):
        return self._sm.set_range(self._bid, addr, code)

    def set_cal(self, addr: int, code: int):
        return self._sm.set_cal(self._bid, addr, code)

    def list_sensors(self) -> list[int]:
        return self._sm.list_sensors(self._bid)
