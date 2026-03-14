import json
from pathlib import Path

from mbp.db import get_db_path

_VALID_UNITS = ("kg", "lbs")
_VALID_HEIGHT_UNITS = ("cm", "in")
_HEIGHT_RANGE_CM = (50.0, 300.0)
_HEIGHT_RANGE_IN = (20.0, 120.0)


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


def get_name() -> str | None:
    return load_config().get("name")


def set_name(name: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    cfg = load_config()
    cfg["name"] = name
    save_config(cfg)


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
    return load_config().get("height_cm")


def set_height(value: float, unit: str) -> None:
    if unit == "in":
        lo, hi = _HEIGHT_RANGE_IN
        if not (lo <= value <= hi):
            raise ValueError(f"Height must be between {lo} and {hi} inches.")
        height_cm = value * 2.54
    elif unit == "cm":
        lo, hi = _HEIGHT_RANGE_CM
        if not (lo <= value <= hi):
            raise ValueError(f"Height must be between {lo} and {hi} cm.")
        height_cm = value
    else:
        raise ValueError(f"Invalid height unit '{unit}'. Choose from: cm, in")
    cfg = load_config()
    cfg["height_cm"] = round(height_cm, 2)
    save_config(cfg)
