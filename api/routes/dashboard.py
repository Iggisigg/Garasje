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
    Get current status of all vehicles and recommendation

    Returns:
        JSON with Tesla status and charging recommendation
    """
    from api.app import tesla_service, decision_engine, scheduler

    try:
        # Get Tesla status
        tesla_status = await tesla_service.get_vehicle_status()

        # Calculate recommendation
        recommendation = await decision_engine.calculate_recommendation(tesla_status)

        # Get next scheduled update time
        next_update = scheduler.get_next_run_time()

        return {
            "tesla": tesla_status.to_dict(),
            "recommendation": recommendation.to_dict(),
            "last_updated": datetime.now().isoformat(),
            "next_update": next_update.isoformat() if next_update else None
        }

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
        "mock_mode": config.mock_mode
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
