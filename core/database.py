"""
Database operations using SQLAlchemy with async support
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager

from models.vehicle import VehicleStatus
from models.recommendation import Recommendation, ChargeAction
from utils.logger import get_logger
from utils.exceptions import DatabaseError

logger = get_logger(__name__)

Base = declarative_base()


class BatteryReading(Base):
    """Battery reading database model"""
    __tablename__ = "battery_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    vehicle = Column(String(50), nullable=False, index=True)
    battery_percent = Column(Float, nullable=False)
    range_km = Column(Float, nullable=False)
    location = Column(String(20), nullable=False)
    is_charging = Column(Boolean, nullable=False)
    is_mock = Column(Boolean, default=False)


class RecommendationRecord(Base):
    """Recommendation database model"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    vehicle = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    reason = Column(String(500), nullable=False)
    battery_percent = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)


class ErrorLog(Base):
    """Error log database model"""
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    service = Column(String(50), nullable=False)
    error_type = Column(String(100), nullable=False)
    message = Column(String(1000), nullable=False)


class Database:
    """Database manager with async support"""

    def __init__(self, database_url: str):
        """
        Initialize database connection

        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite+aiosqlite:///data/charging_manager.db)
        """
        self.database_url = database_url
        self.engine = None
        self.session_maker = None
        self._in_error_handler = False  # Prevent recursive error logging

    async def initialize(self):
        """Initialize database engine and create tables"""
        try:
            # Convert sqlite:// to sqlite+aiosqlite://
            if self.database_url.startswith("sqlite:///"):
                url = self.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            else:
                url = self.database_url

            self.engine = create_async_engine(url, echo=False)
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info(f"Database initialized: {self.database_url}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        if not self.session_maker:
            raise DatabaseError("Database not initialized. Call initialize() first.")

        session = self.session_maker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def save_battery_reading(self, status: VehicleStatus):
        """
        Save battery reading to database

        Args:
            status: Vehicle status to save
        """
        try:
            async with self.get_session() as session:
                reading = BatteryReading(
                    timestamp=status.last_updated,
                    vehicle=status.vehicle_name,
                    battery_percent=status.battery_percent,
                    range_km=status.range_km,
                    location=status.location,
                    is_charging=status.is_charging,
                    is_mock=status.is_mock
                )
                session.add(reading)

            logger.debug(f"Saved battery reading: {status.vehicle_name} - {status.battery_percent}%")

        except Exception as e:
            logger.error(f"Failed to save battery reading: {e}")
            # Fire-and-forget error logging to avoid blocking
            if not self._in_error_handler:
                asyncio.create_task(self.save_error("database", "BatteryReadingError", str(e)))

    async def save_recommendation(self, recommendation: Recommendation, vehicle_name: str):
        """
        Save recommendation to database

        Args:
            recommendation: Recommendation to save
            vehicle_name: Name of vehicle this recommendation is for
        """
        try:
            async with self.get_session() as session:
                record = RecommendationRecord(
                    timestamp=recommendation.timestamp,
                    vehicle=vehicle_name,
                    action=recommendation.action.value,
                    reason=recommendation.reason,
                    battery_percent=recommendation.battery_percent,
                    threshold=recommendation.threshold
                )
                session.add(record)

            logger.debug(f"Saved recommendation: {vehicle_name} - {recommendation.action.value}")

        except Exception as e:
            logger.error(f"Failed to save recommendation: {e}")
            # Fire-and-forget error logging to avoid blocking
            if not self._in_error_handler:
                asyncio.create_task(self.save_error("database", "RecommendationError", str(e)))

    async def save_error(self, service: str, error_type: str, message: str):
        """
        Save error to database

        Args:
            service: Service that generated the error
            error_type: Type of error
            message: Error message
        """
        # Prevent recursive error handling
        if self._in_error_handler:
            logger.warning(f"Skipping recursive error save: {service} - {error_type}")
            return

        try:
            self._in_error_handler = True
            async with self.get_session() as session:
                error = ErrorLog(
                    timestamp=datetime.now(timezone.utc),
                    service=service,
                    error_type=error_type,
                    message=message
                )
                session.add(error)

            logger.debug(f"Saved error: {service} - {error_type}")

        except Exception as e:
            # Don't recurse - just log to console
            logger.error(f"Failed to save error to database: {e}")
        finally:
            self._in_error_handler = False

    async def get_history(self, vehicle: Optional[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get battery reading history

        Args:
            vehicle: Filter by vehicle name (optional)
            hours: Number of hours of history to retrieve

        Returns:
            List of battery readings as dictionaries
        """
        try:
            async with self.get_session() as session:
                since = datetime.now(timezone.utc) - timedelta(hours=hours)

                stmt = select(BatteryReading).where(BatteryReading.timestamp >= since)
                if vehicle:
                    stmt = stmt.where(BatteryReading.vehicle == vehicle)

                stmt = stmt.order_by(BatteryReading.timestamp.desc())

                result = await session.execute(stmt)
                readings = result.scalars().all()

                return [
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "vehicle": r.vehicle,
                        "battery_percent": r.battery_percent,
                        "range_km": r.range_km,
                        "location": r.location,
                        "is_charging": r.is_charging,
                        "is_mock": r.is_mock
                    }
                    for r in readings
                ]

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            raise DatabaseError(f"Failed to retrieve history: {e}")

    async def get_latest_reading(self, vehicle: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent battery reading for a vehicle

        Args:
            vehicle: Vehicle name

        Returns:
            Latest reading as dictionary, or None if no readings found
        """
        try:
            async with self.get_session() as session:
                stmt = (
                    select(BatteryReading)
                    .where(BatteryReading.vehicle == vehicle)
                    .order_by(BatteryReading.timestamp.desc())
                    .limit(1)
                )

                result = await session.execute(stmt)
                reading = result.scalar_one_or_none()

                if reading:
                    return {
                        "timestamp": reading.timestamp.isoformat(),
                        "vehicle": reading.vehicle,
                        "battery_percent": reading.battery_percent,
                        "range_km": reading.range_km,
                        "location": reading.location,
                        "is_charging": reading.is_charging,
                        "is_mock": reading.is_mock
                    }
                return None

        except Exception as e:
            logger.error(f"Failed to get latest reading: {e}")
            return None

    async def cleanup_old_data(self, days: int = 90):
        """
        Delete data older than specified days

        Args:
            days: Number of days to keep
        """
        try:
            async with self.get_session() as session:
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)

                # Delete old battery readings
                await session.execute(
                    BatteryReading.__table__.delete().where(BatteryReading.timestamp < cutoff)
                )

                # Delete old recommendations
                await session.execute(
                    RecommendationRecord.__table__.delete().where(RecommendationRecord.timestamp < cutoff)
                )

                # Delete old errors
                await session.execute(
                    ErrorLog.__table__.delete().where(ErrorLog.timestamp < cutoff)
                )

            logger.info(f"Cleaned up data older than {days} days")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
