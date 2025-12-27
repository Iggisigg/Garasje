"""
FastAPI application setup
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from config import config
from services.tesla_service import TeslaService
from core.decision_engine import DecisionEngine
from core.database import Database
from core.scheduler import ChargingScheduler
from utils.logger import setup_logger, get_logger

# Initialize logger
logger = setup_logger(log_level=config.log_level)

# Global instances (will be initialized in lifespan)
tesla_service: TeslaService = None
decision_engine: DecisionEngine = None
database: Database = None
scheduler: ChargingScheduler = None
templates: Jinja2Templates = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Charging Manager")
    logger.info("=" * 60)

    global tesla_service, decision_engine, database, scheduler, templates

    # Ensure directories exist
    config.ensure_directories()

    # Initialize database
    logger.info("Initializing database...")
    db_path = config.database_path
    if not db_path.startswith("sqlite"):
        db_path = f"sqlite:///{db_path}"
    database = Database(db_path)
    await database.initialize()

    # Initialize Tesla service
    logger.info(f"Initializing Tesla service (mock_mode={config.mock_mode})...")
    tesla_service = TeslaService(
        email=config.tesla_email,
        cache_file=config.tesla_cache_file,
        mock_mode=config.mock_mode
    )

    # Authenticate if not in mock mode
    if not config.mock_mode:
        try:
            await tesla_service.authenticate()
        except Exception as e:
            logger.error(f"Tesla authentication failed: {e}")
            logger.warning("Continuing in mock mode")
            tesla_service.mock_mode = True

    # Initialize decision engine
    logger.info("Initializing decision engine...")
    decision_engine = DecisionEngine(
        charge_threshold=config.charge_threshold_percent
    )

    # Initialize templates
    templates = Jinja2Templates(directory="web/templates")

    # Initialize and start scheduler
    logger.info("Starting scheduler...")
    from api.routes.websocket import websocket_manager
    scheduler = ChargingScheduler(
        tesla_service=tesla_service,
        decision_engine=decision_engine,
        database=database,
        update_interval_minutes=config.update_interval_minutes,
        websocket_broadcast=websocket_manager.broadcast
    )
    scheduler.start()

    logger.info("✓ Charging Manager started successfully")
    logger.info(f"Dashboard available at: http://{config.host}:{config.port}")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down Charging Manager...")

    if scheduler:
        scheduler.stop()

    if tesla_service:
        await tesla_service.close()

    if database:
        await database.close()

    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Ladeprioriteringssystem",
    description="Automatisk ladeprioriteringssystem for elbiler",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (allow local network access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path("web/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Import and include routers
from api.routes import dashboard, websocket

app.include_router(dashboard.router)
app.include_router(websocket.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mock_mode": config.mock_mode,
        "scheduler_running": scheduler.is_running if scheduler else False
    }
