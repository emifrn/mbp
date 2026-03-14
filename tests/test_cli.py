import importlib
import pytest
from click.testing import CliRunner

from mbp.cli import cli


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MBP_DB", str(tmp_path / "test.db"))
    # Also force a known username
    monkeypatch.setattr("mbp.cli._current_user", lambda: "testuser")
    importlib.reload(importlib.import_module("mbp.db"))
    yield
    importlib.reload(importlib.import_module("mbp.db"))


@pytest.fixture
def runner():
    return CliRunner()


class TestLogBpCommand:
    def test_basic_log(self, runner):
        result = runner.invoke(cli, ["log", "bp", "115", "75"])
        assert result.exit_code == 0
        assert "115/75" in result.output
        assert "Normal" in result.output

    def test_log_with_pulse(self, runner):
        result = runner.invoke(cli, ["log", "bp", "120", "80", "--pulse", "65"])
        assert result.exit_code == 0
        assert "pulse 65" in result.output

    def test_log_with_note(self, runner):
        result = runner.invoke(cli, ["log", "bp", "120", "80", "--note", "after rest"])
        assert result.exit_code == 0

    def test_log_swapped_auto_corrects(self, runner):
        result = runner.invoke(cli, ["log", "bp", "80", "120"])
        assert result.exit_code == 0
        assert "swapped" in result.output.lower()
        assert "120/80" in result.output

    def test_log_invalid_systolic(self, runner):
        result = runner.invoke(cli, ["log", "bp", "400", "80"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_high_category_shown(self, runner):
        result = runner.invoke(cli, ["log", "bp", "145", "95"])
        assert "High Stage 2" in result.output


class TestLogWeightCommand:
    def test_weight_kg(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        result = runner.invoke(cli, ["log", "weight", "75.5"])
        assert result.exit_code == 0
        assert "75.5 kg" in result.output

    def test_weight_lbs(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "lbs"])
        result = runner.invoke(cli, ["log", "weight", "165.0"])
        assert result.exit_code == 0
        assert "165.0 lbs" in result.output

    def test_weight_invalid(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        result = runner.invoke(cli, ["log", "weight", "5.0"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestReportCommand:
    def test_report_empty(self, runner):
        result = runner.invoke(cli, ["report"])
        assert result.exit_code == 0
        assert "No" in result.output

    def test_report_shows_readings(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        runner.invoke(cli, ["log", "bp", "125", "85"])
        result = runner.invoke(cli, ["report", "--type", "bp"])
        assert result.exit_code == 0
        assert "120" in result.output
        assert "125" in result.output

    def test_report_weight_only(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        runner.invoke(cli, ["log", "weight", "74.0"])
        result = runner.invoke(cli, ["report", "--type", "weight"])
        assert result.exit_code == 0
        assert "74.0" in result.output


class TestStatsCommand:
    def test_stats_empty(self, runner):
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0

    def test_stats_bp(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        runner.invoke(cli, ["log", "bp", "130", "85"])
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

    def test_set_height_cm(self, runner):
        result = runner.invoke(cli, ["config", "--height-unit", "cm", "--height", "175"])
        assert result.exit_code == 0
        assert "175" in result.output

    def test_set_height_in(self, runner):
        result = runner.invoke(cli, ["config", "--height-unit", "in", "--height", "71"])
        assert result.exit_code == 0
        assert "71" in result.output

    def test_view_config_shows_height(self, runner):
        runner.invoke(cli, ["config", "--height-unit", "cm", "--height", "175"])
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "Height" in result.output
        assert "175" in result.output

    def test_view_config_no_height(self, runner):
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "not set" in result.output

    def test_set_name(self, runner):
        result = runner.invoke(cli, ["config", "--name", "Alice"])
        assert result.exit_code == 0
        assert "Alice" in result.output

    def test_view_config_shows_name(self, runner):
        runner.invoke(cli, ["config", "--name", "Alice"])
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "Alice" in result.output


class TestLogDate:
    def test_log_bp_with_date(self, runner):
        result = runner.invoke(cli, ["log", "bp", "120", "80", "--date", "2026-01-15"])
        assert result.exit_code == 0
        assert "120/80" in result.output

    def test_log_bp_with_datetime(self, runner):
        result = runner.invoke(cli, ["log", "bp", "120", "80", "--date", "2026-01-15 08:30"])
        assert result.exit_code == 0

    def test_log_weight_with_date(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        result = runner.invoke(cli, ["log", "weight", "75.0", "--date", "2026-01-15"])
        assert result.exit_code == 0
        assert "75.0 kg" in result.output

    def test_log_bp_invalid_date(self, runner):
        result = runner.invoke(cli, ["log", "bp", "120", "80", "--date", "not-a-date"])
        assert result.exit_code != 0


class TestDeleteCommand:
    def test_delete_bp(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["delete", "bp", "1", "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_delete_bp_not_found(self, runner):
        result = runner.invoke(cli, ["delete", "bp", "999", "--yes"])
        assert result.exit_code == 1

    def test_delete_bp_confirms(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["delete", "bp", "1"], input="y\n")
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_delete_bp_aborts(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["delete", "bp", "1"], input="n\n")
        assert result.exit_code != 0

    def test_delete_weight(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        runner.invoke(cli, ["log", "weight", "75.0"])
        result = runner.invoke(cli, ["delete", "weight", "1", "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_delete_weight_not_found(self, runner):
        result = runner.invoke(cli, ["delete", "weight", "999", "--yes"])
        assert result.exit_code == 1


class TestExportCommand:
    def test_export_bp(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["export", "--type", "bp"])
        assert result.exit_code == 0
        assert "systolic" in result.output
        assert "120" in result.output

    def test_export_weight(self, runner):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        runner.invoke(cli, ["log", "weight", "75.0"])
        result = runner.invoke(cli, ["export", "--type", "weight"])
        assert result.exit_code == 0
        assert "value_kg" in result.output
        assert "75.0" in result.output

    def test_export_to_file(self, runner, tmp_path):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        out = str(tmp_path / "out.csv")
        result = runner.invoke(cli, ["export", "--type", "bp", "--output", out])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert "120" in open(out).read()


class TestUserOption:
    def test_report_other_user_empty(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["report", "--type", "bp", "--user", "otheruser"])
        assert result.exit_code == 0
        assert "No" in result.output

    def test_export_other_user_empty(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["export", "--type", "bp", "--user", "otheruser"])
        assert result.exit_code == 0
        assert "120" not in result.output


class TestRollingAvg:
    def test_rolling_avg_shown_with_multiple_readings(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        runner.invoke(cli, ["log", "bp", "130", "85"])
        result = runner.invoke(cli, ["report", "--type", "bp"])
        assert result.exit_code == 0
        assert "125.0/" in result.output  # rolling avg of both readings

    def test_rolling_avg_not_shown_with_single_reading(self, runner):
        runner.invoke(cli, ["log", "bp", "120", "80"])
        result = runner.invoke(cli, ["report", "--type", "bp"])
        assert result.exit_code == 0
        assert "/" not in result.output.split("120")[1].split("\n")[0]  # no avg col next to value


class TestPlotBMI:
    def test_plot_bmi_no_height(self, runner):
        result = runner.invoke(cli, ["plot", "bmi"])
        assert result.exit_code == 0
        assert "Tip" in result.output

    def test_plot_bmi_no_readings(self, runner):
        runner.invoke(cli, ["config", "--height-unit", "cm", "--height", "175"])
        result = runner.invoke(cli, ["plot", "bmi"])
        assert result.exit_code == 0
        assert "No weight readings" in result.output

    def test_plot_bmi_terminal(self, runner, monkeypatch):
        runner.invoke(cli, ["config", "--weight-unit", "kg"])
        runner.invoke(cli, ["config", "--height-unit", "cm", "--height", "175"])
        runner.invoke(cli, ["log", "weight", "75.0"])

        called = []
        monkeypatch.setattr(
            "mbp.plot.plot_bmi_terminal",
            lambda readings, height_cm: called.append((readings, height_cm)),
        )
        result = runner.invoke(cli, ["plot", "bmi"])
        assert result.exit_code == 0
        assert len(called) == 1
        assert called[0][1] == 175.0
