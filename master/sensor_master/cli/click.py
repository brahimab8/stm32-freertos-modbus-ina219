#!/usr/bin/env python3
import click

from sensor_master.protocol import protocol
from sensor_master.sensors import registry
from sensor_master.backend import SensorBackend

STATUS_NAMES = {v: k for k, v in protocol.status_codes.items()}


@click.group()
@click.option('--port', '-p', default='COM3', show_default=True,
              help='RS-485 serial port (e.g. COM3)')
@click.option('--baud', '-b', default=115200, show_default=True,
              help='Serial baud rate')
@click.pass_context
def cli(ctx, port, baud):
    """CLI for interacting with the STM32 sensor hub."""
    ctx.obj = SensorBackend(port=port, baud=baud)


def handle_result(label, status):
    click.echo(f"{label} → {STATUS_NAMES.get(status, status)}")


@cli.command()
@click.pass_context
def session(ctx):
    """Enter an interactive sensor-cli session."""
    from sensor_master.cli.shell import SensorShell
    SensorShell(ctx.obj).cmdloop()


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.pass_context
def ping(ctx, board):
    """Ping a board to check if it is alive."""
    backend = ctx.obj
    try:
        status = backend.ping(board)
        click.echo(f"PING → {STATUS_NAMES.get(status, status)}")
    except Exception as e:
        click.echo(f"Error pinging board {board}: {e}")


@cli.command()
@click.pass_context
def scan(ctx):
    """Scan for all boards (discovery)."""
    backend = ctx.obj
    boards = list(backend.set_mode("discovery").keys())
    click.echo("Boards found: " + (", ".join(str(b) for b in boards) or "None"))


