import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mbp.models import BPReading, WeightReading


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Point every test to a fresh temporary database."""
    monkeypatch.setenv("MBP_DB", str(tmp_path / "test.db"))
    # Re-import db so get_db_path() picks up the new env var
    import importlib
    import mbp.db
    importlib.reload(mbp.db)
    yield
    importlib.reload(mbp.db)  # restore after test


def _conn():
    from mbp import db
    return db.connect()


def _bp(**kwargs):
    defaults = dict(systolic=120, diastolic=80, pulse=65, note=None, username="testuser")
    defaults.update(kwargs)
    return BPReading(**defaults)


def _weight(**kwargs):
    defaults = dict(value_kg=75.0, unit="kg", note=None, username="testuser")
    defaults.update(kwargs)
    return WeightReading(**defaults)


class TestBPInsertQuery:
    def test_insert_and_retrieve(self):
        from mbp import db
        conn = _conn()
        r = _bp()
        row_id = db.insert_bp(conn, r)
        assert row_id == 1

        rows = db.query_bp(conn, "testuser")
        assert len(rows) == 1
        assert rows[0].systolic == 120
        assert rows[0].diastolic == 80
        assert rows[0].pulse == 65

    def test_multiple_users_isolated(self):
        from mbp import db
        conn = _conn()
        db.insert_bp(conn, _bp(username="alice"))
        db.insert_bp(conn, _bp(username="bob"))

        alice = db.query_bp(conn, "alice")
        bob   = db.query_bp(conn, "bob")
        assert len(alice) == 1
        assert len(bob)   == 1

    def test_date_filter(self):
        from mbp import db
        conn = _conn()
        now = datetime.now()
        old = _bp(timestamp=now - timedelta(days=60))
        new = _bp(timestamp=now - timedelta(days=1))
        db.insert_bp(conn, old)
        db.insert_bp(conn, new)

        from_dt, to_dt = db.days_range(30)
        rows = db.query_bp(conn, "testuser", from_dt, to_dt)
        assert len(rows) == 1

    def test_note_stored(self):
        from mbp import db
        conn = _conn()
        db.insert_bp(conn, _bp(note="after exercise"))
        rows = db.query_bp(conn, "testuser")
        assert rows[0].note == "after exercise"


class TestWeightInsertQuery:
    def test_insert_and_retrieve(self):
        from mbp import db
        conn = _conn()
        db.insert_weight(conn, _weight())
        rows = db.query_weight(conn, "testuser")
        assert len(rows) == 1
        assert rows[0].value_kg == pytest.approx(75.0)
        assert rows[0].unit == "kg"

    def test_lbs_stored_as_kg(self):
        from mbp import db
        conn = _conn()
        value_kg = 165.0 / 2.20462
        db.insert_weight(conn, _weight(value_kg=value_kg, unit="lbs"))
        rows = db.query_weight(conn, "testuser")
        assert rows[0].value_kg == pytest.approx(value_kg, rel=1e-4)
        assert rows[0].unit == "lbs"

    def test_date_filter(self):
        from mbp import db
        conn = _conn()
        now = datetime.now()
        db.insert_weight(conn, _weight(timestamp=now - timedelta(days=90)))
        db.insert_weight(conn, _weight(timestamp=now - timedelta(days=5)))

        from_dt, to_dt = db.days_range(30)
        rows = db.query_weight(conn, "testuser", from_dt, to_dt)
        assert len(rows) == 1
