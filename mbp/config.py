import json
from pathlib import Path

from mbp.db import get_db_path

_VALID_UNITS = ("kg", "lbs")
_VALID_HEIGHT_UNITS = ("cm", "in")


def _config_path() -> Path:
    return get_db_path().parent / "config.json"


def load_config() -> dict:
    path = _config_path()
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_config(cfg: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2))


def get_weight_unit() -> str:
    return load_config().get("weight_unit", "kg")


def set_weight_unit(unit: str) -> None:
    if unit not in _VALID_UNITS:
        raise ValueError(f"Invalid unit '{unit}'. Choose from: {', '.join(_VALID_UNITS)}")
    cfg = load_config()
    cfg["weight_unit"] = unit
    save_config(cfg)


def get_height_unit() -> str:
    return load_config().get("height_unit", "cm")


def set_height_unit(unit: str) -> None:
    if unit not in _VALID_HEIGHT_UNITS:
        raise ValueError(f"Invalid height unit '{unit}'. Choose from: {', '.join(_VALID_HEIGHT_UNITS)}")
    cfg = load_config()
    cfg["height_unit"] = unit
    save_config(cfg)


def get_height_cm() -> float | None:
    """Return stored height in cm, or None if not set."""
    return load_config().get("height_cm")


def set_height(value: float, unit: str) -> None:
    """Store height internally in cm. unit is 'cm' or 'in'."""
    if unit == "in":
        height_cm = value * 2.54
    elif unit == "cm":
        height_cm = value
    else:
        raise ValueError(f"Invalid height unit '{unit}'. Choose from: cm, in")
    cfg = load_config()
    cfg["height_cm"] = round(height_cm, 2)
    save_config(cfg)
