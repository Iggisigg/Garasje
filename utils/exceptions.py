"""
Custom exceptions for Charging Manager
"""


class ChargingManagerError(Exception):
    """Base exception for all Charging Manager errors"""
    pass


class VehicleServiceError(ChargingManagerError):
    """Base exception for vehicle service errors"""
    pass


class TeslaAPIError(VehicleServiceError):
    """Tesla API communication error"""
    pass


class TeslaAuthenticationError(TeslaAPIError):
    """Tesla OAuth authentication failed"""
    pass


class VehicleAsleepError(VehicleServiceError):
    """Vehicle is asleep and cannot be woken"""
    pass


class VehicleNotHomeError(VehicleServiceError):
    """Vehicle is not at home location"""
    pass


class DatabaseError(ChargingManagerError):
    """Database operation failed"""
    pass


class ConfigurationError(ChargingManagerError):
    """Configuration is invalid or missing"""
    pass
