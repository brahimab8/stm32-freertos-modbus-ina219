import click
from sensor_master.cli.shell import SensorShell
from sensor_master.boards import BoardManager
from sensor_master.protocol import protocol
from sensor_master.sensors import registry

STATUS_NAMES = {v: k for k, v in protocol.status_codes.items()}


@click.group()
@click.option('--port', '-p', default='COM3', show_default=True, help='RS-485 serial port (e.g. COM3)')
@click.option('--baud', '-b', default=115200, show_default=True, help='Serial baud rate')
@click.pass_context
def cli(ctx, port, baud):
    """CLI for interacting with the STM32 sensor hub."""
    ctx.obj = (port, baud)


@cli.command()
@click.pass_context
def session(ctx):
    """Enter an interactive sensor-cli session."""
    port, baud = ctx.obj
    SensorShell(port, baud).cmdloop()


def handle_result(label, status):
    click.echo(f"{label} → {STATUS_NAMES.get(status, status)}")


@cli.command()
@click.option('--board', '-B', required=True, type=int, help='Board ID')
@click.pass_context
def ping(ctx, board):
    """Ping a board (no payload)."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.ping(board)
        handle_result("PING", status)
    except Exception as e:
        click.echo(f"Error pinging board {board}: {e}")


@cli.command(name='list')
@click.option('--board', '-B', required=True, type=int, help='Board ID')
@click.pass_context
def list_sensors(ctx, board):
    """List all active I²C addresses on a board."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        addrs = mgr.select(board).list_sensors()
        if not addrs:
            click.echo("No sensors found")
        else:
            click.echo(f"Found {len(addrs)} sensor(s):")
            for name, addr in addrs:
                click.echo(f"  {name:<10} @ {addr}")
    except Exception as e:
        click.echo(f"Error listing sensors: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.pass_context
def add(ctx, board, addr, sensor):
    """Add a sensor."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.select(board).add_sensor(addr, sensor)
        handle_result("ADD", status)
    except Exception as e:
        click.echo(f"Error adding sensor: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.pass_context
def rmv(ctx, board, addr):
    """Remove a sensor."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.select(board).remove_sensor(addr)
        handle_result("REMOVE", status)
    except Exception as e:
        click.echo(f"Error removing sensor: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--ms', '-m', required=True, type=int)
@click.pass_context
def period(ctx, board, addr, ms):
    """Set polling period (ms)."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.select(board).set_period(addr, ms)
        handle_result("PERIOD", status)
    except ValueError as ve:
        click.echo(f"Invalid period: {ve}")
    except Exception as e:
        click.echo(f"Error setting period: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--value', '-v', required=True, type=int)
@click.pass_context
def gain(ctx, board, addr, value):
    """Set gain."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.select(board).set_gain(addr, value)
        handle_result("GAIN", status)
    except Exception as e:
        click.echo(f"Error setting gain: {e}")


@cli.command(name='range')
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--value', '-v', required=True, type=int)
@click.pass_context
def _range(ctx, board, addr, value):
    """Set input range."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.select(board).set_range(addr, value)
        handle_result("RANGE", status)
    except Exception as e:
        click.echo(f"Error setting range: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--value', '-v', required=True, type=int)
@click.pass_context
def cal(ctx, board, addr, value):
    """Set calibration."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        status = mgr.select(board).set_cal(addr, value)
        handle_result("CAL", status)
    except Exception as e:
        click.echo(f"Error setting calibration: {e}")


@cli.command()
@click.option('--board', '-B', required=True, type=int)
@click.option('--addr', '-a', required=True, type=lambda v: int(v, 0))
@click.option('--sensor', '-s', required=True, type=click.Choice(registry.available()))
@click.pass_context
def read(ctx, board, addr, sensor):
    """Read samples."""
    port, baud = ctx.obj
    mgr = BoardManager(port, baud)
    try:
        recs = mgr.select(board).read_samples(addr, sensor)
        if not recs:
            click.echo("No data")
            return
        click.echo(f"Returned {len(recs)} samples:")
        md = registry.metadata(sensor)
        for i, rec in enumerate(recs):
            click.echo(f"Sample {i}: tick={rec['tick']} ms")
            for fld in md['payload_fields']:
                val = rec.get(fld['name'], '?')
                click.echo(f"  {fld['name']} = {val}")
    except Exception as e:
        click.echo(f"Error reading sensor data: {e}")


if __name__ == '__main__':
    cli()
