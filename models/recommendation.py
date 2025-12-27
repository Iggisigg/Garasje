"""
Recommendation data models
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ChargeAction(str, Enum):
    """Possible charging actions"""
    CHARGE = "CHARGE"
    NO_CHARGE = "NO_CHARGE"
    CONTINUE_CHARGING = "CONTINUE_CHARGING"


@dataclass
class Recommendation:
    """Represents a charging recommendation"""

    action: ChargeAction
    reason: str
    timestamp: datetime
    battery_percent: float
    threshold: float
    priority_score: float = 0.0  # For future multi-vehicle comparison

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['action'] = self.action.value
        return data

    @property
    def should_charge(self) -> bool:
        """Check if recommendation is to charge"""
        return self.action == ChargeAction.CHARGE

    @property
    def norwegian_action(self) -> str:
        """Get Norwegian translation of action"""
        translations = {
            ChargeAction.CHARGE: "LAD",
            ChargeAction.NO_CHARGE: "IKKE LAD",
            ChargeAction.CONTINUE_CHARGING: "FORTSETT Å LADE"
        }
        return translations.get(self.action, self.action.value)

    def __str__(self) -> str:
        """String representation"""
        return f"{self.norwegian_action}: {self.reason} (Batteri: {self.battery_percent}%, Terskel: {self.threshold}%)"
