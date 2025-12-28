# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an EV charging priority management system built in Python with FastAPI. The system monitors battery levels for electric vehicles (currently Tesla Model Y, with planned support for Hyundai Ioniq 5) and provides charging recommendations based on configurable thresholds. The application features a real-time web dashboard with WebSocket updates.

**Language Notes**: Code comments and UI text are in Norwegian. Variable names and documentation are in English.

## Common Commands

### Running the Application

```bash
# Start the server (creates .env from .env.example if missing)
python main.py

# Access dashboard
open http://localhost:8000
```

### Tesla Fleet API Setup (First-Time Only)

```bash
# Step 1: Register application with Tesla Fleet API
python scripts/register_tesla_account.py

# Step 2: Complete OAuth flow to get access tokens
python scripts/setup_tesla_fleet.py

# Step 3: Update .env to use real data
# Set TESLA_MOCK_MODE=false in .env
```

**Important**: After adding new OAuth scopes (like `vehicle_location`), you must re-run `setup_tesla_fleet.py` to get a new token with updated permissions.

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with debug logging
# Set LOG_LEVEL=DEBUG in .env, then:
python main.py

# Kill server running on port 8000
lsof -ti:8000 | xargs kill -9
```

### Mock Mode Testing

The system supports independent mock modes for each vehicle:
- `TESLA_MOCK_MODE=true` - Use simulated Tesla data (sine wave pattern)
- `IONIQ_MOCK_MODE=true` - Use simulated Ioniq data (cosine wave pattern)

Mock mode is useful for testing without API access or physical hardware.

## Architecture

### Application Lifecycle

```
main.py → uvicorn → api/app.py (lifespan) → Services/Scheduler/Database init
                                          → FastAPI routes/WebSocket
