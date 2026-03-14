import pytest
from mbp.validate import validate_bp, validate_weight
from mbp.models import WeightReading
from datetime import datetime


class TestValidateBP:
    def test_normal(self):
        r = validate_bp(120, 80, 65)
        assert r.systolic == 120
        assert r.diastolic == 80
        assert r.pulse == 65
        assert r.warnings == []

    def test_auto_swap(self):
        r = validate_bp(80, 120, None)
        assert r.systolic == 120
        assert r.diastolic == 80
        assert len(r.warnings) == 1
        assert "swapped" in r.warnings[0].lower()

    def test_no_pulse(self):
        r = validate_bp(115, 75, None)
        assert r.pulse is None

    def test_systolic_too_low(self):
        with pytest.raises(ValueError, match="Systolic"):
            validate_bp(50, 30, None)

    def test_systolic_too_high(self):
        with pytest.raises(ValueError, match="Systolic"):
            validate_bp(350, 80, None)

    def test_diastolic_too_low(self):
        with pytest.raises(ValueError, match="Diastolic"):
            validate_bp(120, 10, None)

    def test_pulse_out_of_range(self):
        with pytest.raises(ValueError, match="Pulse"):
            validate_bp(120, 80, 5)


class TestValidateWeight:
    def test_kg(self):
        kg = validate_weight(75.0, "kg")
        assert kg == pytest.approx(75.0)

    def test_lbs_to_kg(self):
        kg = validate_weight(165.0, "lbs")
        assert kg == pytest.approx(165.0 / 2.20462, rel=1e-3)

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="Unknown weight unit"):
            validate_weight(70, "stone")

    def test_too_light(self):
        with pytest.raises(ValueError, match="plausible range"):
            validate_weight(5.0, "kg")

    def test_too_heavy(self):
        with pytest.raises(ValueError, match="plausible range"):
            validate_weight(600.0, "kg")


def _make_weight(value_kg: float) -> WeightReading:
    return WeightReading(
        value_kg=value_kg,
        unit="kg",
        note=None,
        username="test",
        timestamp=datetime.now(),
    )


class TestBMI:
    def test_bmi_calculation(self):
        r = _make_weight(70.0)
        # 70 / (1.75 ** 2) = 22.857...
        assert r.bmi(175.0) == pytest.approx(22.9, abs=0.1)

    def test_bmi_underweight(self):
        r = _make_weight(50.0)
        assert r.bmi_category(175.0) == "Underweight"
        assert r.bmi_color(175.0) == "yellow"

    def test_bmi_normal(self):
        r = _make_weight(70.0)
        assert r.bmi_category(175.0) == "Normal"
        assert r.bmi_color(175.0) == "green"

    def test_bmi_overweight(self):
        r = _make_weight(85.0)
        assert r.bmi_category(175.0) == "Overweight"
        assert r.bmi_color(175.0) == "orange1"

    def test_bmi_obese(self):
        r = _make_weight(105.0)
        assert r.bmi_category(175.0) == "Obese"
        assert r.bmi_color(175.0) == "red"

    def test_bmi_boundary_normal_lower(self):
        # BMI of exactly 18.5 should be Normal
        # weight = 18.5 * (1.75 ** 2) = 56.6...
        height_cm = 175.0
        height_m = height_cm / 100.0
        value_kg = 18.5 * (height_m ** 2)
        r = _make_weight(value_kg)
        assert r.bmi_category(height_cm) == "Normal"

    def test_bmi_boundary_overweight(self):
        # BMI of exactly 25.0 should be Overweight
        height_cm = 175.0
        height_m = height_cm / 100.0
        value_kg = 25.0 * (height_m ** 2)
        r = _make_weight(value_kg)
        assert r.bmi_category(height_cm) == "Overweight"

    def test_bmi_boundary_obese(self):
        # BMI of exactly 30.0 should be Obese
        height_cm = 175.0
        height_m = height_cm / 100.0
        value_kg = 30.0 * (height_m ** 2)
        r = _make_weight(value_kg)
        assert r.bmi_category(height_cm) == "Obese"
