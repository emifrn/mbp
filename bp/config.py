import json
from pathlib import Path

from bp.db import get_db_path

_VALID_UNITS = ("kg", "lbs")


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