@cli.command(name='list')
@click.option('--board', '-B', required=True, type=int)
@click.pass_context
def list_sensors(ctx, board):
    """List all active sensors on a board."""
    backend = ctx.obj
    sensors = backend.list_sensors(board)
    if not sensors:
        click.echo("No sensors found")
    else:
        click.echo(f"Found {len(sensors)} sensor(s):")
        for name, addr in sensors:
            click.echo(f"  {name:<10} @ {addr}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.pass_context
def add(ctx, board, addr, sensor):
    """Add a sensor to a board."""
    backend = ctx.obj
    status = backend.add_sensor(board, addr, sensor)
    handle_result("ADD", status)


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.pass_context
def rmv(ctx, board, addr):
    """Remove a sensor from a board."""
    backend = ctx.obj
    status = backend.remove_sensor(board, addr)
    handle_result("REMOVE", status)


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--ms', '-m', required=True, type=int)
@click.pass_context
def period(ctx, board, addr, ms):
    """Set sensor polling period (ms)."""
    backend = ctx.obj
    try:
        status = backend.set_period(board, addr, ms)
        handle_result("PERIOD", status)
    except ValueError as e:
        click.echo(f"Invalid period: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.pass_context
def read(ctx, board, addr, sensor):
    """Read one batch of samples from a sensor."""
    backend = ctx.obj
    recs = backend.read_samples(board, addr, sensor)
    if not recs:
        click.echo("No data")
        return
    click.echo(f"Returned {len(recs)} samples:")
    md = registry.metadata(sensor)
    for i, rec in enumerate(recs):
        click.echo(f"Sample {i}: tick={rec['tick']} ms")
        for fld in md['payload_fields']:
            click.echo(f"  {fld['name']} = {rec[fld['name']]}")

@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.pass_context
def get_period(ctx, board, addr):
    """Get the current polling period (ms) for a sensor."""
    backend = ctx.obj
    try:
        ms = backend.get_period(board, addr)
        click.echo(f"PERIOD → {ms} ms")
    except Exception as e:
        click.echo(f"Error getting period: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.option('--field', '-f', required=True, type=str)
@click.option('--value', '-v', required=True, type=int)
@click.pass_context
def set_config(ctx, board, addr, sensor, field, value):
    """Set a configuration field for a sensor."""
    backend = ctx.obj
    status = backend.set_config(board, addr, sensor, field, value)
    handle_result(f"SET_CONFIG {field}", status)


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.option('--field', '-f', required=True, type=str)
@click.pass_context
def get_config(ctx, board, addr, sensor, field):
    """Get a configuration field value from a sensor. Use --field all to list all."""
    backend = ctx.obj
    if field.lower() == "all":
        ctx.invoke(get_all_configs, board=board, addr=addr, sensor=sensor)
        return
    try:
        value = backend.get_config_field(board, addr, sensor, field)
        click.echo(f"{field.upper()} → {value}")
    except Exception as e:
        click.echo(f"Error getting config '{field}': {e}")
        ctx.invoke(show_config, sensor=sensor)


@cli.command()
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.pass_context
def show_config(ctx, sensor):
    """Show available configuration fields for a sensor."""
    md = registry.metadata(sensor)
    fields = md.get("config_fields", [])
    if not fields:
        click.echo(f"No configurable fields for '{sensor}'.")
        return
    click.echo(f"Available config fields for '{sensor}':")
    for f in fields:
        click.echo(f"  {f['name']:15} {f.get('description', '')}")
        if f.get("range"):
            click.echo(f"{'':17}Range: {f['range']}")
        for k, v in f.get("enum_labels", {}).items():
            click.echo(f"{'':19}{k} → {v.strip()}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.pass_context
def get_all_configs(ctx, board, addr, sensor):
    """Get all configuration fields for a sensor."""
    backend = ctx.obj
    try:
        configs = backend.get_all_configs(board, addr, sensor)
        md = registry.metadata(sensor)
        fields = {f["name"]: f for f in md.get("config_fields", [])}
        click.echo("Current configurations:")
        for field, value in configs.items():
            explanation = ""
            fmeta = fields.get(field)
            if fmeta:
                enum = fmeta.get("enum_labels")
                if enum and str(value) in enum:
                    explanation = f"({enum[str(value)]})"
                elif fmeta.get("description"):
                    explanation = f"({fmeta['description']})"
            click.echo(f"  {field}: {value} {explanation}")
    except Exception as e:
        click.echo(f"Error getting all configs: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--mask', '-m', required=True, type=int)
@click.pass_context
def setmask(ctx, board, addr, mask):
    """Set the one-byte payload mask (0..255)."""
    backend = ctx.obj
    status = backend.set_payload_mask(board, addr, mask)
    click.echo(f"SET_MASK → {STATUS_NAMES.get(status, status)}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.pass_context
def getmask(ctx, board, addr):
    """Get the one-byte payload mask (0..255)."""
    backend = ctx.obj
    try:
        mask = backend.get_payload_mask(board, addr)
        click.echo(f"PAYLOAD_MASK → 0x{mask:02X}")
    except Exception as e:
        click.echo(f"Error getting payload mask: {e}")


@cli.command()
@click.option('--interval', '-i', default=1.0, show_default=True, type=float,
              help='Seconds between prints')
@click.pass_context
def stream(ctx, interval):
    """Stream all discovered sensors continuously."""
    import time
    backend = ctx.obj
    click.echo(f"→ Streaming every {interval}s. CTRL-C to stop.")

    def _cb(board, addr, sensor, records):
        click.echo(f"\n[Board {board} | Sensor {sensor}@0x{addr:02X}] {len(records)} samples")
        md = registry.metadata(sensor)
        for rec in records:
            vals = "  ".join(
                f"{fld['name']}={rec[fld['name']]}"
                for fld in md['payload_fields']
                if fld['name'] in rec
            )
            click.echo(f"  tick={rec['tick']}ms  {vals}")

    backend.start_stream(_cb)

    try:
        while backend.mode == "stream":
            time.sleep(interval)
    except KeyboardInterrupt:
        backend.stop_stream()
        click.echo("\n→ Stream stopped.")


if __name__ == '__main__':
    cli()