```

**Startup sequence** (`api/app.py:lifespan`):
1. Initialize SQLite database
2. Initialize vehicle services (Tesla, Ioniq if enabled)
3. Authenticate Tesla (if not in mock mode)
4. Initialize decision engine with charge threshold
5. Start APScheduler with three jobs:
   - Immediate startup update
   - Periodic updates (default: hourly)
   - Daily cleanup at 3 AM
6. FastAPI server starts serving requests

**Shutdown sequence**:
- Stop scheduler
- Close vehicle service connections
- Close database connection

### Core Components

**Services** (`services/`):
- `base_service.py` - Abstract base class defining `get_vehicle_status()` interface
- `tesla_service.py` - Tesla Fleet API integration with OAuth 2.0 + PKCE
- `ioniq_service.py` - Hyundai Ioniq 5 service (currently mock only, OBD-II planned)

All services implement the same interface returning `VehicleStatus` objects, making mock/real modes transparent to the rest of the system.

**Decision Engine** (`core/decision_engine.py`):
- `calculate_recommendation(vehicle)` - Single vehicle: CHARGE, NO_CHARGE, or CONTINUE_CHARGING
- `calculate_dual_recommendations(tesla, ioniq)` - Both vehicles with priority logic
- `compare_vehicles(a, b)` - Determines which vehicle should charge first

Priority algorithm:
1. If neither needs charging → "NONE"
2. If only one needs charging → that vehicle
3. If both need charging → compare `priority_score` (urgency metric)
4. Tiebreaker → lowest battery percentage

**Scheduler** (`core/scheduler.py`):
- Uses APScheduler (AsyncIOScheduler)
- Three scheduled jobs: periodic updates, startup update, daily cleanup
- `update_vehicle_data()` - Main job: fetch data → save to DB → calculate recommendations → broadcast via WebSocket
- Manual updates bypass scheduler via `trigger_manual_update()`

**Database** (`core/database.py`):
- SQLite with SQLAlchemy async
- Three tables: `battery_readings`, `recommendations`, `errors`
- Auto-cleanup: deletes entries older than 90 days

**WebSocket** (`api/routes/websocket.py`):
- Connection manager with broadcast capability
- Message types: `initial_status`, `status_update`, `ping/pong`
- Reconnection logic on client side (3s exponential backoff)

### Tesla Fleet API Integration

**Authentication Flow**:
1. OAuth 2.0 with PKCE (Proof Key for Code Exchange)
2. Required scopes: `openid`, `offline_access`, `vehicle_device_data`, `vehicle_cmds`, `vehicle_charging_cmds`, `vehicle_location`
3. Tokens cached in `data/tesla_cache.json`
4. Auto-refresh when token expires (uses refresh token)
5. Region-specific endpoints (EU vs NA)

**API Calls**:
- `GET /api/1/vehicles` - List vehicles, get vehicle ID
- `GET /api/1/vehicles/{id}/vehicle_data?endpoints=...` - Get battery, GPS, charge state
- Handles 408 response (vehicle asleep) gracefully

**GPS Location**:
- Extracts `latitude`/`longitude` from `drive_state`
- Reverse geocodes using Nominatim (OpenStreetMap) API
- Displays address in Norwegian format: "Gate 123, Oslo, 0123"

### Configuration Management

**Two-tier config system**:
1. **Environment variables** (`.env`) - User-editable configuration
2. **Pydantic Settings** (`config.py`) - Validated, typed config object

Runtime config updates (e.g., toggle mock mode via dashboard) modify both:
- In-memory `config` object
- Service instance `mock_mode` attribute
- `.env` file for persistence

### Frontend Architecture

**Stack**: Vanilla JavaScript + Tailwind CSS (no build process)

**Files**:
- `dashboard.html` - Two-column grid layout for Tesla/Ioniq cards
- `dashboard.js` - UI updates, fetch API calls, event handlers
- `websocket.js` - WebSocket connection management with auto-reconnect

**Data flow**:
1. Initial load: `GET /api/status` → populate UI
2. Real-time: WebSocket receives `status_update` → `updateUI()`
3. Manual update: Button click → `POST /api/update` → scheduler runs → WebSocket broadcast

**UI Components**:
- Vehicle cards: battery gauge, range, location (address or GPS), charging status
- Priority recommendation banner (color-coded)
- Settings panel: charge threshold slider, mock mode toggles (iOS-style)
- WebSocket connection indicator

### Error Handling Patterns

**Service Layer**:
- Custom exceptions: `TeslaAPIError`, `TeslaAuthenticationError`
- Graceful degradation: if API fails and cache exists, return stale data
- Token refresh failures trigger re-authentication

**Scheduler**:
- Exceptions caught and logged, don't stop scheduler
- Errors saved to database via `save_error()`
- Next scheduled run continues normally

**API Layer**:
- FastAPI exception handlers return JSON errors
- WebSocket disconnects handled by client auto-reconnect

## Key Technical Details

### Tesla OAuth Token Refresh

Token refresh is handled automatically in `authenticate()`:
- Checks if token expires within 60 seconds
- Uses lock (`asyncio.Lock`) to prevent concurrent refreshes
- Double-check pattern after acquiring lock (another task may have refreshed)
- Falls back to manual re-authentication if refresh token invalid

### Mock Data Generation

Mock data uses time-based mathematical functions for realistic variation:
- **Tesla**: `sin(time/3600) * 20` - oscillates ±20% around 70% baseline
- **Ioniq**: `cos(time/3600 * 1.2) * 25` - different frequency, ±25% around 65%

This creates different battery patterns for testing dual-vehicle logic.

### Database Schema

**battery_readings**:
- Stores all vehicle status snapshots
- Indexed by timestamp for history queries
- Includes mock flag for filtering test data

**recommendations**:
- Stores decision engine outputs
- Links to vehicle via name (not ID, for flexibility)
- Includes full reasoning for auditability

**errors**:
- Structured error logging
- Separate from app logs for programmatic analysis

### WebSocket Broadcast Pattern

```python
# In scheduler:
await websocket_broadcast({
    "type": "status_update",
    "tesla": tesla_status.to_dict(),
    "ioniq": ioniq_status.to_dict(),
    "tesla_recommendation": rec_tesla.to_dict(),
    "ioniq_recommendation": rec_ioniq.to_dict(),
    "priority_vehicle": "Tesla Model Y"  # or "NONE"
})

# ConnectionManager broadcasts to all active connections:
for connection in active_connections:
    await connection.send_json(message)
```

## Common Pitfalls

### OAuth Scope Changes
If you add new Tesla API scopes (e.g., `vehicle_location`), updating `scripts/setup_tesla_fleet.py` is NOT enough. You must:
1. Update scope in **both** `setup_tesla_fleet.py` AND `register_tesla_account.py`
2. Re-run `python scripts/setup_tesla_fleet.py` to get a new token
3. User must approve new scopes in Tesla OAuth consent screen

### Mock Mode Toggle Not Persisting
When adding API endpoints to update mock mode, you must update THREE places:
1. In-memory `config.tesla_mock_mode` / `config.ioniq_mock_mode`
2. Service instance: `tesla_service.mock_mode` / `ioniq_service.mock_mode`
3. `.env` file for persistence across restarts

Missing any of these causes state inconsistencies.

### WebSocket State Import
In FastAPI 0.108.0, `WebSocketState` is in `starlette.websockets`, not `fastapi`:
```python
from starlette.websockets import WebSocketState  # Correct
from fastapi import WebSocketState  # Wrong
```

### Priority Logic Edge Cases
The decision engine must treat `CONTINUE_CHARGING` the same as `CHARGE` when comparing vehicles. Use a helper function:
```python
def needs_charging(action: ChargeAction) -> bool:
    return action in (ChargeAction.CHARGE, ChargeAction.CONTINUE_CHARGING)
