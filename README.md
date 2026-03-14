# mbp — Blood Pressure & Weight Tracker

A minimal CLI to log and visualize blood pressure and weight over time.
Data lives in a local SQLite database. No cloud, no accounts.

## Features

- Log blood pressure (systolic / diastolic / pulse)
- Log weight in your preferred unit (kg or lbs, set once per user)
- Track height and compute BMI automatically from weight readings
- View readings in a formatted table with color-coded health categories
- Plot trends in the terminal with [plotext](https://github.com/piccolomo/plotext)
- Export publication-quality PNG charts (for sharing with your doctor) via matplotlib
- Per-user configuration and data isolation
- Auto-timestamp on every record
- Input validation with auto-correction (swapped systolic/diastolic, out-of-range values)
- Optional notes on any reading

## Installation

```bash
git clone https://github.com/yourname/my-blood-pressure.git
cd my-blood-pressure
pip install -e .
```

### Dependencies

```
click
rich
plotext
matplotlib
```

## Usage

### Blood pressure

```bash
# Log a reading (systolic diastolic)
mbp log 120 80

# Log with pulse
mbp log 120 80 --pulse 65

# Log with a note
mbp log 120 80 --pulse 65 --note "after coffee"
```

### Weight

```bash
# First time: set your preferred unit (once per user)
mbp config --weight-unit kg     # or: lbs

# Log weight
mbp weight 74.5
mbp weight 74.5 --note "morning, before breakfast"
```

### BMI

BMI is computed automatically from your weight readings once you set your height:

```bash
# Set height unit and value (once per user)
mbp config --height-unit cm --height 175
# or for imperial users:
mbp config --height-unit in --height 71

# BMI appears automatically in weight report and stats
mbp report --type weight
mbp stats --type weight

# Plot BMI over time
mbp plot bmi
mbp plot bmi --png --output ~/Desktop/bmi_march.png
```

### View readings

```bash
# Recent readings (default: last 30 days)
mbp report

# Specify a time range
mbp report --days 90
mbp report --from 2026-01-01 --to 2026-03-01

# Blood pressure only or weight only
mbp report --type bp
mbp report --type weight
```

### Statistics

```bash
mbp stats            # summary: mean, min, max, trend for all metrics
mbp stats --type bp
mbp stats --type weight
```

### Plots

```bash
# Terminal plots (quick view)
mbp plot bp           # systolic & diastolic over time
mbp plot weight       # weight over time
mbp plot bmi          # BMI over time (requires height to be configured)

# Export to PNG (for sharing)
mbp plot bp --png
mbp plot bp --png --output ~/Desktop/bp_march.png

mbp plot weight --png
mbp plot weight --png --output ~/Desktop/weight_march.png

mbp plot bmi --png
mbp plot bmi --png --output ~/Desktop/bmi_march.png

# Time range applies to all plots
mbp plot bp --days 90
mbp plot bp --from 2026-01-01
```

## Configuration

```bash
mbp config --name "John"        # set your display name (defaults to system user)
mbp config --weight-unit kg     # or lbs
mbp config --height-unit cm     # or in (inches)
mbp config --height 175         # your height in the configured unit
mbp config                      # view current settings
```

## Database

By default, the SQLite database is stored at:

```
~/.local/share/mbp/mbp.db
```

Override with the `MBP_DB` environment variable:

```bash
export MBP_DB=/path/to/my.db
```

## Blood Pressure Reference (AHA)

| Category | Systolic | | Diastolic |
|---|---|---|---|
| Normal | < 120 | and | < 80 |
| Elevated | 120–129 | and | < 80 |
| High Stage 1 | 130–139 | or | 80–89 |
| High Stage 2 | ≥ 140 | or | ≥ 90 |
| Crisis | > 180 | or | > 120 |

`mbp` will warn you if a reading falls into the Elevated or higher category.

## BMI Reference (WHO)

| Category | BMI |
|---|---|
| Underweight | < 18.5 |
| Normal | 18.5 – 24.9 |
| Overweight | 25 – 29.9 |
| Obese | ≥ 30 |

## Project Structure

```
my-blood-pressure/
├── mbp/
│   ├── __init__.py
│   ├── cli.py          # click commands
│   ├── db.py           # SQLite schema & queries
│   ├── models.py       # dataclasses for BP & weight readings, BMI logic
│   ├── validate.py     # input validation & auto-correction
│   ├── plot.py         # plotext (terminal) + matplotlib (PNG)
│   ├── report.py       # rich table formatting
│   └── config.py       # per-user config (name, weight unit, height unit, height)
├── tests/
│   ├── test_validate.py
│   ├── test_db.py
│   └── test_cli.py
├── pyproject.toml
└── README.md
```

## License

MIT
