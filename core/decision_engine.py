"""
Decision engine for charging recommendations
"""

from datetime import datetime
from typing import Optional, Tuple, Dict

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

    async def calculate_dual_recommendations(
        self,
        tesla_status: VehicleStatus,
        ioniq_status: Optional[VehicleStatus] = None
    ) -> Dict[str, Recommendation]:
        """
        Calculate charging recommendations for both vehicles

        Args:
            tesla_status: Tesla status
            ioniq_status: Ioniq status (optional, None if disabled)

        Returns:
            Dictionary with 'tesla' and 'ioniq' recommendations
            Also includes 'priority_vehicle' indicating which should charge first
        """
        recommendations = {}

        # Get Tesla recommendation
        tesla_rec = await self.calculate_recommendation(tesla_status)
        recommendations['tesla'] = tesla_rec

        # Get Ioniq recommendation if enabled
        if ioniq_status:
            ioniq_rec = await self.calculate_recommendation(ioniq_status)
            recommendations['ioniq'] = ioniq_rec

            # Determine priority vehicle
            priority = await self.compare_vehicles(tesla_status, ioniq_status)
            recommendations['priority_vehicle'] = priority

            self.logger.info(f"Dual vehicle recommendations: Tesla={tesla_rec.action.value}, Ioniq={ioniq_rec.action.value}, Priority={priority}")
        else:
            recommendations['ioniq'] = None
            recommendations['priority_vehicle'] = tesla_status.vehicle_name if tesla_rec.action == ChargeAction.CHARGE else "NONE"

            self.logger.info(f"Single vehicle recommendation: Tesla={tesla_rec.action.value}")

        return recommendations

    async def compare_vehicles(
        self,
        vehicle_a: VehicleStatus,
        vehicle_b: VehicleStatus
    ) -> str:
        """
        Compare two vehicles and recommend which should charge

        Args:
            vehicle_a: First vehicle status (Tesla)
            vehicle_b: Second vehicle status (Ioniq)

        Returns:
            Name of vehicle that should charge, or "NONE" if neither needs charging
        """

        # Get recommendations for both
        rec_a = await self.calculate_recommendation(vehicle_a)
        rec_b = await self.calculate_recommendation(vehicle_b)

        self.logger.debug(f"Comparing vehicles:")
        self.logger.debug(f"  {vehicle_a.vehicle_name}: {vehicle_a.battery_percent}% → priority_score={rec_a.priority_score}, action={rec_a.action.value}")
        self.logger.debug(f"  {vehicle_b.vehicle_name}: {vehicle_b.battery_percent}% → priority_score={rec_b.priority_score}, action={rec_b.action.value}")

        # Helper function to check if a vehicle needs charging (CHARGE or CONTINUE_CHARGING)
        def needs_charging(action: ChargeAction) -> bool:
            return action in (ChargeAction.CHARGE, ChargeAction.CONTINUE_CHARGING)

        # If neither should charge
        if not needs_charging(rec_a.action) and not needs_charging(rec_b.action):
            self.logger.info("Neither vehicle needs charging")
            return "NONE"

        # If only one needs charging
        if needs_charging(rec_a.action) and not needs_charging(rec_b.action):
            self.logger.info(f"Only {vehicle_a.vehicle_name} needs charging (action={rec_a.action.value})")
            return vehicle_a.vehicle_name

        if needs_charging(rec_b.action) and not needs_charging(rec_a.action):
            self.logger.info(f"Only {vehicle_b.vehicle_name} needs charging (action={rec_b.action.value})")
            return vehicle_b.vehicle_name

        # If both need charging, prioritize by battery level
        # Lower battery = higher gap = higher priority_score = should charge first
        if rec_a.priority_score > rec_b.priority_score:
            self.logger.info(f"Both need charging. Priority: {vehicle_a.vehicle_name} ({vehicle_a.battery_percent}% < {vehicle_b.battery_percent}%, priority_score={rec_a.priority_score})")
            return vehicle_a.vehicle_name
        elif rec_b.priority_score > rec_a.priority_score:
            self.logger.info(f"Both need charging. Priority: {vehicle_b.vehicle_name} ({vehicle_b.battery_percent}% < {vehicle_a.battery_percent}%, priority_score={rec_b.priority_score})")
            return vehicle_b.vehicle_name
        else:
            # Equal priority - prefer the one with lower battery as tiebreaker
            if vehicle_a.battery_percent < vehicle_b.battery_percent:
                self.logger.info(f"Equal priority. Tiebreaker: {vehicle_a.vehicle_name} ({vehicle_a.battery_percent}% < {vehicle_b.battery_percent}%)")
                return vehicle_a.vehicle_name
            else:
                self.logger.info(f"Equal priority. Tiebreaker: {vehicle_b.vehicle_name} ({vehicle_b.battery_percent}% <= {vehicle_a.battery_percent}%)")
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
