# bp — Blood Pressure & Weight Tracker

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
bp log 120 80

# Log with pulse
bp log 120 80 --pulse 65

# Log with a note
bp log 120 80 --pulse 65 --note "after coffee"
```

### Weight

```bash
# First time: set your preferred unit (once per user)
bp config --weight-unit kg     # or: lbs

# Log weight
bp weight 74.5
bp weight 74.5 --note "morning, before breakfast"
```

### View readings

```bash
# Recent readings (default: last 30 days)
bp report

# Specify a time range
bp report --days 90
bp report --from 2026-01-01 --to 2026-03-01

# Blood pressure only or weight only
bp report --type bp
bp report --type weight
```

### Statistics

```bash
bp stats            # summary: mean, min, max, trend for all metrics
bp stats --type bp
bp stats --type weight
```

### Plots

```bash
# Terminal plots (quick view)
bp plot bp           # systolic & diastolic over time
bp plot weight       # weight over time

# Export to PNG (for sharing)
bp plot bp --png
bp plot bp --png --output ~/Desktop/bp_march.png

bp plot weight --png
bp plot weight --png --output ~/Desktop/weight_march.png

# Time range applies to plots too
bp plot bp --days 90
bp plot bp --from 2026-01-01
```

## Configuration

User config is stored alongside the database. Set once:

```bash
bp config --weight-unit kg     # or lbs
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

`bp` will warn you if a reading falls into the Elevated or higher category.

## Project Structure

```
bp/
├── bp/
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
