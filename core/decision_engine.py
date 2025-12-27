"""
Decision engine for charging recommendations
"""

from datetime import datetime
from typing import Optional

from models.vehicle import VehicleStatus
from models.recommendation import Recommendation, ChargeAction
from utils.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """Determines when vehicles should be charged"""

    def __init__(self, charge_threshold: float = 80.0, minimum_charge: float = 20.0):
        """
        Initialize decision engine

        Args:
            charge_threshold: Don't charge if battery is above this percentage
            minimum_charge: Always charge if battery is below this percentage
        """
        self.charge_threshold = charge_threshold
        self.minimum_charge = minimum_charge
        self.logger = logger

    async def calculate_recommendation(
        self,
        tesla_status: VehicleStatus
    ) -> Recommendation:
        """
        Calculate charging recommendation for Tesla

        Args:
            tesla_status: Current Tesla status

        Returns:
            Recommendation object
        """

        battery = tesla_status.battery_percent

        # Rule 1: Critical low battery - always charge
        if battery < self.minimum_charge:
            self.logger.info(f"Battery critically low: {battery}% < {self.minimum_charge}%")
            return Recommendation(
                action=ChargeAction.CHARGE,
                reason=f"Kritisk lavt batteri ({battery}% < {self.minimum_charge}%)",
                timestamp=datetime.now(),
                battery_percent=battery,
                threshold=self.charge_threshold,
                priority_score=100.0  # Highest priority
            )

        # Rule 2: Already charging - continue if below threshold
        if tesla_status.is_charging:
            if battery < self.charge_threshold:
                return Recommendation(
                    action=ChargeAction.CONTINUE_CHARGING,
                    reason=f"Fortsetter lading til terskel ({battery}% → {self.charge_threshold}%)",
                    timestamp=datetime.now(),
                    battery_percent=battery,
                    threshold=self.charge_threshold,
                    priority_score=50.0
                )
            else:
                return Recommendation(
                    action=ChargeAction.NO_CHARGE,
                    reason=f"Lading fullført - over terskel ({battery}% >= {self.charge_threshold}%)",
                    timestamp=datetime.now(),
                    battery_percent=battery,
                    threshold=self.charge_threshold,
                    priority_score=0.0
                )

        # Rule 3: Above threshold - no need to charge
        if battery >= self.charge_threshold:
            return Recommendation(
                action=ChargeAction.NO_CHARGE,
                reason=f"Batteri over terskel ({battery}% >= {self.charge_threshold}%)",
                timestamp=datetime.now(),
                battery_percent=battery,
                threshold=self.charge_threshold,
                priority_score=0.0
            )

        # Rule 4: Below threshold - should charge
        else:
            # Calculate priority based on how far below threshold
            gap = self.charge_threshold - battery
            priority = min(gap / self.charge_threshold * 100, 100.0)

            return Recommendation(
                action=ChargeAction.CHARGE,
                reason=f"Batteri under terskel ({battery}% < {self.charge_threshold}%)",
                timestamp=datetime.now(),
                battery_percent=battery,
                threshold=self.charge_threshold,
                priority_score=priority
            )

    async def compare_vehicles(
        self,
        vehicle_a: VehicleStatus,
        vehicle_b: VehicleStatus
    ) -> str:
        """
        Compare two vehicles and recommend which should charge

        Args:
            vehicle_a: First vehicle status
            vehicle_b: Second vehicle status

        Returns:
            Name of vehicle that should charge, or "NONE" if neither needs charging

        Note: This is for future use when Ioniq 5 is added
        """

        # Get recommendations for both
        rec_a = await self.calculate_recommendation(vehicle_a)
        rec_b = await self.calculate_recommendation(vehicle_b)

        # If neither should charge
        if rec_a.action == ChargeAction.NO_CHARGE and rec_b.action == ChargeAction.NO_CHARGE:
            return "NONE"

        # If only one should charge
        if rec_a.action == ChargeAction.CHARGE and rec_b.action != ChargeAction.CHARGE:
            return vehicle_a.vehicle_name

        if rec_b.action == ChargeAction.CHARGE and rec_a.action != ChargeAction.CHARGE:
            return vehicle_b.vehicle_name

        # If both should charge, prioritize by battery level (lower = higher priority)
        if rec_a.priority_score > rec_b.priority_score:
            return vehicle_a.vehicle_name
        else:
            return vehicle_b.vehicle_name

    def update_threshold(self, new_threshold: float):
        """
        Update charge threshold

        Args:
            new_threshold: New threshold percentage (0-100)
        """
        if not 0 <= new_threshold <= 100:
            raise ValueError("Threshold must be between 0 and 100")

        old = self.charge_threshold
        self.charge_threshold = new_threshold
        self.logger.info(f"Charge threshold updated: {old}% → {new_threshold}%")

    def get_status(self) -> dict:
        """Get current engine configuration"""
        return {
            "charge_threshold": self.charge_threshold,
            "minimum_charge": self.minimum_charge
        }
