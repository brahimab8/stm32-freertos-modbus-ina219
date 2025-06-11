#!/usr/bin/env python3
import cmd
import shlex
import time

from sensor_master.protocol import protocol
from sensor_master.sensors import registry
from sensor_master.backend import SensorBackend, Mode

STATUS_NAMES = {v: k for k, v in protocol.status_codes.items()}


class SensorShell(cmd.Cmd):
    intro = "Entering sensor-cli session. Type help or ? to list commands.\n"
    file = None

    def __init__(self, backend: SensorBackend):
        super().__init__()
        # the shared backend drives everything
        self.backend = backend
        self.current_board = None
        self.current_sensor = None
        self.current_addr = None

    @property
    def prompt(self):
        parts = [f"port={self.backend.board_mgr.port}",
                 f"baud={self.backend.board_mgr.baud}"]
        if self.current_board is not None:
            parts.append(f"board={self.current_board}")
        if self.current_sensor and self.current_addr is not None:
            parts.append(f"sensor={self.current_sensor}@0x{self.current_addr:02X}")
        return "[" + " | ".join(parts) + "] > "

    # --- Config / connection commands ---

    def do_port(self, arg):
        """Set the serial port."""
        try:
            p = shlex.split(arg)[0]
            self.backend.board_mgr.port = p
        except Exception as e:
            print("Error setting port:", e)

    def do_baud(self, arg):
        """Set the baud rate."""
        try:
            b = int(shlex.split(arg)[0])
            self.backend.board_mgr.baud = b
        except Exception as e:
            print("Error setting baud rate:", e)

    # --- Board & sensor selection ---

    def do_board(self, arg):
        """Set the current board ID."""
        try:
            self.current_board = int(shlex.split(arg)[0], 0)
        except Exception as e:
            print("Error setting board ID:", e)

    def do_sensor(self, arg):
        """Select the current sensor and address."""
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

    # --- Discovery commands ---

    def do_ping(self, arg):
        """Ping the currently selected board: ping"""
        if self.current_board is None:
            print("Select a board first:  board <id>")
            return
        try:
            status = self.backend.ping(self.current_board)
            print("PING →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error pinging board:", e)

    def do_scan(self, arg):
        """Scan for all boards (discovery mode)."""
        try:
            # Run discovery mode and get back a dict: { board_id: [ {name, addr, config}, … ], … }
            info = self.backend.set_mode(Mode.DISCOVERY)

            if not isinstance(info, dict):
                print("Boards found: None")
                return

            boards = sorted(info.keys())
            if not boards:
                print("Boards found: None")
                return

            # Print each board and its sensor‐list
            for bid in boards:
                sensors = info[bid]            # this is a list of { 'name':…, 'addr':…, 'config':… }
                if sensors:
                    print(f"Board {bid}:")
                    for s in sensors:
                        print(f"  • {s['name']} @ 0x{s['addr']:02X}")
                else:
                    print(f"Board {bid}: <no sensors>")

        except Exception as e:
            print("Error scanning for boards:", e)

    def do_list(self, arg):
        """List sensors on the current board."""
        if self.current_board is None:
            print("Select a board first:  board <id>")
            return
        try:
            sensors = self.backend.list_sensors(self.current_board)
            if not sensors:
                print("No sensors found")
                return
            print("Active sensors:")
            for name, addr in sensors:
                print(f"  {name:<10} @ {addr}")
        except Exception as e:
            print("Error listing sensors:", e)

    # --- Sensor configuration commands ---

    def do_add(self, arg):
        """Add the current sensor to the current board."""
        if None in (self.current_board, self.current_sensor, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            status = self.backend.add_sensor(
                self.current_board, self.current_addr, self.current_sensor
            )
            print("ADD →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error adding sensor:", e)

    def do_rmv(self, arg):
        """Remove the current sensor from the board."""
        if None in (self.current_board, self.current_addr):
            print("Select board and sensor first.")
            return
        try:
            status = self.backend.remove_sensor(
                self.current_board, self.current_addr
            )
            print("REMOVE →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error removing sensor:", e)

    # --- Manual read command ---

    def do_read(self, arg):
        """Read one batch of samples from the current sensor."""
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        try:
            recs = self.backend.read_samples(
                self.current_board, self.current_addr, self.current_sensor
            )
            if not recs:
                print("No data")
                return
            # print table
            md = registry.metadata(self.current_sensor)
            fields = [name for name in [f['name'] for f in md['payload_fields']]
            if name in recs[0].keys()]

            headers = ["tick(ms)"] + fields
            print("\t".join(f"{h:>12}" for h in headers))
            for rec in recs:
                row = [rec['tick']] + [rec.get(f, "") for f in fields]
                print("\t".join(f"{v:>12}" for v in row))
        except Exception as e:
            print("Error reading samples:", e)

    # --- Streaming commands ---

    def do_stream(self, arg):
        """
        Stream all known sensors continuously.
        Usage: stream [interval_s]
        """
        interval = float(shlex.split(arg)[0]) if arg else 1.0
        print(f"→ Streaming all sensors every {interval}s. Press CTRL-C or 'stop'.")
        self.backend.start_stream(self._print_cb)
        try:
            # loop until user interrupts
            while self.backend.mode == Mode.STREAM:
                time.sleep(interval)
        except KeyboardInterrupt:
            self.backend.stop_stream()
            print("\n→ Stream stopped.")

    def do_stop(self, arg):
        """Stop any ongoing stream."""
        self.backend.stop_stream()
        print("→ Stream stopped.")

    def _print_cb(self, board, addr, sensor, records):
        """
        Called by StreamScheduler for each batch of “records” from one sensor.
        We only print those payload_fields that actually showed up in rec.
        """
        print(f"\n[Board {board} | Sensor {sensor}@0x{addr:02X}] {len(records)} samples")
        md = registry.metadata(sensor)

        # Build a list of field-names that were actually present in the first record
        # (all records have the same mask, so checking rec.keys() suffices)
        for rec in records:
            # Only include fields that actually appear in `rec`
            vals = "  ".join(
                f"{fld['name']}={rec[fld['name']]}"
                for fld in md['payload_fields']
                if fld['name'] in rec
            )
            print(f"  tick={rec['tick']}ms  {vals}")

    # --- Generalized configuration commands ---

    def do_set_config(self, arg):
        """Set a configuration field for the current sensor.
        Usage: set_config <field_name> <value>
        """
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        try:
            field_name, value = shlex.split(arg)
            value = int(value, 0)
            status = self.backend.set_config(
                self.current_board, self.current_addr, self.current_sensor, field_name, value
            )
            print("SET_CONFIG →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error:", e)
            self._print_config_help()

    def do_get_config(self, arg):
        """Get a specific configuration field of the current sensor.
        Usage: get_config <field_name> OR get_config all
        """
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        args = shlex.split(arg)
        if not args:
            print("Usage: get_config <field_name> OR get_config all")
            self._print_config_help()
            return
        field_name = args[0].strip().lower()
        try:
            if field_name == "all":
                self.do_get_all_configs("")
                return
            value = self.backend.get_config_field(
                self.current_board, self.current_addr, self.current_sensor, field_name
            )
            print(f"{field_name.upper()} → {value}")
        except Exception as e:
            print("Error:", e)
            self._print_config_help()

    def do_show_config(self, arg):
        """Show all available config fields for the current sensor."""
        if self.current_sensor is None:
            print("Select a sensor first.")
            return
        md = registry.metadata(self.current_sensor)
        config_fields = md.get('config_fields', [])
        if not config_fields:
            print(f"No configurable fields for sensor '{self.current_sensor}'.")
            return
        print(f"Config fields for '{self.current_sensor}':")
        for fld in config_fields:
            setter = fld.get('setter_cmd', 'None')
            getter = fld.get('getter_cmd', 'None')
            print(f"  {fld['name']:15} Getter: {getter:<15} Setter: {setter}")

    def _print_config_help(self):
        """Prints available config fields for the current sensor, with hints."""
        if not self.current_sensor:
            print("No sensor selected.")
            return
        try:
            md = registry.metadata(self.current_sensor)
            print(f"Available config fields for '{self.current_sensor}':")
            for fld in md.get("config_fields", []):
                desc = fld.get("description", "").strip()
                rng  = fld.get("range", "")
                enum = fld.get("enum_labels", {})
                print(f"  {fld['name']:15} {desc}")
                if rng:
                    print(f"{'':17}Range: {rng}")
                if enum:
                    print(f"{'':17}Enums:")
                    for k, v in enum.items():
                        print(f"{'':19}{k} → {v.strip()}")
        except Exception:
            print("(unable to load metadata)")

    def do_get_all_configs(self, arg):
        """Get all configuration values for the current sensor."""
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        try:
            configs = self.backend.get_all_configs(
                self.current_board, self.current_addr, self.current_sensor
            )
            md = registry.metadata(self.current_sensor)
            config_fields = {cf["name"]: cf for cf in md.get("config_fields", [])}
            print("Current Configurations:")
            for field, value in configs.items():
                explanation = ""
                cf = config_fields.get(field)
                if cf:
                    enum_map = cf.get("enum_labels")
                    if enum_map and str(value) in enum_map:
                        explanation = f"({enum_map[str(value)]})"
                    elif field == "period":
                        explanation = f"(polls every {value * 100} ms)"
                    elif cf.get("description"):
                        explanation = f"({cf['description']})"
                print(f"  {field}: {value} {explanation}")
        except Exception as e:
            print("Error getting all configs:", e)

    def do_setmask(self, arg):
        """
        Set the payload-bitmask (one byte) for the selected sensor.
        Usage: setmask <mask_int>
        """
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        try:
            mask = int(shlex.split(arg)[0], 0)
            if not (0 <= mask <= 0xFF):
                raise ValueError
            status = self.backend.set_payload_mask(
                self.current_board,
                self.current_addr,
                mask
            )
            print("SET_MASK →", STATUS_NAMES.get(status, status))
        except Exception as e:
            print("Error setting payload mask:", e)

    def do_getmask(self, arg):
        """
        Query the current payload-bitmask (one byte) for the selected sensor.
        Usage: getmask
        """
        if None in (self.current_board, self.current_addr, self.current_sensor):
            print("Select board and sensor first.")
            return
        try:
            mask = self.backend.get_payload_mask(
                self.current_board, self.current_addr
            )
            print(f"PAYLOAD_MASK → 0x{mask:02X}")
        except Exception as e:
            print("Error getting payload mask:", e)

    # --- Utility commands & exits ---

    def do_sensors(self, arg):
        """List all available sensor types and their defaults."""
        for name in registry.available():
            md = registry.metadata(name)
            print(f"{name} → defaults {md.get('config_defaults', {})}")

    def do_quit(self, arg):
        """Exit the shell."""
        return True
    
    def do_exit(self, arg):
        """Exit the shell."""
        return True
    
    def do_EOF(self, arg):  
        """Exit the shell (Ctrl-D)."""
        return True

