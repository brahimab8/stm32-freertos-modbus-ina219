#!/usr/bin/env python3
import cmd
import shlex

from sensor_master.boards import BoardManager
from sensor_master.protocol import protocol
from sensor_master.sensors import registry

STATUS_NAMES = {v: k for k, v in protocol.status_codes.items()}


class SensorShell(cmd.Cmd):
    intro = "Entering sensor-cli session. Type help or ? to list commands.\n"
    file = None

    def __init__(self, port, baud):
        super().__init__()
        self.manager = BoardManager(port, baud)
        self.current_board = None
        self.current_sensor = None
        self.current_addr = None

    @property
    def prompt(self):
        parts = [f"port={self.manager.port}", f"baud={self.manager.baud}"]
        if self.current_board is not None:
            parts.append(f"board={self.current_board}")
        if self.current_sensor and self.current_addr is not None:
            parts.append(f"sensor={self.current_sensor}@0x{self.current_addr:02X}")
        return "[" + " | ".join(parts) + "] > "

    def do_port(self, arg):
        try:
            self.manager.port = shlex.split(arg)[0]
        except Exception as e:
            print("Error setting port:", e)

    def do_baud(self, arg):
        try:
            self.manager.baud = int(shlex.split(arg)[0])
        except Exception as e:
            print("Error setting baud rate:", e)

    def do_board(self, arg):
        try:
            self.current_board = int(shlex.split(arg)[0], 0)
        except Exception as e:
            print("Error setting board ID:", e)

    def do_sensor(self, arg):
        if self.current_board is None:
            print("Select a board first:  board <id>")
            return
        try:
            name, addr = shlex.split(arg)
            name = name.lower()
            if name not in registry.available():
                print("Unknown sensor. Available:", ", ".join(registry.available()))
                return
            self.current_sensor = name
            self.current_addr = int(addr, 0)
        except Exception as e:
            print("Usage: sensor <type> <addr>\nError:", e)

    def do_scan(self, arg):
        try:
            boards = self.manager.scan()
            print("Boards found:", ", ".join(str(b) for b in boards) or "None")
        except Exception as e:
            print("Error scanning:", e)

    def do_ping(self, arg):
        if self.current_board is None:
            print("Select a board first:  board <id>")
            return
        try:
            status = self.manager.ping(self.current_board)
            print("PING →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error pinging board:", e)

    def do_list(self, arg):
        if self.current_board is None:
            print("Select a board first:  board <id>")
            return
        try:
            sensors = self.manager.select(self.current_board).list_sensors()
            if not sensors:
                print("No sensors found")
                return
            print("Active sensors:")
            for name, addr in sensors:
                print(f"  {name:<10} @ {addr}")
        except Exception as e:
            print("Error listing sensors:", e)

    def do_add(self, arg):
        if None in (self.current_board, self.current_sensor, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            status = self.manager.select(self.current_board).add_sensor(self.current_addr, self.current_sensor)
            print("ADD →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error adding sensor:", e)

    def do_rmv(self, arg):
        if None in (self.current_board, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            status = self.manager.select(self.current_board).remove_sensor(self.current_addr)
            print("REMOVE →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error removing sensor:", e)

    def do_period(self, arg):
        if None in (self.current_board, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            ms = int(shlex.split(arg)[0])
            status = self.manager.select(self.current_board).set_period(self.current_addr, ms)
            print("PERIOD →", STATUS_NAMES.get(status, status))
        except ValueError:
            print("Period must be an integer (ms), and a multiple of 100.")
        except Exception as e:
            print("Error setting period:", e)

    def do_gain(self, arg):
        if None in (self.current_board, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            code = int(shlex.split(arg)[0])
            status = self.manager.select(self.current_board).set_gain(self.current_addr, code)
            print("GAIN →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error setting gain:", e)

    def do_range(self, arg):
        if None in (self.current_board, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            code = int(shlex.split(arg)[0])
            status = self.manager.select(self.current_board).set_range(self.current_addr, code)
            print("RANGE →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error setting range:", e)

    def do_cal(self, arg):
        if None in (self.current_board, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            code = int(shlex.split(arg)[0])
            status = self.manager.select(self.current_board).set_cal(self.current_addr, code)
            print("CAL →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error setting calibration:", e)

    def do_read(self, arg):
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        try:
            recs = self.manager.select(self.current_board).read_samples(self.current_addr, self.current_sensor)
            if not recs:
                print("No data")
                return
            fields = [fld['name'] for fld in registry.metadata(self.current_sensor)['payload_fields']]
            headers = ["tick(ms)"] + fields
            print("\t".join(f"{h:>12}" for h in headers))
            for rec in recs:
                row = [rec['tick']] + [rec[f] for f in fields]
                print("\t".join(f"{v:>12}" for v in row))
        except Exception as e:
            print("Error reading samples:", e)

    def do_sensors(self, arg):
        try:
            for name in registry.available():
                md = registry.metadata(name)
                print(f"{name} → defaults {md.get('config_defaults', {})}")
        except Exception as e:
            print("Error listing sensor types:", e)

    def do_quit(self, arg):
        return True

    def do_exit(self, arg):
        return True

    def do_EOF(self, arg):
        return True

    def help_add(self):
        print("Add the currently selected sensor to the board.")
        print("Usage: add")

    def help_read(self):
        print("Read samples from the selected sensor. Usage: read")

    def help_ping(self):
        print("Ping the currently selected board. Usage: ping")

    def help_list(self):
        print("List all active sensor addresses on the selected board. Usage: list")

    def help_rmv(self):
        print("Remove the selected sensor. Usage: rmv")
