"""
Dashboard API routes
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models for request validation
class ThresholdUpdate(BaseModel):
    """Model for threshold update request"""
    threshold: float = Field(..., ge=0, le=100, description="Charge threshold percentage (0-100)")

    @field_validator('threshold')
    @classmethod
    def validate_threshold(cls, v):
        """Ensure threshold is a reasonable value"""
        if v < 0 or v > 100:
            raise ValueError('Threshold must be between 0 and 100')
        return round(v, 1)  # Round to 1 decimal place


class MockModeUpdate(BaseModel):
    """Model for mock mode update request"""
    enabled: bool = Field(..., description="Enable or disable mock mode")


@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serve the main dashboard HTML page"""
    from api.app import templates

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@router.get("/api/status")
async def get_status():
    """
    Get current status of all vehicles and recommendations

    Returns:
        JSON with Tesla and Ioniq status and charging recommendations
    """
    from api.app import tesla_service, ioniq_service, decision_engine, scheduler

    try:
        # Get Tesla status
        tesla_status = await tesla_service.get_vehicle_status()

        # Get Ioniq status (if enabled)
        ioniq_status = None
        if ioniq_service:
            ioniq_status = await ioniq_service.get_vehicle_status()

        # Calculate recommendations
        recommendations = await decision_engine.calculate_dual_recommendations(
            tesla_status,
            ioniq_status
        )

        # Get next scheduled update time
        next_update = scheduler.get_next_run_time()

        # Build response
        response = {
            "tesla": tesla_status.to_dict(),
            "tesla_recommendation": recommendations['tesla'].to_dict(),
            "priority_vehicle": recommendations['priority_vehicle'],
            "last_updated": datetime.now().isoformat(),
            "next_update": next_update.isoformat() if next_update else None
        }

        # Add Ioniq data if available
        if ioniq_status and recommendations['ioniq']:
            response['ioniq'] = ioniq_status.to_dict()
            response['ioniq_recommendation'] = recommendations['ioniq'].to_dict()
        else:
            response['ioniq'] = None
            response['ioniq_recommendation'] = None

        return response

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/update")
async def trigger_update():
    """
    Manually trigger a vehicle data update

    Returns:
        Status message
    """
    from api.app import scheduler

    try:
        logger.info("Manual update triggered via API")
        await scheduler.trigger_manual_update()

        return {
            "status": "success",
            "message": "Update completed",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Manual update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history")
async def get_history(
    hours: int = Query(default=24, ge=1, le=720, description="Number of hours of history (1-720)"),
    vehicle: Optional[str] = Query(default=None, max_length=100, description="Filter by vehicle name")
):
    """
    Get battery reading history

    Args:
        hours: Number of hours of history (1-720, default: 24)
        vehicle: Filter by vehicle name (optional, max 100 chars)

    Returns:
        List of battery readings
    """
    from api.app import database

    try:
        readings = await database.get_history(vehicle=vehicle, hours=hours)

        return {
            "readings": readings,
            "count": len(readings),
            "hours": hours,
            "vehicle": vehicle
        }

    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/scheduler")
async def get_scheduler_status():
    """
    Get scheduler status and configuration

    Returns:
        Scheduler information
    """
    from api.app import scheduler

    return scheduler.get_status()


@router.get("/api/settings")
async def get_settings():
    """
    Get current application settings

    Returns:
        Current configuration
    """
    from api.app import decision_engine
    from config import config

    return {
        "charge_threshold": decision_engine.charge_threshold,
        "minimum_charge": decision_engine.minimum_charge,
        "update_interval_minutes": config.update_interval_minutes,
        "tesla_mock_mode": config.tesla_mock_mode,
        "ioniq_mock_mode": config.ioniq_mock_mode
    }


@router.put("/api/settings/threshold")
async def update_threshold(update: ThresholdUpdate):
    """
    Update charge threshold

    Args:
        update: Threshold update request with validated threshold (0-100)

    Returns:
        Updated settings
    """
    from api.app import decision_engine

    try:
        decision_engine.update_threshold(update.threshold)

        return {
            "status": "success",
            "charge_threshold": decision_engine.charge_threshold,
            "message": f"Threshold updated to {update.threshold}%"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/settings/mock-mode/{vehicle}")
async def update_mock_mode(vehicle: str, update: MockModeUpdate):
    """
    Update mock mode for a specific vehicle

    Args:
        vehicle: Vehicle name ('tesla' or 'ioniq')
        update: Mock mode update request with enabled flag

    Returns:
        Updated mock mode status
    """
    from api.app import tesla_service, ioniq_service
    from config import config
    from pathlib import Path

    # Validate vehicle parameter
    if vehicle not in ['tesla', 'ioniq']:
        raise HTTPException(status_code=400, detail="Vehicle must be 'tesla' or 'ioniq'")

    try:
        # Update both the service and config objects
        if vehicle == 'tesla':
            if not tesla_service:
                raise HTTPException(status_code=400, detail="Tesla service not initialized")
            tesla_service.mock_mode = update.enabled
            config.tesla_mock_mode = update.enabled  # Update config object
            logger.info(f"Tesla mock mode {'enabled' if update.enabled else 'disabled'}")
            env_key = 'TESLA_MOCK_MODE'
        else:  # ioniq
            if not ioniq_service:
                raise HTTPException(status_code=400, detail="Ioniq service not initialized")
            ioniq_service.mock_mode = update.enabled
            config.ioniq_mock_mode = update.enabled  # Update config object
            logger.info(f"Ioniq mock mode {'enabled' if update.enabled else 'disabled'}")
            env_key = 'IONIQ_MOCK_MODE'

        # Update .env file to persist the change across restarts
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()

            # Update the line with the mock mode setting
            updated = False
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.strip().startswith(env_key):
                        f.write(f"{env_key}={'true' if update.enabled else 'false'}\n")
                        updated = True
                    else:
                        f.write(line)

            if updated:
                logger.info(f"Updated {env_key} in .env file")
            else:
                logger.warning(f"{env_key} not found in .env file")

        return {
            "status": "success",
            "vehicle": vehicle,
            "mock_mode": update.enabled,
            "message": f"{vehicle.capitalize()} mock mode {'enabled' if update.enabled else 'disabled'}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update {vehicle} mock mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))
