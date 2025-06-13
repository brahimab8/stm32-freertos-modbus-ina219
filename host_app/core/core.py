import serial
import struct
import threading
from tqdm import tqdm

from .protocol import protocol
from .sensors import registry

STATUS_OK = protocol.status_codes['STATUS_OK']

class SensorMaster:
    """
    Low-level communication class for sending command frames and parsing responses.
    """

    def __init__(self, port='COM3', baud=115200, timeout=0.05):
        self._port = port
        self._baud = baud
        self._timeout = timeout
        self._lock = threading.Lock()
        self._SOF = protocol.constants['SOF_MARKER']
        self._CK_LEN = protocol.constants['CHECKSUM_LENGTH']
        self._open_serial()

    def _open_serial(self):
        self.ser = serial.Serial(self._port, self._baud, timeout=self._timeout)

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, new_port):
        self._port = new_port
        self._open_serial()

    @property
    def baudrate(self):
        return self._baud

    @baudrate.setter
    def baudrate(self, new_baud):
        self._baud = new_baud
        self.ser.baudrate = new_baud

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, new_timeout):
        self._timeout = new_timeout
        self.ser.timeout = new_timeout

    def _send(self, board_id, addr, cmd, param=0):
        frame = bytearray([
            self._SOF, board_id, addr, cmd, param
        ])
        frame.append(frame[1] ^ frame[2] ^ frame[3] ^ frame[4])
        self.ser.write(frame)

    def _recv(self):
        while True:
            b = self.ser.read(1)
            if not b:
                raise IOError('Timeout waiting for SOF')
            if b[0] == self._SOF:
                break

        hdr = self.ser.read(5)
        board, addr, cmd, status, length = struct.unpack('5B', hdr)
        payload = self.ser.read(length)
        chksum = self.ser.read(self._CK_LEN)[0]

        chk = 0
        for byte in hdr + payload:
            chk ^= byte
        if chk != chksum:
            raise ValueError(f'Checksum mismatch: expected 0x{chk:02X}, got 0x{chksum:02X}')

        return board, addr, cmd, status, payload

    def _execute(self, board_id, addr, cmd, param=0):
        with self._lock:
            self.ser.reset_input_buffer()
            self._send(board_id, addr, cmd, param)
            return self._recv()

    # High-level APIs

    def scan(self, start=1, end=255):
        found = []
        for bid in tqdm(range(start, end + 1), desc="Scanning for boards"):
            try:
                _, _, _, status, _ = self._execute(bid, 0x00, protocol.commands['CMD_PING'])
                if status == STATUS_OK:
                    found.append(bid)
            except IOError:
                continue
        return found

    def ping(self, board_id):
        _, _, _, status, _ = self._execute(board_id, 0x00, protocol.commands['CMD_PING'])
        return status

    def list_sensors(self, board_id):
        cmd = protocol.commands['CMD_LIST_SENSORS']
        _, _, _, status, payload = self._execute(board_id, 0x00, cmd)
        if status != STATUS_OK:
            raise RuntimeError(f'LIST_SENSORS failed: {status}')

        sensors = []
        for i in range(0, len(payload), 2):
            type_code, addr7 = payload[i], payload[i+1]
            name = registry.name_from_type(type_code)
            sensors.append((name, f"0x{addr7:02X}"))
        return sensors

    def add_sensor(self, board_id: int, addr: int, sensor_name: str) -> int:
        cmd = protocol.commands['CMD_ADD_SENSOR']
        sensor_code = registry.type_code(sensor_name)
        _, _, _, status, _ = self._execute(board_id, addr, cmd, sensor_code)
        return status

    def remove_sensor(self, board_id: int, addr: int) -> int:
        cmd = protocol.commands['CMD_REMOVE_SENSOR']
        _, _, _, status, _ = self._execute(board_id, addr, cmd, 0)
        return status

    def read_samples(self, board_id, addr, sensor_name, mask_val=None):
        cmd = protocol.commands['CMD_READ_SAMPLES']
        _, _, _, status, payload = self._execute(board_id, addr, cmd)
        if status != STATUS_OK:
            raise RuntimeError(f'READ failed: {status}')

        # Use provided mask if given, otherwise fall back to default mask
        if mask_val is None:
            mask_val = self.get_payload_mask(board_id, addr)

        records = []
        offset = 0
        meta = registry.metadata(sensor_name)
        payload_fields = meta.get('payload_fields', [])
        while offset < len(payload):
            chunk = payload[offset:]
            entry = registry.parse_payload(sensor_name, chunk, mask_val)
            if 'tick' not in entry:
                break
            records.append(entry)

            # 4 bytes for timestamp + sum of enabled field sizes
            consumed = 4
            for idx, fld in enumerate(payload_fields):
                if mask_val & (1 << idx):
                    if 'width' in fld:
                        width = fld['width']
                    else:
                        raise RuntimeError(f"Missing 'width' in metadata for {sensor_name} payload_fields[{idx}]")
                    count = fld.get('count', 1)
                    consumed += count * width
            offset += consumed

        return records

    def get_config(self, board_id, addr, field_cmd):
        _, _, _, status, payload = self._execute(board_id, addr, field_cmd)
        if status != STATUS_OK or not payload:
            raise RuntimeError(f'GET_CONFIG failed for cmd=0x{field_cmd:02X}')
        return payload[0]

    def set_config(self, board_id, addr, field_cmd, value):
        _, _, _, status, _ = self._execute(board_id, addr, field_cmd, value)
        return status

    def get_payload_mask(self, board_id: int, addr: int) -> int:
        cmd = protocol.commands.get('CMD_GET_PAYLOAD_MASK')
        if cmd is None:
            raise ValueError("CMD_GET_PAYLOAD_MASK not defined in protocol")
        
        _, _, _, status, payload = self._execute(board_id, addr, cmd)
        if status != STATUS_OK or not payload:
            raise RuntimeError(f'CMD_GET_PAYLOAD_MASK failed for board {board_id}, addr 0x{addr:02X}')
        
        return payload[0]

    def set_payload_mask(self, board_id: int, addr: int, mask: int) -> int:
        cmd = protocol.commands.get('CMD_SET_PAYLOAD_MASK')
        if cmd is None:
            raise ValueError("CMD_SET_PAYLOAD_MASK not defined in protocol")
        
        _, _, _, status, _ = self._execute(board_id, addr, cmd, mask)
        return status

    def send_command(self, board_id, addr, cmd_name, param=0):
        cmd = protocol.commands.get(cmd_name)
        if cmd is None:
            raise ValueError(f'Unknown command: {cmd_name}')
        _, _, _, status, payload = self._execute(board_id, addr, cmd, param)
        return status, payload

