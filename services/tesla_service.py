"""
Tesla Fleet API service with mock mode support

Fleet API documentation: https://developer.tesla.com/docs/fleet-api
"""

import asyncio
import math
import time
import json
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx

from services.base_service import BaseVehicleService
from models.vehicle import VehicleStatus
from utils.exceptions import TeslaAPIError, TeslaAuthenticationError
from utils.logger import get_logger
from utils.geocoding import reverse_geocode

logger = get_logger(__name__)


class TeslaFleetService(BaseVehicleService):
    """Tesla Fleet API service"""

    # Fleet API endpoints
    AUTH_URL = "https://auth.tesla.com/oauth2/v3"
    REGION_ENDPOINTS = {
        "EU": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
        "NA": "https://fleet-api.prd.na.vn.cloud.tesla.com"
    }

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        cache_file: str = "data/tesla_cache.json",
        mock_mode: bool = False,
        region: str = "EU"
    ):
        """
        Initialize Tesla Fleet API service

        Args:
            client_id: Tesla Developer App Client ID
            client_secret: Tesla Developer App Client Secret
            cache_file: Path to token cache file
            mock_mode: Use mock data instead of real API
            region: Tesla API region (EU or NA)
        """
        super().__init__("Tesla Model Y", mock_mode)
        self.client_id = client_id
        self.client_secret = client_secret
        self.cache_file = Path(cache_file)
        self.region = region.upper()

        # Set API URL based on region
        if self.region not in self.REGION_ENDPOINTS:
            self.logger.warning(f"Unknown region '{region}', defaulting to EU")
            self.region = "EU"
        self.api_url = self.REGION_ENDPOINTS[self.region]
        self.logger.info(f"Using Tesla Fleet API region: {self.region} ({self.api_url})")

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.vehicle_id: Optional[str] = None
        self.last_fetch_time: Optional[datetime] = None
        self.cached_status: Optional[VehicleStatus] = None
        self.cache_duration_seconds = 300  # 5 minutes

        # HTTP client for API requests
        self._http_client = httpx.AsyncClient(timeout=30.0)

        # Lock to prevent concurrent token refresh
        self._token_refresh_lock = asyncio.Lock()

        # Load cached tokens if available
        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from cache file"""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                self.vehicle_id = data.get('vehicle_id')

                expires_str = data.get('expires_at')
                if expires_str:
                    self.token_expires_at = datetime.fromisoformat(expires_str)

                self.logger.debug("Loaded tokens from cache")
        except Exception as e:
            self.logger.warning(f"Failed to load token cache: {e}")

    def _save_tokens(self):
        """Save tokens to cache file"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'vehicle_id': self.vehicle_id,
                'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None
            }

            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.debug("Saved tokens to cache")
        except Exception as e:
            self.logger.error(f"Failed to save token cache: {e}")

    def _is_token_valid(self) -> bool:
        """Check if access token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False

        # Add 60 second buffer
        return datetime.now() < (self.token_expires_at - timedelta(seconds=60))

    async def authenticate(self):
        """
        Authenticate with Tesla Fleet API

        For the first time, this requires running scripts/setup_tesla_fleet.py
        to complete the OAuth flow and obtain tokens.

        For subsequent calls, this will refresh the token if needed.
        """
        if self.mock_mode:
            self.logger.info("Mock mode - skipping authentication")
            return

        # Check if we need to refresh
        if self._is_token_valid():
            self.logger.debug("Token still valid")
            return

        # Try to refresh token with lock to prevent concurrent refreshes
        if self.refresh_token:
            async with self._token_refresh_lock:
                # Double-check token validity after acquiring lock
                # (another task might have refreshed it while we were waiting)
                if self._is_token_valid():
                    self.logger.debug("Token was refreshed by another task")
                    return

                try:
                    await self._refresh_access_token()
                    return
                except Exception as e:
                    self.logger.warning(f"Token refresh failed: {e}")

        # No valid tokens - need to run setup script
        raise TeslaAuthenticationError(
            "No valid tokens found. Please run: python scripts/setup_tesla_fleet.py"
        )

    async def _refresh_access_token(self):
        """Refresh access token using refresh token"""
        self.logger.info("Refreshing access token...")

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.refresh_token
        }

        response = await self._http_client.post(
            f"{self.AUTH_URL}/token",
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if response.status_code != 200:
            raise TeslaAuthenticationError(
                f"Token refresh failed: {response.status_code} - {response.text}"
            )

        token_data = response.json()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token', self.refresh_token)

        # Calculate expiration
        expires_in = token_data.get('expires_in', 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        self._save_tokens()
        self.logger.info("✓ Access token refreshed")

    async def get_vehicle_status(self) -> VehicleStatus:
        """
        Get current vehicle status

        Returns:
            VehicleStatus with current battery data
        """
        if self.mock_mode:
            return self._get_mock_data()

        # Check cache
        if self._is_cache_valid():
            self.logger.debug("Using cached Tesla data")
            return self.cached_status

        try:
            # Ensure we're authenticated
            await self.authenticate()

            # Get vehicle data
            status = await self._fetch_from_api()

            # Update cache
            self.last_fetch_time = datetime.now()
            self.cached_status = status

            return status

        except Exception as e:
            self.logger.error(f"Failed to fetch Tesla data: {e}")

            # Return cached data if available
            if self.cached_status:
                self.logger.warning("Returning stale cached data")
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
        Fetch data from Tesla Fleet API

        Returns:
            VehicleStatus with fresh data
        """
        # Get vehicle ID if we don't have it
        if not self.vehicle_id:
            await self._get_vehicle_id()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Get vehicle data - explicitly request charge_state and drive_state
        response = await self._http_client.get(
            f"{self.api_url}/api/1/vehicles/{self.vehicle_id}/vehicle_data",
            headers=headers,
            params={
                'endpoints': 'charge_state;drive_state;location_data;vehicle_state'
            }
        )

        if response.status_code == 408:
            # Vehicle is asleep
            self.logger.warning("Vehicle is asleep")
            # Return last known data or mock data
            if self.cached_status:
                return self.cached_status
            raise TeslaAPIError("Vehicle is asleep and no cached data available")

        if response.status_code != 200:
            raise TeslaAPIError(
                f"Fleet API error: {response.status_code} - {response.text}"
            )

        data = response.json()['response']

        # Extract charge state
        charge_state = data.get('charge_state', {})
        battery_level = charge_state.get('battery_level', 0)
        battery_range = charge_state.get('battery_range', 0)
        charging_state = charge_state.get('charging_state', 'Disconnected')
        is_charging = charging_state in ['Charging', 'Starting']
        charger_power = charge_state.get('charger_power', 0)

        # Convert miles to km
        range_km = battery_range * 1.60934

        # Extract GPS location
        drive_state = data.get('drive_state', {})
        latitude = drive_state.get('latitude')
        longitude = drive_state.get('longitude')

        self.logger.debug(f"GPS coordinates from API: lat={latitude}, lon={longitude}")

        # Reverse geocode to get address
        address = None
        if latitude is not None and longitude is not None:
            try:
                self.logger.info(f"Reverse geocoding position: {latitude}, {longitude}")
                address = await reverse_geocode(latitude, longitude)
                if address:
                    self.logger.info(f"✓ Geocoded address: {address}")
                else:
                    self.logger.warning("Geocoding returned no address")
            except Exception as e:
                self.logger.error(f"Failed to geocode location: {e}", exc_info=True)
        else:
            self.logger.warning("No GPS coordinates available from Tesla API")

        # Determine location (simplified - could use geofencing with home coordinates)
        location = "home"  # TODO: Implement proper geofencing

        return VehicleStatus(
            vehicle_name=data.get('display_name', 'Tesla Model Y'),
            battery_percent=float(battery_level),
            range_km=range_km,
            is_charging=is_charging,
            location=location,
            last_updated=datetime.now(),
            is_mock=False,
            charging_rate_kw=charger_power if is_charging else None,
            latitude=latitude,
            longitude=longitude,
            address=address
        )

    async def _get_vehicle_id(self):
        """Get vehicle ID from Fleet API"""
        self.logger.info("Getting vehicle ID...")

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        response = await self._http_client.get(
            f"{self.api_url}/api/1/vehicles",
            headers=headers
        )

        if response.status_code != 200:
            raise TeslaAPIError(
                f"Failed to get vehicles: {response.status_code} - {response.text}"
            )

        data = response.json()
        vehicles = data.get('response', [])

        if not vehicles:
            raise TeslaAPIError("No vehicles found in account")

        # Use first vehicle
        self.vehicle_id = str(vehicles[0]['id'])
        self.logger.info(f"✓ Found vehicle: {vehicles[0].get('display_name')} (ID: {self.vehicle_id})")

        # Save vehicle ID to cache
        self._save_tokens()

    def _get_mock_data(self) -> VehicleStatus:
        """
        Generate mock data for testing

        Returns:
            VehicleStatus with simulated data
        """
        # Simulate gradual battery changes using sine wave
        base_battery = 70.0
        time_factor = time.time() / 3600  # Hours since epoch
        variance = math.sin(time_factor) * 20  # ±20% variance
        battery = max(20.0, min(90.0, base_battery + variance))

        # Simulate charging if battery is low
        is_charging = battery < 40.0

        # Calculate range based on battery (Tesla Model Y ~450km at 100%)
        range_km = battery * 4.5

        self.logger.debug(f"Mock data: {battery:.1f}% ({range_km:.0f} km)")

        # Mock GPS coordinates (Oslo, Norway city center)
        mock_latitude = 59.9139
        mock_longitude = 10.7522

        return VehicleStatus(
            vehicle_name="Tesla Model Y",
            battery_percent=round(battery, 1),
            range_km=round(range_km, 0),
            is_charging=is_charging,
            location="home",
            last_updated=datetime.now(),
            is_mock=True,
            charging_rate_kw=11.0 if is_charging else None,
            latitude=mock_latitude,
            longitude=mock_longitude,
            address="Mock adresse - Oslo sentrum"
        )

    async def close(self):
        """Close Tesla connection and HTTP client"""
        await self._http_client.aclose()
        self.logger.info("Tesla Fleet service closed")


# For backwards compatibility - use new class name
TeslaService = TeslaFleetService
