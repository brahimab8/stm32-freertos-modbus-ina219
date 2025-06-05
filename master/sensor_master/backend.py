from enum import Enum, auto
import threading
from .boards import BoardManager
from .scheduler import StreamScheduler
from .sensors import registry
from .protocol import protocol


class Mode(Enum):
    IDLE = auto()
    DISCOVERY = auto()
    STREAM = auto()


class SensorBackend:
    def __init__(self, port='COM3', baud=115200, timeout=0.05):
        self.board_mgr = BoardManager(port, baud, timeout)
        self.stream_scheduler = StreamScheduler(self.board_mgr, timeout)
        self.mode = Mode.IDLE
        self.lock = threading.Lock()

        # Caches
        self.config_cache = {}  # {(board, addr, sensor): {config_field: value}}
        self.payload_mask_cache = {}  # {(board, addr): mask}

    def set_mode(self, new_mode: Mode):
        with self.lock:
            if self.mode == new_mode:
                return self._do_discovery() if new_mode == Mode.DISCOVERY else None

            if self.mode == Mode.STREAM:
                self.stream_scheduler.stop()

            self.mode = new_mode
            return self._do_discovery() if new_mode == Mode.DISCOVERY else None

    def _do_discovery(self):
        discovery_info = {}
        for bid in self.board_mgr.scan():
            bound = self.board_mgr.select(bid)

            try:
                raw_sensors = bound.list_sensors()
            except RuntimeError as e:
                raw_sensors = []

            sensor_list = []
            for name, hex_addr in raw_sensors:
                addr = int(hex_addr, 16)
                cfg = self._get_sensor_config(bound, bid, addr, name)
                sensor_list.append({'name': name, 'addr': addr, 'config': cfg})

            discovery_info[bid] = sensor_list
        return discovery_info

    def _get_sensor_config(self, bound, board, addr, name):
        md = registry.metadata(name)
        key = (board, addr, name)

        if key not in self.config_cache:
            self.config_cache[key] = {}

        cfg = {}
        for fld in md.get('config_fields', []):
            field_name = fld['name']
            if field_name in self.config_cache[key]:
                cfg[field_name] = self.config_cache[key][field_name]
                continue

            cmd_name = fld['getter_cmd']
            cmd = protocol.commands.get(cmd_name)

            if cmd is None:
                continue

            _, _, _, status, payload = bound._sm._execute(board, addr, cmd, 0)

            if status == protocol.status_codes['STATUS_OK']:
                value = int.from_bytes(payload, fld.get('endian') or 'little')
                cfg[field_name] = value
                self.config_cache[key][field_name] = value

        return cfg

    def start_stream(self, callback):
        with self.lock:
            if self.mode == Mode.STREAM:
                return

            self.stream_scheduler.clear_subscriptions()

            discovery_map = self._do_discovery()
            for bid, sensors in discovery_map.items():
                for s in sensors:
                    # Use actual config 'period' value in 100ms units → convert to seconds
                    raw_period = s['config'].get('period', 10)  # default to 1000ms
                    interval = max(0.1, raw_period * 0.1)        # ensure at least 100ms
                    self.stream_scheduler.subscriptions.append((bid, s['addr'], s['name'], interval))

            self.mode = Mode.STREAM

        self.stream_scheduler.start(callback)

    def stop_stream(self):
        with self.lock:
            if self.mode == Mode.STREAM:
                self.stream_scheduler.stop()
                self.mode = Mode.IDLE

    # Generic setter
    def set_config(self, board, addr, sensor, field, value):
        md = registry.metadata(sensor)
        fld = next((f for f in md['config_fields'] if f['name'] == field), None)

        if fld is None or fld['setter_cmd'] is None:
            raise ValueError(f"No setter for {field}")

        cmd = protocol.commands[fld['setter_cmd']]
        _, _, _, status, _ = self.board_mgr.select(board)._sm._execute(board, addr, cmd, value)

        if status == protocol.status_codes['STATUS_OK']:
            self.config_cache.setdefault((board, addr, sensor), {})[field] = value

        return status

    # Generic getter
    def get_config_field(self, board, addr, sensor, field):
        key = (board, addr, sensor)
        if key in self.config_cache and field in self.config_cache[key]:
            return self.config_cache[key][field]

        md = registry.metadata(sensor)
        fld = next((f for f in md['config_fields'] if f['name'] == field), None)

        if fld is None:
            raise ValueError(f"No getter for {field}")

        cmd = protocol.commands[fld['getter_cmd']]
        _, _, _, status, payload = self.board_mgr.select(board)._sm._execute(board, addr, cmd, 0)

        if status == protocol.status_codes['STATUS_OK']:
            value = int.from_bytes(payload, fld.get('endian') or 'little')
            self.config_cache.setdefault(key, {})[field] = value
            return value

        raise RuntimeError(f"Failed to get {field}")

    def get_all_configs(self, board, addr, sensor):
        md = registry.metadata(sensor)
        return {fld['name']: self.get_config_field(board, addr, sensor, fld['name']) for fld in md['config_fields']}

    def get_payload_mask(self, board, addr):
        key = (board, addr)
        if key in self.payload_mask_cache:
            return self.payload_mask_cache[key]

        mask = self.board_mgr.select(board).get_payload_mask(addr)
        self.payload_mask_cache[key] = mask
        return mask

    def set_payload_mask(self, board: int, addr: int, mask: int) -> int:
        """
        Change the sensor’s payload bitmask (one byte). Each bit corresponds
        to one payload_fields entry in the order they appear in JSON.
        Also updates the cache.
        """
        status = self.board_mgr.select(board).set_payload_mask(addr, mask)

        if status == protocol.status_codes['STATUS_OK']:
            self.payload_mask_cache[(board, addr)] = mask

        return status

    # Other methods (ping, add_sensor, remove_sensor, etc.) remain unchanged for brevity.

    # ————————————————————————
    #  (write/or read)
    # ————————————————————————
    def ping(self, board: int) -> int:
        return self.board_mgr.ping(board)

    def scan_boards(self) -> list[int]:
        return self.board_mgr.scan()

    def list_sensors(self, board: int) -> list[tuple[str,str]]:
        return self.board_mgr.list_sensors(board)

    def add_sensor(self, board: int, addr: int, name: str) -> int:
        return self.board_mgr.select(board).add_sensor(addr, name)

    def remove_sensor(self, board: int, addr: int) -> int:
        return self.board_mgr.select(board).remove_sensor(addr)

    def read_samples(self, board: int, addr: int, sensor: str) -> list[dict]:
        # Get the correct bitmask (cached or from device)
        mask = self.get_payload_mask(board, addr)

        # Pass the mask down to the SensorMaster
        return self.board_mgr.select(board)._sm.read_samples(board, addr, sensor, mask_val=mask)
