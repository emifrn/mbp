import pytest
from bp.validate import validate_bp, validate_weight


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
