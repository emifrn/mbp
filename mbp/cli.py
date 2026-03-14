import getpass
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from mbp import db, validate, config
from mbp.models import BPReading, WeightReading
from mbp import report as rpt
from mbp import plot as plt_mod

console = Console()


class RichGroup(click.Group):
    """Click Group that formats errors with Rich."""
    def main(self, *args, standalone_mode=True, **kwargs):
        try:
            return super().main(*args, standalone_mode=False, **kwargs)
        except click.UsageError as e:
            console.print(f"[red]Error:[/red] {e.format_message()}")
            if e.ctx:
                console.print(f"[dim]Try [bold]{e.ctx.command_path} --help[/bold] for usage.[/dim]")
            sys.exit(2)
        except click.exceptions.Exit as e:
            sys.exit(e.code)
        except click.exceptions.Abort:
            console.print("\n[yellow]Aborted.[/yellow]")
            sys.exit(1)


def _current_user() -> str:
    return config.get_name() or getpass.getuser()


def _parse_date(ctx, param, value: str | None) -> datetime | None:
    if value is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise click.BadParameter("Expected format: YYYY-MM-DD or YYYY-MM-DD HH:MM")


def _date_range(
    days: int | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if days is not None:
        return db.days_range(days)
    return from_dt, to_dt


# ── Root group ─────────────────────────────────────────────────────────────────

@click.group(cls=RichGroup)
@click.version_option(package_name="my-blood-pressure", prog_name="mbp")
def cli():
    """Blood pressure and weight tracker."""


# ── log group ──────────────────────────────────────────────────────────────────

@cli.group(cls=RichGroup)
def log():
    """Log a new reading."""


# ── log bp ─────────────────────────────────────────────────────────────────────

@log.command(name="bp")
@click.argument("systolic", type=int)
@click.argument("diastolic", type=int)
@click.option("--pulse", "-p", type=int, default=None, help="Heart rate (bpm)")
@click.option("--note", "-n", default=None, help="Optional note")
@click.option("--device", default=None, help="Device or location name (e.g. 'home', 'pharmacy')")
@click.option("--date", "-d", default=None, callback=_parse_date, is_eager=False,
              help="Timestamp (YYYY-MM-DD or YYYY-MM-DD HH:MM), defaults to now")
def log_bp(systolic: int, diastolic: int, pulse: int | None, note: str | None,
           device: str | None, date: datetime | None):
    """Log a blood pressure reading (SYSTOLIC DIASTOLIC)."""
    try:
        result = validate.validate_bp(systolic, diastolic, pulse)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    for warning in result.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")

    reading = BPReading(
        systolic=result.systolic,
        diastolic=result.diastolic,
        pulse=result.pulse,
        note=note,
        device=device or config.get_bp_device(),
        username=_current_user(),
        timestamp=date or datetime.now(),
    )

    conn = db.connect()
    db.insert_bp(conn, reading)

    color = reading.category_color
    console.print(
        f"[green]Logged:[/green] "
        f"[{color}]{reading.systolic}/{reading.diastolic}[/{color}]"
        + (f"  pulse {reading.pulse}" if reading.pulse else "")
        + f"  — [{color}]{reading.category}[/{color}]"
    )


# ── log weight ─────────────────────────────────────────────────────────────────

@log.command(name="weight")
@click.argument("value", type=float)
@click.option("--note", "-n", default=None, help="Optional note")
@click.option("--device", default=None, help="Device or location name (e.g. 'home', 'pharmacy')")
@click.option("--date", "-d", default=None, callback=_parse_date, is_eager=False,
              help="Timestamp (YYYY-MM-DD or YYYY-MM-DD HH:MM), defaults to now")
def log_weight(value: float, note: str | None, device: str | None, date: datetime | None):
    """Log a weight reading."""
    unit = config.get_weight_unit()
    try:
        value_kg = validate.validate_weight(value, unit)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    reading = WeightReading(
        value_kg=value_kg,
        unit=unit,
        note=note,
        device=device or config.get_weight_device(),
        username=_current_user(),
        timestamp=date or datetime.now(),
    )

    conn = db.connect()
    db.insert_weight(conn, reading)
    console.print(f"[green]Logged:[/green] {value} {unit}")


# ── bp config ──────────────────────────────────────────────────────────────────

@cli.command(name="config")
@click.option("--name", default=None, help="Your name (used to identify readings)")
@click.option("--bp-device", default=None, help="Default BP monitor model (e.g. 'Omron M3')")
@click.option("--weight-device", default=None, help="Default scale model (e.g. 'Withings Body')")
@click.option(
    "--weight-unit",
    type=click.Choice(["kg", "lbs"], case_sensitive=False),
    help="Preferred weight unit",
)
@click.option(
    "--height-unit",
    type=click.Choice(["cm", "in"], case_sensitive=False),
    help="Preferred height unit",
)
@click.option(
    "--height",
    type=float,
    default=None,
    help="Your height (in the current height unit)",
)
def config_cmd(name: str | None, bp_device: str | None, weight_device: str | None,
               weight_unit: str | None, height_unit: str | None, height: float | None):
    """View or update configuration."""
    changed = False
    try:
        if bp_device:
            config.set_bp_device(bp_device)
            console.print(f"[green]Default BP device set to:[/green] {bp_device}")
            changed = True
        if weight_device:
            config.set_weight_device(weight_device)
            console.print(f"[green]Default weight device set to:[/green] {weight_device}")
            changed = True
        if name:
            config.set_name(name)
            console.print(f"[green]Name set to:[/green] {name}")
            changed = True
        if weight_unit:
            config.set_weight_unit(weight_unit.lower())
            console.print(f"[green]Weight unit set to:[/green] {weight_unit.lower()}")
            changed = True
        if height_unit:
            config.set_height_unit(height_unit.lower())
            console.print(f"[green]Height unit set to:[/green] {height_unit.lower()}")
            changed = True
        if height is not None:
            unit = height_unit.lower() if height_unit else config.get_height_unit()
            config.set_height(height, unit)
            console.print(f"[green]Height set to:[/green] {height} {unit}")
            changed = True
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if not changed:
        cfg = config.load_config()
        name_val = cfg.get("name") or f"{getpass.getuser()} [dim](system user, set with --name)[/dim]"
        console.print(f"Name:        [cyan]{name_val}[/cyan]")
        bp_dev = cfg.get("bp_device") or "[dim]not set[/dim]"
        console.print(f"BP device:   [cyan]{bp_dev}[/cyan]")
        w_dev = cfg.get("weight_device") or "[dim]not set[/dim]"
        console.print(f"Weight dev:  [cyan]{w_dev}[/cyan]")
        unit = cfg.get("weight_unit", "kg (default)")
        console.print(f"Weight unit: [cyan]{unit}[/cyan]")
        height_cm = cfg.get("height_cm")
        if height_cm is not None:
            h_unit = cfg.get("height_unit", "cm")
            display_h = round(height_cm / 2.54, 1) if h_unit == "in" else round(height_cm, 1)
            console.print(f"Height:      [cyan]{display_h} {h_unit}[/cyan]")
        else:
            console.print("Height:      [dim]not set[/dim]")
        console.print(f"Database:    [cyan]{db.get_db_path()}[/cyan]")


# ── bp report ─────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--days", "-d", type=int, default=None, help="Show last N days (default: all)")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--type", "metric", type=click.Choice(["bp", "weight", "all"]), default="all")
@click.option("--user", "-u", default=None, help="User name (default: current user)")
@click.option("--device", default=None, help="Filter by device name")
def report(days: int | None, from_date: datetime | None, to_date: datetime | None,
           metric: str, user: str | None, device: str | None):
    """Show readings in a table."""
    from_dt, to_dt = _date_range(days if not from_date else None, from_date, to_date)
    user = user or _current_user()
    conn = db.connect()

    if metric in ("bp", "all"):
        console.print("\n[bold]Blood Pressure[/bold]")
        readings = db.query_bp(conn, user, from_dt, to_dt, device=device)
        rpt.print_bp_table(readings)

    if metric in ("weight", "all"):
        console.print("\n[bold]Weight[/bold]")
        readings = db.query_weight(conn, user, from_dt, to_dt, device=device)
        rpt.print_weight_table(readings, height_cm=config.get_height_cm())


# ── bp stats ──────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--days", "-d", type=int, default=None, help="Show last N days (default: all)")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--type", "metric", type=click.Choice(["bp", "weight", "all"]), default="all")
@click.option("--user", "-u", default=None, help="User name (default: current user)")
@click.option("--device", default=None, help="Filter by device name")
def stats(days: int | None, from_date: datetime | None, to_date: datetime | None,
          metric: str, user: str | None, device: str | None):
    """Show summary statistics and trends."""
    from_dt, to_dt = _date_range(days if not from_date else None, from_date, to_date)
    user = user or _current_user()
    conn = db.connect()

    if metric in ("bp", "all"):
        console.print("\n[bold]Blood Pressure Stats[/bold]")
        readings = db.query_bp(conn, user, from_dt, to_dt, device=device)
        rpt.print_bp_stats(readings)

    if metric in ("weight", "all"):
        console.print("\n[bold]Weight Stats[/bold]")
        readings = db.query_weight(conn, user, from_dt, to_dt, device=device)
        rpt.print_weight_stats(readings, height_cm=config.get_height_cm())


# ── bp plot ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("metric", type=click.Choice(["bp", "weight", "bmi"]))
@click.option("--days", "-d", type=int, default=30, help="Show last N days (default: 30)")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--png",  is_flag=True, default=False, help="Export to PNG instead of terminal plot")
@click.option("--output", "-o", default=None, help="Output file path for PNG (optional)")
@click.option("--user", "-u", default=None, help="User name (default: current user)")
def plot(
    metric: str,
    days: int,
    from_date: datetime | None,
    to_date: datetime | None,
    png: bool,
    output: str | None,
    user: str | None,
):
    """Plot readings in the terminal or export to PNG."""
    from_dt, to_dt = _date_range(days if not from_date else None, from_date, to_date)
    user = user or _current_user()
    conn = db.connect()

    if metric == "bp":
        readings = db.query_bp(conn, user, from_dt, to_dt)
        if not readings:
            console.print("[dim]No blood pressure readings found for this period.[/dim]")
            return
        if png:
            out = Path(output) if output else Path(f"bp_{datetime.now().strftime('%Y%m%d')}.png")
            plt_mod.plot_bp_png(readings, out)
        else:
            plt_mod.plot_bp_terminal(readings)

    elif metric == "weight":
        readings = db.query_weight(conn, user, from_dt, to_dt)
        if not readings:
            console.print("[dim]No weight readings found for this period.[/dim]")
            return
        if png:
            out = Path(output) if output else Path(f"weight_{datetime.now().strftime('%Y%m%d')}.png")
            plt_mod.plot_weight_png(readings, out)
        else:
            plt_mod.plot_weight_terminal(readings)

    elif metric == "bmi":
        height_cm = config.get_height_cm()
        if height_cm is None:
            console.print(
                "[yellow]Tip:[/yellow] run "
                "[bold]mbp config --height-unit cm --height 175[/bold] to enable BMI"
            )
            return
        readings = db.query_weight(conn, user, from_dt, to_dt)
        if not readings:
            console.print("[dim]No weight readings found for this period.[/dim]")
            return
        if png:
            out = Path(output) if output else Path(f"bmi_{datetime.now().strftime('%Y%m%d')}.png")
            plt_mod.plot_bmi_png(readings, height_cm, out)
        else:
            plt_mod.plot_bmi_terminal(readings, height_cm)


# ── delete ─────────────────────────────────────────────────────────────────────

@cli.group(cls=RichGroup)
def delete():
    """Delete a reading by ID."""


@delete.command(name="bp")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def delete_bp(id: int, yes: bool):
    """Delete a blood pressure reading by ID."""
    if not yes:
        click.confirm(f"Delete BP reading {id}?", abort=True)
    conn = db.connect()
    if db.delete_bp(conn, id):
        console.print(f"[green]Deleted[/green] BP reading {id}.")
    else:
        console.print(f"[red]No BP reading found with ID {id}.[/red]")
        sys.exit(1)


@delete.command(name="weight")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def delete_weight(id: int, yes: bool):
    """Delete a weight reading by ID."""
    if not yes:
        click.confirm(f"Delete weight reading {id}?", abort=True)
    conn = db.connect()
    if db.delete_weight(conn, id):
        console.print(f"[green]Deleted[/green] weight reading {id}.")
    else:
        console.print(f"[red]No weight reading found with ID {id}.[/red]")
        sys.exit(1)


# ── export ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--days", "-d", type=int, default=None, help="Export last N days")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--type", "metric", type=click.Choice(["bp", "weight", "all"]), default="all")
@click.option("--output", "-o", default=None, help="Output CSV file (default: stdout)")
@click.option("--user", "-u", default=None, help="User name (default: current user)")
@click.option("--device", default=None, help="Filter by device name")
def export(days: int | None, from_date: datetime | None, to_date: datetime | None,
           metric: str, output: str | None, user: str | None, device: str | None):
    """Export readings to CSV."""
    import csv
    import io

    from_dt, to_dt = _date_range(days, from_date, to_date)
    user = user or _current_user()
    conn = db.connect()

    buf = io.StringIO()
    writer = csv.writer(buf)

    if metric in ("bp", "all"):
        writer.writerow(["type", "id", "timestamp", "username", "systolic", "diastolic", "pulse", "category", "device", "note"])
        for r in db.query_bp(conn, user, from_dt, to_dt, device=device):
            writer.writerow(["bp", r.id, r.timestamp.isoformat(),
                             r.username, r.systolic, r.diastolic, r.pulse or "", r.category, r.device or "", r.note or ""])

    if metric in ("weight", "all"):
        writer.writerow(["type", "id", "timestamp", "username", "value_kg", "unit", "device", "note"])
        for r in db.query_weight(conn, user, from_dt, to_dt, device=device):
            writer.writerow(["weight", r.id, r.timestamp.isoformat(),
                             r.username, r.value_kg, r.unit, r.device or "", r.note or ""])

    content = buf.getvalue()

    if output:
        Path(output).write_text(content)
        console.print(f"[green]Exported to[/green] {output}")
    else:
        click.echo(content, nl=False)


# ── import ─────────────────────────────────────────────────────────────────────

@cli.command(name="import")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
def import_cmd(input_file: str):
    """Import readings from a CSV file produced by mbp export."""
    import csv

    conn = db.connect()
    bp_count = weight_count = error_count = 0

    with open(input_file, newline="") as f:
        reader = csv.reader(f)
        for lineno, row in enumerate(reader, start=1):
            if not row or row[0] == "type":
                continue  # skip blank lines and header rows

            row_type = row[0]

            try:
                if row_type == "bp":
                    # type, id, timestamp, username, systolic, diastolic, pulse, category, device, note
                    _, _, timestamp, username, systolic, diastolic, pulse, _, device, note = row
                    reading = BPReading(
                        systolic=int(systolic),
                        diastolic=int(diastolic),
                        pulse=int(pulse) if pulse else None,
                        device=device or None,
                        note=note or None,
                        username=username,
                        timestamp=datetime.fromisoformat(timestamp),
                    )
                    db.insert_bp(conn, reading)
                    bp_count += 1

                elif row_type == "weight":
                    # type, id, timestamp, username, value_kg, unit, device, note
                    _, _, timestamp, username, value_kg, unit, device, note = row
                    reading = WeightReading(
                        value_kg=float(value_kg),
                        unit=unit,
                        device=device or None,
                        note=note or None,
                        username=username,
                        timestamp=datetime.fromisoformat(timestamp),
                    )
                    db.insert_weight(conn, reading)
                    weight_count += 1

                else:
                    console.print(f"[yellow]Line {lineno}:[/yellow] unknown type '{row_type}', skipping.")
                    error_count += 1

            except Exception as e:
                console.print(f"[yellow]Line {lineno}:[/yellow] skipped — {e}")
                error_count += 1

    console.print(f"[green]Imported:[/green] {bp_count} BP reading(s), {weight_count} weight reading(s).", end="")
    if error_count:
        console.print(f"  [yellow]{error_count} row(s) skipped.[/yellow]")
    else:
        console.print("")
