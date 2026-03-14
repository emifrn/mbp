import importlib
import pytest
from click.testing import CliRunner

from mbp.cli import cli


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BP_DB", str(tmp_path / "test.db"))
    # Also force a known username
    monkeypatch.setattr("mbp.cli._current_user", lambda: "testuser")
    importlib.reload(importlib.import_module("mbp.db"))
    yield
    importlib.reload(importlib.import_module("mbp.db"))


@pytest.fixture
def runner():
    return CliRunner()


class TestLogCommand:
    def test_basic_log(self, runner):
        result = runner.invoke(cli, ["log", "115", "75"])
        assert result.exit_code == 0
        assert "115/75" in result.output
        assert "Normal" in result.output

    def test_log_with_pulse(self, runner):
        result = runner.invoke(cli, ["log", "120", "80", "--pulse", "65"])
        assert result.exit_code == 0
        assert "pulse 65" in result.output

    def test_log_with_note(self, runner):
        result = runner.invoke(cli, ["log", "120", "80", "--note", "after rest"])
        assert result.exit_code == 0

    def test_log_swapped_auto_corrects(self, runner):
        result = runner.invoke(cli, ["log", "80", "120"])
        assert result.exit_code == 0
        assert "swapped" in result.output.lower()
        assert "120/80" in result.output

    def test_log_invalid_systolic(self, runner):
        result = runner.invoke(cli, ["log", "400", "80"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_high_category_shown(self, runner):
        result = runner.invoke(cli, ["log", "145", "95"])
        assert "High Stage 2" in result.output


class TestWeightCommand:
    def test_weight_kg(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        result = runner.invoke(cli, ["weight", "75.5"])
        assert result.exit_code == 0
        assert "75.5 kg" in result.output

    def test_weight_lbs(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "lbs"])
        result = runner.invoke(cli, ["weight", "165.0"])
        assert result.exit_code == 0
        assert "165.0 lbs" in result.output

    def test_weight_invalid(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        result = runner.invoke(cli, ["weight", "5.0"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestReportCommand:
    def test_report_empty(self, runner):
        result = runner.invoke(cli, ["report"])
        assert result.exit_code == 0
        assert "No" in result.output

    def test_report_shows_readings(self, runner):
        runner.invoke(cli, ["log", "120", "80"])
        runner.invoke(cli, ["log", "125", "85"])
        result = runner.invoke(cli, ["report", "--type", "bp"])
        assert result.exit_code == 0
        assert "120" in result.output
        assert "125" in result.output

    def test_report_weight_only(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        runner.invoke(cli, ["weight", "74.0"])
        result = runner.invoke(cli, ["report", "--type", "weight"])
        assert result.exit_code == 0
        assert "74.0" in result.output


class TestStatsCommand:
    def test_stats_empty(self, runner):
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0

    def test_stats_bp(self, runner):
        runner.invoke(cli, ["log", "120", "80"])
        runner.invoke(cli, ["log", "130", "85"])
        result = runner.invoke(cli, ["stats", "--type", "bp"])
        assert result.exit_code == 0
        assert "125" in result.output  # avg systolic


class TestConfigCommand:
    def test_set_weight_unit(self, runner):
        result = runner.invoke(cli, ["config", "--weight-unit", "lbs"])
        assert result.exit_code == 0
        assert "lbs" in result.output

    def test_view_config(self, runner):
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "Weight unit" in result.output
