"""
Base service for vehicle data providers
"""

from abc import ABC, abstractmethod
from models.vehicle import VehicleStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseVehicleService(ABC):
    """Abstract base class for vehicle data services"""

    def __init__(self, vehicle_name: str, mock_mode: bool = False):
        """
        Initialize vehicle service

        Args:
            vehicle_name: Name of the vehicle
            mock_mode: Whether to use mock data instead of real API
        """
        self.vehicle_name = vehicle_name
        self.mock_mode = mock_mode
        self.logger = logger

    @abstractmethod
    async def get_vehicle_status(self) -> VehicleStatus:
        """
        Get current vehicle status

        Returns:
            VehicleStatus object with current battery level, range, etc.

        Raises:
            VehicleServiceError: If unable to fetch vehicle data
        """
        pass

    @abstractmethod
    async def authenticate(self):
        """
        Authenticate with vehicle API

        Raises:
            VehicleServiceError: If authentication fails
        """
        pass

    async def close(self):
        """Close any open connections or cleanup resources"""
        pass
