# mbp — Blood Pressure & Weight Tracker

A minimal CLI to log and visualize blood pressure and weight over time.
Data lives in a local SQLite database. No cloud, no accounts.

## Features

- Log blood pressure (systolic / diastolic / pulse)
- Log weight in your preferred unit (kg or lbs, set once per user)
- View readings in a formatted table
- Plot trends in the terminal with [plotext](https://github.com/piccolomo/plotext)
- Export publication-quality PNG charts (for sharing with your doctor) via matplotlib
- Per-user configuration and data isolation
- Auto-timestamp on every record
- Input validation with auto-correction (swapped systolic/diastolic, out-of-range values)
- Optional notes on any reading

## Installation

```bash
git clone https://github.com/yourname/bp.git
cd bp
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

# Export to PNG (for sharing)
mbp plot bp --png
mbp plot bp --png --output ~/Desktop/bp_march.png

mbp plot weight --png
mbp plot weight --png --output ~/Desktop/weight_march.png

# Time range applies to plots too
mbp plot bp --days 90
mbp plot bp --from 2026-01-01
```

## Configuration

User config is stored alongside the database. Set once:

```bash
mbp config --weight-unit kg     # or lbs
```

## Database

By default, the SQLite database is stored at:

```
~/.local/share/bp/bp.db
```

Override with the `BP_DB` environment variable:

```bash
export BP_DB=/path/to/my.db
```

## Blood Pressure Reference

| Category | Systolic | | Diastolic |
|---|---|---|---|
| Normal | < 120 | and | < 80 |
| Elevated | 120–129 | and | < 80 |
| High Stage 1 | 130–139 | or | 80–89 |
| High Stage 2 | ≥ 140 | or | ≥ 90 |
| Crisis | > 180 | or | > 120 |

`mbp` will warn you if a reading falls into the Elevated or higher category.

## Project Structure

```
my-blood-pressure/
├── mbp/
│   ├── __init__.py
│   ├── cli.py          # click commands
│   ├── db.py           # SQLite schema & queries
│   ├── models.py       # dataclasses for BP & weight readings
│   ├── validate.py     # input validation & auto-correction
│   ├── plot.py         # plotext (terminal) + matplotlib (PNG)
│   ├── report.py       # rich table formatting
│   └── config.py       # per-user config (weight unit, etc.)
├── tests/
│   ├── test_validate.py
│   ├── test_db.py
│   └── test_cli.py
├── pyproject.toml
└── README.md
```

## License

MIT
