from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich import box

from bp.models import BPReading, WeightReading

console = Console()


def print_bp_table(readings: list[BPReading]) -> None:
    if not readings:
        console.print("[dim]No blood pressure readings found.[/dim]")
        return

    table = Table(box=box.ROUNDED, show_lines=False, header_style="bold cyan")
    table.add_column("Date", style="dim", min_width=16)
    table.add_column("Systolic", justify="right")
    table.add_column("Diastolic", justify="right")
    table.add_column("Pulse", justify="right")
    table.add_column("Category", min_width=14)
    table.add_column("Note")

    for r in readings:
        color = r.category_color
        table.add_row(
            r.timestamp.strftime("%Y-%m-%d %H:%M"),
            f"[{color}]{r.systolic}[/{color}]",
            f"[{color}]{r.diastolic}[/{color}]",
            str(r.pulse) if r.pulse is not None else "—",
            f"[{color}]{r.category}[/{color}]",
            r.note or "",
        )

    console.print(table)
    console.print(f"[dim]{len(readings)} reading(s)[/dim]")


def print_weight_table(readings: list[WeightReading]) -> None:
    if not readings:
        console.print("[dim]No weight readings found.[/dim]")
        return

    # Use the unit from the most recent reading as the display unit
    display_unit = readings[-1].unit

    table = Table(box=box.ROUNDED, show_lines=False, header_style="bold cyan")
    table.add_column("Date", style="dim", min_width=16)
    table.add_column(f"Weight ({display_unit})", justify="right")
    table.add_column("Note")

    for r in readings:
        table.add_row(
            r.timestamp.strftime("%Y-%m-%d %H:%M"),
            str(r.display_value()) if r.unit == display_unit
            else str(round(r.value_kg * 2.20462, 1) if display_unit == "lbs" else round(r.value_kg, 1)),
            r.note or "",
        )

    console.print(table)
    console.print(f"[dim]{len(readings)} reading(s)[/dim]")


def print_bp_stats(readings: list[BPReading]) -> None:
    if not readings:
        console.print("[dim]No blood pressure readings found.[/dim]")
        return

    sys_vals = [r.systolic for r in readings]
    dia_vals = [r.diastolic for r in readings]
    pulse_vals = [r.pulse for r in readings if r.pulse is not None]

    def _stats(vals: list[int]) -> tuple[float, int, int]:
        return round(sum(vals) / len(vals), 1), min(vals), max(vals)

    sys_avg, sys_min, sys_max = _stats(sys_vals)
    dia_avg, dia_min, dia_max = _stats(dia_vals)

    table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", show_edge=False)
    table.add_column("Metric")
    table.add_column("Avg", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")

    table.add_row("Systolic",  str(sys_avg), str(sys_min), str(sys_max))
    table.add_row("Diastolic", str(dia_avg), str(dia_min), str(dia_max))
    if pulse_vals:
        p_avg, p_min, p_max = _stats(pulse_vals)
        table.add_row("Pulse", str(p_avg), str(p_min), str(p_max))

    console.print(table)
    console.print(f"[dim]Based on {len(readings)} reading(s)[/dim]")

    # Trend: compare first half vs second half average
    if len(readings) >= 4:
        mid = len(readings) // 2
        first_avg = sum(r.systolic for r in readings[:mid]) / mid
        second_avg = sum(r.systolic for r in readings[mid:]) / (len(readings) - mid)
        delta = round(second_avg - first_avg, 1)
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        color = "red" if delta > 2 else ("green" if delta < -2 else "yellow")
        console.print(
            f"Systolic trend: [{color}]{arrow} {abs(delta):+.1f} mmHg[/{color}] "
            f"(first half avg {first_avg:.1f} → second half avg {second_avg:.1f})"
        )


def print_weight_stats(readings: list[WeightReading]) -> None:
    if not readings:
        console.print("[dim]No weight readings found.[/dim]")
        return

    display_unit = readings[-1].unit
    vals = [
        r.value_kg * 2.20462 if display_unit == "lbs" else r.value_kg
        for r in readings
    ]
    avg = round(sum(vals) / len(vals), 1)
    low = round(min(vals), 1)
    high = round(max(vals), 1)

    table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", show_edge=False)
    table.add_column("Metric")
    table.add_column(f"Weight ({display_unit})", justify="right")
    table.add_row("Average", str(avg))
    table.add_row("Min",     str(low))
    table.add_row("Max",     str(high))

    console.print(table)
    console.print(f"[dim]Based on {len(readings)} reading(s)[/dim]")

    if len(readings) >= 2:
        delta = round(vals[-1] - vals[0], 1)
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        color = "red" if delta > 0 else ("green" if delta < 0 else "yellow")
        first_dt = readings[0].timestamp.strftime("%Y-%m-%d")
        last_dt = readings[-1].timestamp.strftime("%Y-%m-%d")
        console.print(
            f"Change since {first_dt}: [{color}]{arrow} {delta:+.1f} {display_unit}[/{color}] "
            f"(to {last_dt})"
        )