```

### GPS Location Returns None
If Tesla API returns GPS coordinates as `None`:
- Check OAuth token has `vehicle_location` scope
- Vehicle may be in a location with poor GPS signal
- API returns 403 if scope is missing - check logs for "Unauthorized missing scopes vehicle_location"

## File Organization

```
/
├── main.py                     # Entry point
├── config.py                   # Pydantic settings
├── requirements.txt
├── .env                        # User config (git-ignored)
├── .env.example               # Template
│
├── services/                   # Vehicle data sources
│   ├── base_service.py         # Abstract interface
│   ├── tesla_service.py        # Tesla Fleet API
│   └── ioniq_service.py        # Ioniq 5 (mock only for now)
│
├── models/                     # Data classes
│   ├── vehicle.py              # VehicleStatus
│   └── recommendation.py       # Recommendation, ChargeAction enum
│
├── core/                       # Business logic
│   ├── database.py             # SQLAlchemy async
│   ├── decision_engine.py      # Charging logic
│   └── scheduler.py            # APScheduler
│
├── api/                        # FastAPI app
│   ├── app.py                  # FastAPI setup, lifespan
│   └── routes/
│       ├── dashboard.py        # REST endpoints
│       └── websocket.py        # WebSocket + ConnectionManager
│
├── web/                        # Frontend
│   ├── templates/dashboard.html
│   └── static/
│       ├── css/styles.css
│       └── js/
│           ├── dashboard.js    # UI logic
│           └── websocket.js    # WS client
│
├── utils/
│   ├── logger.py               # Logging setup
│   ├── exceptions.py           # Custom exceptions
│   └── geocoding.py            # Reverse geocoding (Nominatim)
│
├── scripts/
│   ├── setup_tesla_fleet.py         # OAuth flow
│   ├── register_tesla_account.py    # Partner registration
│   └── generate_keys.py             # Public key generation
│
└── data/                       # Runtime (git-ignored)
    ├── charging_manager.db     # SQLite
    ├── tesla_cache.json        # OAuth tokens
    └── logs/app.log            # Application logs
```

## API Endpoints Reference

**Dashboard**:
- `GET /` - Serve dashboard HTML
- `GET /api/status` - Current vehicle status + recommendations
- `POST /api/update` - Trigger manual update
- `GET /api/history?hours=24` - Battery history

**Settings**:
- `GET /api/settings` - Get current settings
- `PUT /api/settings/threshold?threshold=85` - Update charge threshold
- `PUT /api/settings/mock-mode/{vehicle}` - Toggle mock mode (body: `{"enabled": true}`)

**System**:
- `GET /api/scheduler` - Scheduler status + next run time
- `GET /health` - Health check
- `WS /ws` - WebSocket connection

## Development Workflow

### Adding a New Vehicle Service

1. Create `services/new_vehicle_service.py` extending `BaseVehicleService`
2. Implement `async def get_vehicle_status() -> VehicleStatus`
3. Add mock mode support with unique data pattern
4. Update `config.py` with new vehicle config variables
5. Initialize service in `api/app.py:lifespan`
6. Update `DecisionEngine` to handle 3+ vehicles
7. Update dashboard UI to display new vehicle card
8. Update scheduler to fetch new vehicle data

### Adding a New OAuth Scope

1. Update `scripts/setup_tesla_fleet.py` - add scope to line 52
2. Update `scripts/register_tesla_account.py` - add scope to line 33
3. Delete `data/tesla_cache.json`
4. Re-run: `python scripts/setup_tesla_fleet.py`
5. Test that new API data is accessible

### Modifying Decision Logic

1. Update `core/decision_engine.py`
2. Consider impact on `calculate_recommendation()` and `compare_vehicles()`
3. Update database schema if new recommendation fields needed
4. Update frontend to display new recommendation details

## Future Expansion (v2.0)

**Ioniq 5 OBD-II Integration**:
- Use `python-obd` library for Bluetooth OBD-II adapter communication
- Research Hyundai-specific PIDs for EV battery data
- Implement real `IoniqService.get_vehicle_status()` (currently mock only)
- Add Bluetooth pairing logic and connection management

**Raspberry Pi Deployment**:
- Create systemd service file
- Setup static IP or mDNS for dashboard access
- Handle Bluetooth OBD-II dongle on Pi

**Smart Switch Integration**:
- Add switch control logic based on priority recommendation
- Implement safety checks (don't switch while charging)
- Add manual override capability
