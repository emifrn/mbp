import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from bp.models import BPReading, WeightReading

_DEFAULT_DB = Path.home() / ".local" / "share" / "bp" / "bp.db"


def get_db_path() -> Path:
    env = os.environ.get("BP_DB")
    return Path(env) if env else _DEFAULT_DB


def connect() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bp_readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL,
            systolic    INTEGER NOT NULL,
            diastolic   INTEGER NOT NULL,
            pulse       INTEGER,
            note        TEXT,
            timestamp   TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS weight_readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL,
            value_kg    REAL    NOT NULL,
            unit        TEXT    NOT NULL DEFAULT 'kg',
            note        TEXT,
            timestamp   TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_bp_user_ts
            ON bp_readings(username, timestamp);

        CREATE INDEX IF NOT EXISTS idx_weight_user_ts
            ON weight_readings(username, timestamp);
    """)
    conn.commit()


# ── BP ────────────────────────────────────────────────────────────────────────

def insert_bp(conn: sqlite3.Connection, r: BPReading) -> int:
    cur = conn.execute(
        """INSERT INTO bp_readings (username, systolic, diastolic, pulse, note, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (r.username, r.systolic, r.diastolic, r.pulse, r.note,
         r.timestamp.isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def query_bp(
    conn: sqlite3.Connection,
    username: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[BPReading]:
    from_dt = from_dt or datetime.min
    to_dt = to_dt or datetime.max
    rows = conn.execute(
        """SELECT * FROM bp_readings
           WHERE username = ?
             AND timestamp >= ?
             AND timestamp <= ?
           ORDER BY timestamp""",
        (username, from_dt.isoformat(), to_dt.isoformat()),
    ).fetchall()
    return [_row_to_bp(r) for r in rows]


def _row_to_bp(row: sqlite3.Row) -> BPReading:
    return BPReading(
        id=row["id"],
        username=row["username"],
        systolic=row["systolic"],
        diastolic=row["diastolic"],
        pulse=row["pulse"],
        note=row["note"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
    )


# ── Weight ────────────────────────────────────────────────────────────────────

def insert_weight(conn: sqlite3.Connection, r: WeightReading) -> int:
    cur = conn.execute(
        """INSERT INTO weight_readings (username, value_kg, unit, note, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (r.username, r.value_kg, r.unit, r.note, r.timestamp.isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def query_weight(
    conn: sqlite3.Connection,
    username: str,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[WeightReading]:
    from_dt = from_dt or datetime.min
    to_dt = to_dt or datetime.max
    rows = conn.execute(
        """SELECT * FROM weight_readings
           WHERE username = ?
             AND timestamp >= ?
             AND timestamp <= ?
           ORDER BY timestamp""",
        (username, from_dt.isoformat(), to_dt.isoformat()),
    ).fetchall()
    return [_row_to_weight(r) for r in rows]


def _row_to_weight(row: sqlite3.Row) -> WeightReading:
    return WeightReading(
        id=row["id"],
        username=row["username"],
        value_kg=row["value_kg"],
        unit=row["unit"],
        note=row["note"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def days_range(days: int) -> tuple[datetime, datetime]:
    to_dt = datetime.now()
    from_dt = to_dt - timedelta(days=days)
    return from_dt, to_dt
