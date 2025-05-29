import serial
import struct
import time
from .protocol import protocol
from .sensors import registry

class SensorMaster:
    def __init__(self,
                 port: str = 'COM3',
                 baud: int = 115200,
                 timeout: float = 1.0):
        self._port    = port
        self._baud    = baud
        self._timeout = timeout
        self._open_serial()

        # protocol constants
        self._SOF     = protocol.constants['SOF_MARKER']
        self._TICK_BYTES = protocol.constants['TICK_BYTES']
        self._CK_LEN  = protocol.constants['CHECKSUM_LENGTH']

    def _open_serial(self):
        # (re)open serial with current settings
        self.ser = serial.Serial(self._port,
                                 self._baud,
                                 timeout=self._timeout)

    @property
    def port(self) -> str:
        return self._port

    @port.setter
    def port(self, new_port: str):
        self._port = new_port
        self._open_serial()

    @property
    def baudrate(self) -> int:
        return self._baud

    @baudrate.setter
    def baudrate(self, new_baud: int):
        self._baud = new_baud
        self.ser.baudrate = new_baud

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, new_to: float):
        self._timeout = new_to
        self.ser.timeout = new_to

    def _send(self, board_id: int, addr: int, cmd: int, param: int = 0):
        frame = bytearray(5)
        frame[0] = self._SOF
        frame[1] = board_id
        frame[2] = addr
        frame[3] = cmd
        frame[4] = param
        frame.append(frame[1] ^ frame[2] ^ frame[3] ^ frame[4])
        self.ser.write(frame)

    def _recv(self):
        # wait for SOF
        while True:
            b = self.ser.read(1)
            if not b:
                raise IOError('Timeout waiting for SOF')
            if b[0] == self._SOF:
                break

        hdr = self.ser.read(5)
        board, addr, cmd, status, length = struct.unpack('5B', hdr)
        payload = self.ser.read(length)
        chksum  = self.ser.read(self._CK_LEN)[0]

        # verify XOR checksum
        chk = 0
        for byte in hdr + payload:
            chk ^= byte
        if chk != chksum:
            raise ValueError(
                f'Checksum mismatch: got 0x{chksum:02X}, expected 0x{chk:02X}'
            )

        return board, addr, cmd, status, payload

    def _execute(self, board_id: int, addr: int,
                 cmd: int, param: int = 0):
        self._send(board_id, addr, cmd, param)
        return self._recv()

    # — high-level APIs —#

    def read_samples(self,
                     board_id: int,
                     addr: int,
                     sensor_name: str):
        """
        Read raw samples off the wire, then split and decode each record
        according to the sensor’s payload_fields metadata.
        Returns a list of dicts, each with a 'tick' key plus one entry per field.
        """
        cmd   = protocol.commands['CMD_READ_SAMPLES']
        _, _, _, status, payload = self._execute(board_id, addr, cmd)
        if status != protocol.status_codes['STATUS_OK']:
            raise RuntimeError(f'READ failed: {status}')

        # Grab the per-field metadata for this sensor:
        md     = registry.metadata(sensor_name)
        fields = md['payload_fields']

        records = []
        offset  = 0
        rec_len = self._TICK_BYTES + sum(f['size'] for f in fields)

        # Step through the payload, record by record
        while offset + rec_len <= len(payload):
            # first TICK_BYTES is a big-endian uint32
            tick = struct.unpack_from('>I', payload, offset)[0]
            offset += self._TICK_BYTES

            entry = {'tick': tick}
            # now unpack each field in order
            for fld in fields:
                raw = payload[offset:offset + fld['size']]
                offset += fld['size']

                # decode by type prefix
                t = fld['type']
                if t.startswith('uint'):
                    val = int.from_bytes(raw, 'big', signed=False)
                elif t.startswith('int'):
                    val = int.from_bytes(raw, 'big', signed=True)
                else:
                    # fallback: hex string
                    val = raw.hex()

                entry[fld['name']] = val

            records.append(entry)

        return records

    def add_sensor(self,
                   board_id: int,
                   addr: int,
                   sensor_name: str):
        cmd  = protocol.commands['CMD_ADD_SENSOR']
        code = registry.type_code(sensor_name)
        _, _, _, status, _ = self._execute(board_id, addr, cmd, code)
        return status

    def remove_sensor(self,
                      board_id: int,
                      addr: int):
        cmd = protocol.commands['CMD_REMOVE_SENSOR']
        _, _, _, status, _ = self._execute(board_id, addr, cmd, 0)
        return status

    def set_period(self,
                   board_id: int,
                   addr: int,
                   ms: int):
        if ms % 100 != 0:
            raise ValueError('Period must be multiple of 100 ms')
        param = ms // 100
        cmd = protocol.commands['CMD_SET_PERIOD']
        _, _, _, status, _ = self._execute(board_id, addr, cmd, param)
        return status

    def set_gain(self,
                 board_id: int,
                 addr: int,
                 gain_code: int):
        cmd = protocol.commands['CMD_SET_GAIN']
        _, _, _, status, _ = self._execute(board_id, addr, cmd, gain_code)
        return status

    def set_range(self,
                  board_id: int,
                  addr: int,
                  range_code: int):
        cmd = protocol.commands['CMD_SET_RANGE']
        _, _, _, status, _ = self._execute(board_id, addr, cmd, range_code)
        return status

    def set_cal(self,
                board_id: int,
                addr: int,
                cal_code: int):
        cmd = protocol.commands['CMD_SET_CAL']
        _, _, _, status, _ = self._execute(board_id, addr, cmd, cal_code)
        return status

    def ping(self, board_id: int):
        """
        Send a simple ping (no payload) to the given board_id,
        and return the status code.
        """
        cmd = protocol.commands['CMD_PING']
        _, _, _, status, _ = self._execute(board_id, 0x00, cmd, 0)
        return status

    def list_sensors(self, board_id: int) -> list[int]:
        """
        Ask the board to list all active I²C addresses it’s managing.
        Returns a list of addr7 (0x01–0x7F) bytes.
        """
        cmd = protocol.commands['CMD_LIST_SENSORS']
        # we use addr=0x00 and param=0 for a pure board-level cmd
        _, _, _, status, payload = self._execute(board_id, 0x00, cmd, 0)
        if status != protocol.status_codes['STATUS_OK']:
            raise RuntimeError(f'LIST_SENSORS failed: {status}')
        # payload is just a sequence of addr7 bytes
        return list(payload)
