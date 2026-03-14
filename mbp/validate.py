from dataclasses import dataclass

# Physiologically plausible ranges used for sanity checks
_SYS_MIN, _SYS_MAX = 60, 300
_DIA_MIN, _DIA_MAX = 30, 200
_PULSE_MIN, _PULSE_MAX = 20, 300
_WEIGHT_MIN_KG, _WEIGHT_MAX_KG = 20.0, 500.0


@dataclass
class BPValidationResult:
    systolic: int
    diastolic: int
    pulse: int | None
    warnings: list[str]


def validate_bp(systolic: int, diastolic: int, pulse: int | None) -> BPValidationResult:
    warnings: list[str] = []

    # Auto-correct reversed values
    if systolic < diastolic:
        systolic, diastolic = diastolic, systolic
        warnings.append("Systolic and diastolic were swapped — corrected automatically.")

    if not (_SYS_MIN <= systolic <= _SYS_MAX):
        raise ValueError(
            f"Systolic {systolic} is outside plausible range ({_SYS_MIN}–{_SYS_MAX})."
        )
    if not (_DIA_MIN <= diastolic <= _DIA_MAX):
        raise ValueError(
            f"Diastolic {diastolic} is outside plausible range ({_DIA_MIN}–{_DIA_MAX})."
        )
    if pulse is not None and not (_PULSE_MIN <= pulse <= _PULSE_MAX):
        raise ValueError(
            f"Pulse {pulse} is outside plausible range ({_PULSE_MIN}–{_PULSE_MAX})."
        )

    return BPValidationResult(systolic, diastolic, pulse, warnings)


def validate_weight(value: float, unit: str) -> float:
    """Validate weight and return the value in kg."""
    if unit not in ("kg", "lbs"):
        raise ValueError(f"Unknown weight unit '{unit}'. Use 'kg' or 'lbs'.")

    value_kg = value if unit == "kg" else value / 2.20462

    if not (_WEIGHT_MIN_KG <= value_kg <= _WEIGHT_MAX_KG):
        min_display = value if unit == "kg" else round(_WEIGHT_MIN_KG * 2.20462, 1)
        max_display = value if unit == "kg" else round(_WEIGHT_MAX_KG * 2.20462, 1)
        raise ValueError(
            f"Weight {value} {unit} is outside plausible range "
            f"({min_display}–{max_display} {unit})."
        )

    return value_kg
