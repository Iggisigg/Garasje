"""
Hyundai Ioniq 5 service with mock mode support

Future: Will integrate with OBD-II dongle via Bluetooth
Currently: Mock mode only for testing dual-vehicle system
"""

import math
import time
from datetime import datetime
from typing import Optional

from services.base_service import BaseVehicleService
from models.vehicle import VehicleStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class IoniqService(BaseVehicleService):
    """Hyundai Ioniq 5 service"""

    def __init__(
        self,
        mock_mode: bool = True,
        obd_adapter_address: Optional[str] = None
    ):
        """
        Initialize Ioniq 5 service

        Args:
            mock_mode: Use mock data instead of real OBD-II (default: True for now)
            obd_adapter_address: Bluetooth address of OBD-II adapter (future use)
        """
        super().__init__("Hyundai Ioniq 5", mock_mode)
        self.obd_adapter_address = obd_adapter_address
        self.cached_status: Optional[VehicleStatus] = None
        self.last_fetch_time: Optional[datetime] = None
        self.cache_duration_seconds = 300  # 5 minutes

        if not mock_mode:
            logger.warning("OBD-II integration not yet implemented. Using mock mode.")
            self.mock_mode = True

    async def authenticate(self):
        """
        Authenticate with Ioniq (no-op for OBD-II)

        OBD-II doesn't require authentication, but this method
        is required by the BaseVehicleService abstract class
        """
        if self.mock_mode:
            self.logger.debug("Mock mode - no authentication needed")
        else:
            # Future: Initialize OBD-II connection
            self.logger.info("OBD-II connection initialization (not yet implemented)")

    async def get_vehicle_status(self) -> VehicleStatus:
        """
        Get current vehicle status

        Returns:
            VehicleStatus with current battery data
        """
        if self.mock_mode:
            return self._get_mock_data()

        # Future: OBD-II implementation
        raise NotImplementedError("OBD-II integration coming in version 2.1")

    def _get_mock_data(self) -> VehicleStatus:
        """
        Generate mock data for Ioniq 5

        Simulates different charging pattern than Tesla to test dual-vehicle logic

        Returns:
            VehicleStatus with simulated data
        """
        # Simulate gradual battery changes using cosine wave (different from Tesla's sine)
        # This ensures the two vehicles have different battery levels for testing
        base_battery = 65.0
        time_factor = time.time() / 3600  # Hours since epoch
        variance = math.cos(time_factor * 1.2) * 25  # ±25% variance, different frequency
        battery = max(15.0, min(95.0, base_battery + variance))

        # Simulate charging if battery is very low
        is_charging = battery < 35.0

        # Calculate range based on battery (Ioniq 5 ~480km at 100%)
        range_km = battery * 4.8

        self.logger.debug(f"Mock data (Ioniq 5): {battery:.1f}% ({range_km:.0f} km)")

        return VehicleStatus(
            vehicle_name="Hyundai Ioniq 5",
            battery_percent=round(battery, 1),
            range_km=round(range_km, 0),
            is_charging=is_charging,
            location="home",
            last_updated=datetime.now(),
            is_mock=True,
            charging_rate_kw=10.5 if is_charging else None  # Slightly slower home charging than Tesla
        )

    async def close(self):
        """Close Ioniq connection"""
        if self.obd_adapter_address and not self.mock_mode:
            # Future: Close OBD-II connection
            pass
        self.logger.info("Ioniq service closed")
