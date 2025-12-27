"""
Background scheduler for automatic vehicle data updates
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from services.tesla_service import TeslaService
from core.decision_engine import DecisionEngine
from core.database import Database
from utils.logger import get_logger
from utils.exceptions import ChargingManagerError

logger = get_logger(__name__)


class ChargingScheduler:
    """Manages scheduled tasks for the charging manager"""

    def __init__(
        self,
        tesla_service: TeslaService,
        decision_engine: DecisionEngine,
        database: Database,
        update_interval_minutes: int = 60,
        websocket_broadcast: Optional[Callable] = None
    ):
        """
        Initialize scheduler

        Args:
            tesla_service: Tesla service instance
            decision_engine: Decision engine instance
            database: Database instance
            update_interval_minutes: How often to update vehicle data
            websocket_broadcast: Optional function to broadcast updates via WebSocket
        """
        self.tesla_service = tesla_service
        self.decision_engine = decision_engine
        self.database = database
        self.update_interval_minutes = update_interval_minutes
        self.websocket_broadcast = websocket_broadcast

        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.logger = logger

    async def update_vehicle_data(self):
        """
        Update vehicle data and calculate recommendation

        This is the main scheduled task that runs periodically
        """
        self.logger.info("Running scheduled vehicle update...")

        try:
            # Fetch Tesla data
            self.logger.debug("Fetching Tesla status...")
            tesla_status = await self.tesla_service.get_vehicle_status()
            self.logger.info(f"Tesla: {tesla_status}")

            # Save to database
            await self.database.save_battery_reading(tesla_status)

            # Calculate recommendation
            self.logger.debug("Calculating recommendation...")
            recommendation = await self.decision_engine.calculate_recommendation(tesla_status)
            self.logger.info(f"Recommendation: {recommendation}")

            # Save recommendation
            await self.database.save_recommendation(recommendation, tesla_status.vehicle_name)

            # Broadcast update via WebSocket if available
            if self.websocket_broadcast:
                await self.websocket_broadcast({
                    "type": "status_update",
                    "timestamp": datetime.now().isoformat(),
                    "tesla": tesla_status.to_dict(),
                    "recommendation": recommendation.to_dict()
                })

            self.logger.info("✓ Scheduled update completed successfully")

        except Exception as e:
            self.logger.error(f"Scheduled update failed: {e}")
            await self.database.save_error("scheduler", type(e).__name__, str(e))

            # Don't raise - we don't want to stop the scheduler
            # It will try again at the next interval

    async def cleanup_old_data(self):
        """
        Clean up old database entries

        Runs daily to keep database size manageable
        """
        self.logger.info("Running database cleanup...")

        try:
            await self.database.cleanup_old_data(days=90)
            self.logger.info("✓ Database cleanup completed")

        except Exception as e:
            self.logger.error(f"Database cleanup failed: {e}")

    def start(self):
        """Start the scheduler with all configured jobs"""

        if self.is_running:
            self.logger.warning("Scheduler already running")
            return

        self.logger.info("Starting scheduler...")

        # Job 1: Update vehicle data periodically
        self.scheduler.add_job(
            self.update_vehicle_data,
            trigger=IntervalTrigger(minutes=self.update_interval_minutes),
            id="update_vehicles",
            name="Update vehicle data",
            replace_existing=True
        )

        # Job 2: Run update immediately on startup
        self.scheduler.add_job(
            self.update_vehicle_data,
            id="startup_update",
            name="Startup update",
            replace_existing=True
        )

        # Job 3: Daily cleanup at 3 AM
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=CronTrigger(hour=3, minute=0),
            id="daily_cleanup",
            name="Daily database cleanup",
            replace_existing=True
        )

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        self.logger.info(f"✓ Scheduler started (update interval: {self.update_interval_minutes} min)")

    def stop(self):
        """Stop the scheduler"""

        if not self.is_running:
            self.logger.warning("Scheduler not running")
            return

        self.logger.info("Stopping scheduler...")
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        self.logger.info("✓ Scheduler stopped")

    async def trigger_manual_update(self):
        """
        Manually trigger a vehicle data update

        This is called when user clicks "Oppdater nå" button
        """
        self.logger.info("Manual update triggered")
        await self.update_vehicle_data()

    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get the next scheduled run time

        Returns:
            Next run time or None if scheduler not running
        """
        if not self.is_running:
            return None

        job = self.scheduler.get_job("update_vehicles")
        if job and job.next_run_time:
            return job.next_run_time

        return None

    def get_status(self) -> dict:
        """
        Get scheduler status

        Returns:
            Dictionary with scheduler information
        """
        next_run = self.get_next_run_time()

        return {
            "is_running": self.is_running,
            "update_interval_minutes": self.update_interval_minutes,
            "next_run_time": next_run.isoformat() if next_run else None,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }
