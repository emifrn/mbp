from __future__ import annotations

from datetime import datetime
from pathlib import Path

from mbp.models import BPReading, WeightReading

# ── Terminal plots (plotext) ───────────────────────────────────────────────────

def plot_bp_terminal(readings: list[BPReading]) -> None:
    if not readings:
        print("No blood pressure readings to plot.")
        return

    import plotext as plt

    dates = [r.timestamp.strftime("%m-%d") for r in readings]
    systolic  = [r.systolic  for r in readings]
    diastolic = [r.diastolic for r in readings]
    xs = list(range(len(dates)))
    step = max(1, len(dates) // 10)

    plt.clf()
    plt.theme("dark")
    plt.title("Blood Pressure over Time")
    plt.xlabel("Date")
    plt.ylabel("mmHg")

    plt.plot(xs, systolic,  label="Systolic",  marker="dot")
    plt.plot(xs, diastolic, label="Diastolic", marker="dot")
    plt.xticks(xs[::step], dates[::step])

    # Reference lines
    plt.hline(120, color="yellow+")   # elevated threshold
    plt.hline(80,  color="yellow+")

    plt.show()


def plot_weight_terminal(readings: list[WeightReading]) -> None:
    if not readings:
        print("No weight readings to plot.")
        return

    import plotext as plt

    display_unit = readings[-1].unit
    dates = [r.timestamp.strftime("%m-%d") for r in readings]
    values = [
        round(r.value_kg * 2.20462, 1) if display_unit == "lbs" else round(r.value_kg, 1)
        for r in readings
    ]
    xs = list(range(len(dates)))
    step = max(1, len(dates) // 10)

    plt.clf()
    plt.theme("dark")
    plt.title(f"Weight over Time ({display_unit})")
    plt.xlabel("Date")
    plt.ylabel(display_unit)

    plt.plot(xs, values, label="Weight", marker="dot")
    plt.xticks(xs[::step], dates[::step])
    plt.show()


# ── PNG export (matplotlib) ────────────────────────────────────────────────────

def plot_bp_png(readings: list[BPReading], output: Path) -> None:
    if not readings:
        print("No blood pressure readings to plot.")
        return

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    dates     = [r.timestamp for r in readings]
    systolic  = [r.systolic  for r in readings]
    diastolic = [r.diastolic for r in readings]

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(dates, systolic,  "o-", label="Systolic",  color="#e74c3c", linewidth=1.5, markersize=4)
    ax.plot(dates, diastolic, "o-", label="Diastolic", color="#3498db", linewidth=1.5, markersize=4)

    # AHA reference bands
    ax.axhspan(0,   80,  alpha=0.04, color="green",  label="Normal diastolic")
    ax.axhline(120, color="#f39c12", linewidth=0.8, linestyle="--", label="Elevated threshold (120)")
    ax.axhline(80,  color="#f39c12", linewidth=0.8, linestyle="--")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.set_title("Blood Pressure over Time", fontsize=14, fontweight="bold")
    ax.set_ylabel("mmHg")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved to {output}")


def plot_bmi_terminal(readings: list[WeightReading], height_cm: float) -> None:
    if not readings:
        print("No weight readings to plot.")
        return

    import plotext as plt

    dates = [r.timestamp.strftime("%m-%d") for r in readings]
    bmi_vals = [r.bmi(height_cm) for r in readings]
    xs = list(range(len(dates)))
    step = max(1, len(dates) // 10)

    plt.clf()
    plt.theme("dark")
    plt.title("BMI over Time")
    plt.xlabel("Date")
    plt.ylabel("BMI")

    plt.plot(xs, bmi_vals, label="BMI", marker="dot")
    plt.xticks(xs[::step], dates[::step])

    # WHO reference lines
    plt.hline(18.5, color="yellow+")   # Underweight threshold
    plt.hline(25.0, color="yellow+")   # Overweight threshold
    plt.hline(30.0, color="red+")      # Obese threshold

    plt.show()


def plot_bmi_png(readings: list[WeightReading], height_cm: float, output: Path) -> None:
    if not readings:
        print("No weight readings to plot.")
        return

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    dates    = [r.timestamp for r in readings]
    bmi_vals = [r.bmi(height_cm) for r in readings]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, bmi_vals, "o-", color="#9b59b6", linewidth=1.5, markersize=4, label="BMI")

    # WHO reference lines
    ax.axhline(18.5, color="#f39c12", linewidth=0.8, linestyle="--", label="Underweight (18.5)")
    ax.axhline(25.0, color="#e67e22", linewidth=0.8, linestyle="--", label="Overweight (25)")
    ax.axhline(30.0, color="#e74c3c", linewidth=0.8, linestyle="--", label="Obese (30)")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.set_title("BMI over Time", fontsize=14, fontweight="bold")
    ax.set_ylabel("BMI")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved to {output}")


def plot_weight_png(readings: list[WeightReading], output: Path) -> None:
    if not readings:
        print("No weight readings to plot.")
        return

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    display_unit = readings[-1].unit
    dates  = [r.timestamp for r in readings]
    values = [
        round(r.value_kg * 2.20462, 1) if display_unit == "lbs" else round(r.value_kg, 1)
        for r in readings
    ]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, values, "o-", color="#2ecc71", linewidth=1.5, markersize=4, label="Weight")

    # Trend line
    if len(values) >= 3:
        import numpy as np
        x_num = mdates.date2num(dates)
        coeffs = np.polyfit(x_num, values, 1)
        trend = np.poly1d(coeffs)(x_num)
        ax.plot(dates, trend, "--", color="#95a5a6", linewidth=1, label="Trend")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.set_title(f"Weight over Time ({display_unit})", fontsize=14, fontweight="bold")
    ax.set_ylabel(display_unit)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved to {output}")
