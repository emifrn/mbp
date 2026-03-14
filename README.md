# mbp — Blood Pressure & Weight Tracker

A minimal CLI to log and visualize blood pressure and weight over time.
Data lives in a local SQLite database. No cloud, no accounts.

## Quickstart

```bash
pip install -e .
mbp config --name "Alice" --weight-unit kg --height-unit cm --height 170
mbp log bp 120 80 --pulse 65
mbp report
```

## Features

- Log blood pressure (systolic / diastolic / pulse) and weight
- Track the device/monitor used for each reading
- BMI computed automatically from weight readings once height is set
- Color-coded health categories (AHA for BP, WHO for BMI)
- 7-day rolling average column in BP report
- Terminal plots and publication-quality PNG export
- Summary statistics with trend detection
- Filter any view by date range or device
- Backfill past readings with `--date`
- Delete individual readings by ID
- Export to CSV and re-import
- Input validation with auto-correction (e.g. swapped systolic/diastolic)

## Installation

```bash
git clone https://github.com/emifrn/mbp.git
cd mbp
pip install -e .
```

**Dependencies:** `click`, `rich`, `plotext`, `matplotlib`

## Command Reference

| Command | Description |
|---|---|
| `mbp log bp SYSTOLIC DIASTOLIC` | Log a blood pressure reading |
| `mbp log weight VALUE` | Log a weight reading |
| `mbp report` | Show readings in a table |
| `mbp stats` | Show summary statistics and trends |
| `mbp plot bp\|weight\|bmi` | Plot in terminal or export to PNG |
| `mbp delete bp\|weight ID` | Delete a reading by ID |
| `mbp export` | Export readings to CSV |
| `mbp import FILE` | Import readings from a CSV file |
| `mbp config` | View or update configuration |
| `mbp --version` | Show version |

## Usage

### Log blood pressure

```bash
mbp log bp 120 80
mbp log bp 120 80 --pulse 65
mbp log bp 120 80 --pulse 65 --note "after rest"
mbp log bp 120 80 --device "Omron M3"        # override default device
mbp log bp 120 80 --date "2026-03-10"         # backfill a past reading
mbp log bp 120 80 --date "2026-03-10 08:30"
```

### Log weight

```bash
mbp log weight 74.5
mbp log weight 74.5 --note "morning, before breakfast"
mbp log weight 74.5 --device "Withings Body"
mbp log weight 74.5 --date "2026-03-10"
```

### Report

```bash
mbp report                          # all readings
mbp report --type bp                # blood pressure only
mbp report --type weight            # weight only (shows BMI if height is set)
mbp report --days 30                # last 30 days
mbp report --from 2026-01-01 --to 2026-03-01
mbp report --device "Omron M3"      # filter by device
```

### Statistics

```bash
mbp stats                           # mean, min, max, trend for all metrics
mbp stats --type bp
mbp stats --type weight
mbp stats --days 90
mbp stats --device "Omron M3"
```

### Plots

```bash
# Terminal (quick view)
mbp plot bp
mbp plot weight
mbp plot bmi                        # requires height to be configured

# PNG export
mbp plot bp --png
mbp plot bp --png --output ~/Desktop/bp_march.png
mbp plot weight --png
mbp plot bmi --png

# Time range
mbp plot bp --days 90
mbp plot bp --from 2026-01-01
```

### Delete

Run `mbp report` to find the ID of the reading to remove.

```bash
mbp delete bp 42
mbp delete weight 7
mbp delete bp 42 --yes              # skip confirmation prompt
```

### Export & Import

```bash
mbp export                          # all readings to stdout
mbp export --type bp --output bp.csv
mbp export --type weight --output weight.csv
mbp export --days 90 --output recent.csv
mbp export --device "Omron M3" --output omron.csv

mbp import backup.csv               # re-import from any exported CSV
```

## Configuration

```bash
mbp config                                  # view current settings
mbp config --name "Alice"                   # display name (defaults to system user)
mbp config --bp-device "Omron M3"          # default BP monitor
mbp config --weight-device "Withings Body" # default scale
mbp config --weight-unit kg                # or lbs
mbp config --height-unit cm               # or in
mbp config --height 175
```

## Database

By default, the SQLite database and config are stored in:

```
~/.local/share/mbp/mbp.db
~/.local/share/mbp/config.json
```

Override with the `MBP_DB` environment variable — config follows automatically:

```bash
export MBP_DB=~/work/mbp.db        # db and config both live in ~/work/
```

This is also how multiple users share a machine: each sets their own `MBP_DB`.

## Blood Pressure Reference (AHA)

| Category | Systolic | | Diastolic |
|---|---|---|---|
| Normal | < 120 | and | < 80 |
| Elevated | 120–129 | and | < 80 |
| High Stage 1 | 130–139 | or | 80–89 |
| High Stage 2 | ≥ 140 | or | ≥ 90 |
| Crisis | > 180 | or | > 120 |

## BMI Reference (WHO)

| Category | BMI |
|---|---|
| Underweight | < 18.5 |
| Normal | 18.5 – 24.9 |
| Overweight | 25 – 29.9 |
| Obese | ≥ 30 |

## Project Structure

```
mbp/
├── mbp/
│   ├── cli.py          # commands
│   ├── db.py           # SQLite schema & queries
│   ├── models.py       # BPReading & WeightReading dataclasses
│   ├── validate.py     # input validation & auto-correction
│   ├── report.py       # rich table formatting
│   ├── plot.py         # terminal (plotext) & PNG (matplotlib) plots
│   └── config.py       # configuration (name, units, height, devices)
├── tests/
│   ├── test_cli.py
│   ├── test_db.py
│   └── test_validate.py
├── pyproject.toml
└── README.md
```

## License

MIT — © 2026 emifrn
