"""
Tesla API service with mock mode support
"""

import math
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.base_service import BaseVehicleService
from models.vehicle import VehicleStatus
from utils.exceptions import TeslaAPIError, TeslaAuthenticationError, VehicleAsleepError
from utils.logger import get_logger

logger = get_logger(__name__)


class TeslaService(BaseVehicleService):
    """Tesla API service"""

    def __init__(
        self,
        email: str,
        cache_file: str = "data/tesla_cache.json",
        mock_mode: bool = False
    ):
        """
        Initialize Tesla service

        Args:
            email: Tesla account email
            cache_file: Path to cache file for OAuth tokens
            mock_mode: Use mock data instead of real API
        """
        super().__init__("Tesla Model Y", mock_mode)
        self.email = email
        self.cache_file = Path(cache_file)
        self.tesla = None
        self.vehicle = None
        self.last_fetch_time: Optional[datetime] = None
        self.cached_status: Optional[VehicleStatus] = None
        self.cache_duration_seconds = 300  # Cache for 5 minutes

    async def authenticate(self):
        """
        Authenticate with Tesla API using OAuth

        Raises:
            TeslaAuthenticationError: If authentication fails
        """
        if self.mock_mode:
            self.logger.info("Mock mode enabled - skipping Tesla authentication")
            return

        try:
            import teslapy

            # Ensure cache directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Initialize Tesla API
            self.tesla = teslapy.Tesla(self.email, cache_file=str(self.cache_file))

            # Check if we need to authenticate
            if not self.tesla.authorized:
                self.logger.warning("Tesla token not found or expired. Run scripts/setup_tesla.py first.")
                raise TeslaAuthenticationError(
                    "Not authenticated. Please run 'python scripts/setup_tesla.py' to complete OAuth flow."
                )

            # Get list of vehicles
            vehicles = self.tesla.vehicle_list()
            if not vehicles:
                raise TeslaAuthenticationError("No vehicles found in Tesla account")

            # Use first vehicle (can be extended for multiple vehicles)
            self.vehicle = vehicles[0]
            self.logger.info(f"Connected to Tesla: {self.vehicle['display_name']}")

        except ImportError:
            raise TeslaAuthenticationError("teslapy library not installed. Run: pip install teslapy")
        except Exception as e:
            raise TeslaAuthenticationError(f"Tesla authentication failed: {e}")

    async def get_vehicle_status(self) -> VehicleStatus:
        """
        Get current vehicle status

        Returns:
            VehicleStatus with current battery data

        Raises:
            TeslaAPIError: If unable to fetch data
        """
        if self.mock_mode:
            return self._get_mock_data()

        # Check cache first
        if self._is_cache_valid():
            self.logger.debug("Using cached Tesla data")
            return self.cached_status

        try:
            # Fetch fresh data from Tesla API
            status = await self._fetch_from_api()

            # Update cache
            self.last_fetch_time = datetime.now()
            self.cached_status = status

            return status

        except Exception as e:
            self.logger.error(f"Failed to fetch Tesla data: {e}")

            # Return cached data if available, even if expired
            if self.cached_status:
                self.logger.warning("Returning stale cached data due to API error")
                return self.cached_status

            raise TeslaAPIError(f"Failed to fetch Tesla data: {e}")

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cached_status or not self.last_fetch_time:
            return False

        age = (datetime.now() - self.last_fetch_time).total_seconds()
        return age < self.cache_duration_seconds

    async def _fetch_from_api(self) -> VehicleStatus:
        """
        Fetch data from Tesla API

        Returns:
            VehicleStatus with fresh data

        Raises:
            TeslaAPIError: If fetch fails
        """
        if not self.vehicle:
            await self.authenticate()

        try:
            # Get vehicle data
            # Note: This may wake the vehicle if it's asleep
            # For production, check vehicle state first
            data = self.vehicle.get_vehicle_data()

            # Extract charge state
            charge_state = data.get('charge_state', {})
            battery_level = charge_state.get('battery_level', 0)
            battery_range = charge_state.get('battery_range', 0)
            charging_state = charge_state.get('charging_state', 'Disconnected')
            is_charging = charging_state in ['Charging', 'Starting']

            # Convert miles to km (Tesla API returns miles)
            range_km = battery_range * 1.60934

            # Determine location (simplified - could use geofencing)
            drive_state = data.get('drive_state', {})
            # For now, assume home if not driving
            location = "home"  # Could check coordinates against home location

            return VehicleStatus(
                vehicle_name=data.get('display_name', 'Tesla Model Y'),
                battery_percent=float(battery_level),
                range_km=range_km,
                is_charging=is_charging,
                location=location,
                last_updated=datetime.now(),
                is_mock=False,
                charging_rate_kw=charge_state.get('charger_power') if is_charging else None
            )

        except Exception as e:
            self.logger.error(f"Tesla API error: {e}")
            raise TeslaAPIError(f"Failed to fetch from Tesla API: {e}")

    def _get_mock_data(self) -> VehicleStatus:
        """
        Generate mock data for testing

        Returns:
            VehicleStatus with simulated data
        """
        # Simulate gradual battery changes using sine wave
        # This creates realistic-looking battery percentage changes over time
        base_battery = 70.0
        time_factor = time.time() / 3600  # Hours since epoch
        variance = math.sin(time_factor) * 20  # ±20% variance
        battery = max(20.0, min(90.0, base_battery + variance))

        # Simulate charging if battery is low
        is_charging = battery < 40.0

        # Calculate range based on battery (Tesla Model Y ~450km at 100%)
        range_km = battery * 4.5

        self.logger.debug(f"Mock data: {battery:.1f}% ({range_km:.0f} km)")

        return VehicleStatus(
            vehicle_name="Tesla Model Y",
            battery_percent=round(battery, 1),
            range_km=round(range_km, 0),
            is_charging=is_charging,
            location="home",
            last_updated=datetime.now(),
            is_mock=True,
            charging_rate_kw=11.0 if is_charging else None
        )

    async def wake_vehicle(self) -> bool:
        """
        Wake vehicle from sleep

        Returns:
            True if vehicle is awake, False otherwise

        Raises:
            VehicleAsleepError: If unable to wake vehicle
        """
        if self.mock_mode:
            return True

        try:
            self.vehicle.sync_wake_up()
            self.logger.info("Tesla woken up successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to wake Tesla: {e}")
            raise VehicleAsleepError(f"Could not wake vehicle: {e}")

    async def close(self):
        """Close Tesla connection"""
        self.tesla = None
        self.vehicle = None
        self.logger.info("Tesla service closed")
