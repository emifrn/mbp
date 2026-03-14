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


def _current_user() -> str:
    return getpass.getuser()


def _parse_date(ctx, param, value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter("Expected format: YYYY-MM-DD")


def _date_range(
    days: int | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if days is not None:
        return db.days_range(days)
    return from_dt, to_dt


# ── Root group ─────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Blood pressure and weight tracker."""


# ── log group ──────────────────────────────────────────────────────────────────

@cli.group()
def log():
    """Log a new reading."""


# ── log bp ─────────────────────────────────────────────────────────────────────

@log.command(name="bp")
@click.argument("systolic", type=int)
@click.argument("diastolic", type=int)
@click.option("--pulse", "-p", type=int, default=None, help="Heart rate (bpm)")
@click.option("--note", "-n", default=None, help="Optional note")
def log_bp(systolic: int, diastolic: int, pulse: int | None, note: str | None):
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
        username=_current_user(),
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
def log_weight(value: float, note: str | None):
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
        username=_current_user(),
    )

    conn = db.connect()
    db.insert_weight(conn, reading)
    console.print(f"[green]Logged:[/green] {value} {unit}")


# ── bp config ──────────────────────────────────────────────────────────────────

@cli.command(name="config")
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
def config_cmd(weight_unit: str | None, height_unit: str | None, height: float | None):
    """View or update user configuration."""
    changed = False
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
    if not changed:
        cfg = config.load_config()
        unit = cfg.get("weight_unit", "kg (default)")
        console.print(f"Weight unit: [cyan]{unit}[/cyan]")
        height_cm = cfg.get("height_cm")
        if height_cm is not None:
            h_unit = cfg.get("height_unit", "cm")
            if h_unit == "in":
                display_h = round(height_cm / 2.54, 1)
            else:
                display_h = round(height_cm, 1)
            console.print(f"Height:      [cyan]{display_h} {h_unit}[/cyan]")
        else:
            console.print("Height:      [dim]not set[/dim]")
        console.print(f"Database:    [cyan]{db.get_db_path()}[/cyan]")


# ── bp report ─────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--days", "-d", type=int, default=30, help="Show last N days (default: 30)")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--type", "metric", type=click.Choice(["bp", "weight", "all"]), default="all")
def report(days: int, from_date: datetime | None, to_date: datetime | None, metric: str):
    """Show recent readings in a table."""
    from_dt, to_dt = _date_range(days if not from_date else None, from_date, to_date)
    user = _current_user()
    conn = db.connect()

    if metric in ("bp", "all"):
        console.print("\n[bold]Blood Pressure[/bold]")
        readings = db.query_bp(conn, user, from_dt, to_dt)
        rpt.print_bp_table(readings)

    if metric in ("weight", "all"):
        console.print("\n[bold]Weight[/bold]")
        readings = db.query_weight(conn, user, from_dt, to_dt)
        rpt.print_weight_table(readings, height_cm=config.get_height_cm())


# ── bp stats ──────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--days", "-d", type=int, default=30, help="Show last N days (default: 30)")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--type", "metric", type=click.Choice(["bp", "weight", "all"]), default="all")
def stats(days: int, from_date: datetime | None, to_date: datetime | None, metric: str):
    """Show summary statistics and trends."""
    from_dt, to_dt = _date_range(days if not from_date else None, from_date, to_date)
    user = _current_user()
    conn = db.connect()

    if metric in ("bp", "all"):
        console.print("\n[bold]Blood Pressure Stats[/bold]")
        readings = db.query_bp(conn, user, from_dt, to_dt)
        rpt.print_bp_stats(readings)

    if metric in ("weight", "all"):
        console.print("\n[bold]Weight Stats[/bold]")
        readings = db.query_weight(conn, user, from_dt, to_dt)
        rpt.print_weight_stats(readings, height_cm=config.get_height_cm())


# ── bp plot ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("metric", type=click.Choice(["bp", "weight", "bmi"]))
@click.option("--days", "-d", type=int, default=30, help="Show last N days (default: 30)")
@click.option("--from", "from_date", default=None, callback=_parse_date, help="Start date YYYY-MM-DD")
@click.option("--to",   "to_date",   default=None, callback=_parse_date, help="End date YYYY-MM-DD")
@click.option("--png",  is_flag=True, default=False, help="Export to PNG instead of terminal plot")
@click.option("--output", "-o", default=None, help="Output file path for PNG (optional)")
def plot(
    metric: str,
    days: int,
    from_date: datetime | None,
    to_date: datetime | None,
    png: bool,
    output: str | None,
):
    """Plot readings in the terminal or export to PNG."""
    from_dt, to_dt = _date_range(days if not from_date else None, from_date, to_date)
    user = _current_user()
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
