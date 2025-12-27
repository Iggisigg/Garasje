"""
Vehicle data models
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class VehicleStatus:
    """Represents the current status of a vehicle"""

    vehicle_name: str
    battery_percent: float
    range_km: float
    is_charging: bool
    location: str  # "home" or "away"
    last_updated: datetime
    is_mock: bool = False
    charging_rate_kw: Optional[float] = None  # If charging, rate in kW
    estimated_full_time: Optional[datetime] = None  # If charging, when will it be full

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime to ISO format strings
        data['last_updated'] = self.last_updated.isoformat()
        if self.estimated_full_time:
            data['estimated_full_time'] = self.estimated_full_time.isoformat()
        return data

    @property
    def is_home(self) -> bool:
        """Check if vehicle is at home"""
        return self.location.lower() == "home"

    @property
    def needs_charge(self) -> bool:
        """Check if vehicle might need charging (below 50%)"""
        return self.battery_percent < 50.0

    def __str__(self) -> str:
        """String representation"""
        status = "Lader" if self.is_charging else "Lader ikke"
        location = "Hjemme" if self.is_home else "Borte"
        mock = " [MOCK]" if self.is_mock else ""
        return f"{self.vehicle_name}: {self.battery_percent}% ({self.range_km} km) - {status} - {location}{mock}"
