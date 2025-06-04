from .core import SensorMaster
from .protocol import protocol

class BoardManager:
    def __init__(self, port: str = 'COM3', baud: int = 115200, timeout: float = 0.05):
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

    def scan(self, start: int = 1, end: int = 255) -> list[int]:
        return self._sm.scan(start, end)

    def ping(self, board_id: int) -> int:
        return self._sm.ping(board_id)

    def list_sensors(self, board_id: int) -> list[tuple[str, str]]:
        return self._sm.list_sensors(board_id)

    def select(self, board_id: int):
        return _BoundMaster(self._sm, board_id)


class _BoundMaster:
    def __init__(self, sm: SensorMaster, board_id: int):
        self._sm = sm
        self._bid = board_id

    def ping(self) -> int:
        return self._sm.ping(self._bid)

    def list_sensors(self) -> list[tuple[str, str]]:
        return self._sm.list_sensors(self._bid)

    def read_samples(self, addr: int, sensor_name: str) -> list[dict]:
        return self._sm.read_samples(self._bid, addr, sensor_name)

    def add_sensor(self, addr: int, sensor_name: str) -> int:
        return self._sm.add_sensor(self._bid, addr, sensor_name)

    def remove_sensor(self, addr: int) -> int:
        return self._sm.remove_sensor(self._bid, addr)

    def set_payload_mask(self, addr: int, mask: int) -> int:
        return self._sm.set_payload_mask(self._bid, addr, mask)

    def get_payload_mask(self, addr: int) -> int:
        return self._sm.get_payload_mask(self._bid, addr)

    def set_config(self, addr: int, cmd_name: str, param: int):
        status, _ = self.execute_cmd(addr, cmd_name, param)
        return status

    def get_config(self, addr: int, cmd_name: str):
        status, payload = self.execute_cmd(addr, cmd_name)
        return payload if status == protocol.status_codes['STATUS_OK'] else None

    def execute_cmd(self, addr: int, cmd_name: str, param: int = 0):
        """
        Generic command execution method.
        """
        cmd = protocol.commands.get(cmd_name)
        if cmd is None:
            raise ValueError(f"Unknown command '{cmd_name}'")
        _, _, _, status, payload = self._sm._execute(self._bid, addr, cmd, param)
        return status, payload
