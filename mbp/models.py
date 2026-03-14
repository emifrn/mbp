from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BPReading:
    systolic: int
    diastolic: int
    pulse: int | None
    note: str | None
    username: str
    device: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: int | None = None

    @property
    def category(self) -> str:
        s, d = self.systolic, self.diastolic
        if s > 180 or d > 120:
            return "Crisis"
        if s >= 140 or d >= 90:
            return "High Stage 2"
        if s >= 130 or d >= 80:
            return "High Stage 1"
        if s >= 120 and d < 80:
            return "Elevated"
        return "Normal"

    @property
    def category_color(self) -> str:
        return {
            "Normal": "green",
            "Elevated": "yellow",
            "High Stage 1": "orange1",
            "High Stage 2": "red",
            "Crisis": "bright_red",
        }[self.category]


@dataclass
class WeightReading:
    value_kg: float       # always stored in kg internally
    unit: str             # preferred display unit: "kg" or "lbs"
    note: str | None
    username: str
    device: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def display_value(self) -> float:
        if self.unit == "lbs":
            return round(self.value_kg * 2.20462, 1)
        return round(self.value_kg, 1)

    def bmi(self, height_cm: float) -> float:
        height_m = height_cm / 100.0
        return round(self.value_kg / (height_m ** 2), 1)

    def bmi_category(self, height_cm: float) -> str:
        b = self.bmi(height_cm)
        if b < 18.5:
            return "Underweight"
        if b < 25.0:
            return "Normal"
        if b < 30.0:
            return "Overweight"
        return "Obese"

    def bmi_color(self, height_cm: float) -> str:
        return {
            "Underweight": "yellow",
            "Normal": "green",
            "Overweight": "orange1",
            "Obese": "red",
        }[self.bmi_category(height_cm)]
