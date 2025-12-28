# Systemarkitektur - Ladeprioriteringssystem

**Versjon**: 1.0
**Dato**: 2025-12-28
**Status**: Implementert og testet

## 1. Arkitekturoversikt

### 1.1 High-Level Arkitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                             │
│  ┌──────────────────┐          ┌──────────────────────────┐    │
│  │  Dashboard UI    │◄─────────┤  WebSocket Client        │    │
│  │  (HTML/JS/CSS)   │          │  (Auto-reconnect)        │    │
│  └──────────────────┘          └──────────────────────────┘    │
└────────────┬──────────────────────────────┬───────────────────┘
             │ HTTP/HTTPS                    │ WebSocket (ws://)
             ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Routes                                              │   │
│  │  ├─ /api/status                                          │   │
│  │  ├─ /api/update                                          │   │
│  │  ├─ /api/history                                         │   │
│  │  ├─ /api/settings/*                                      │   │
│  │  └─ /ws (WebSocket)                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Core Business Logic                                     │   │
│  │  ├─ DecisionEngine (Ladelogikk)                         │   │
│  │  ├─ ChargingScheduler (APScheduler)                     │   │
│  │  └─ Database (SQLAlchemy + SQLite)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Vehicle Services                                        │   │
│  │  ├─ TeslaFleetService (OAuth, API calls)                │   │
│  │  └─ IoniqService (Mock mode / Future: OBD-II)           │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────┬─────────────────────┘
             │                             │
             │ HTTPS                       │ File I/O
             ▼                             ▼
┌──────────────────────────┐    ┌─────────────────────────┐
│  Tesla Fleet API         │    │  Local Storage          │
│  - auth.tesla.com        │    │  ├─ tesla_cache.json    │
│  - fleet-api.prd.eu.*    │    │  ├─ charging_mgr.db     │
│                          │    │  └─ logs/app.log        │
└──────────────────────────┘    └─────────────────────────┘

┌──────────────────────────┐
│  Nominatim API           │
│  (OpenStreetMap)         │
│  - Reverse Geocoding     │
└──────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | HTML5, JavaScript (ES6+), Tailwind CSS | Responsivt UI, ingen build process |
| **Backend** | Python 3.9+, FastAPI | Async web framework, auto docs |
| **Web Server** | Uvicorn | ASGI server for FastAPI |
| **Database** | SQLite + SQLAlchemy (async) | Enkel persistens, god nok for use case |
| **Scheduler** | APScheduler (AsyncIOScheduler) | Background tasks, cron-like jobber |
| **WebSocket** | FastAPI WebSocket + starlette | Real-time bidirectional kommunikasjon |
| **External APIs** | Tesla Fleet API, Nominatim | Vehicle data, GPS reverse geocoding |
| **Config** | Pydantic Settings, python-dotenv | Type-safe config, .env support |
| **Logging** | Python logging + RotatingFileHandler | Structured logging, file rotation |

## 2. Komponentarkitektur

### 2.1 Application Layers

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer (web/)                      │
│  - templates/dashboard.html                     │
│  - static/js/dashboard.js                       │
│  - static/js/websocket.js                       │
│  - static/css/styles.css                        │
└─────────────────────────────────────────────────┘
                      ▲
                      │ HTTP, WebSocket
                      ▼
┌─────────────────────────────────────────────────┐
│  API Layer (api/)                               │
│  - app.py (FastAPI setup, lifespan)             │
│  - routes/dashboard.py (REST endpoints)         │
│  - routes/websocket.py (WS endpoint)            │
└─────────────────────────────────────────────────┘
                      ▲
                      │ Function calls
                      ▼
┌─────────────────────────────────────────────────┐
│  Business Logic Layer (core/)                   │
│  - decision_engine.py (Recommendations)         │
│  - scheduler.py (Background tasks)              │
│  - database.py (Data access)                    │
└─────────────────────────────────────────────────┘
                      ▲
                      │ Interface calls
                      ▼
┌─────────────────────────────────────────────────┐
│  Service Layer (services/)                      │
│  - base_service.py (Abstract interface)         │
│  - tesla_service.py (Tesla Fleet API)           │
│  - ioniq_service.py (OBD-II / Mock)             │
└─────────────────────────────────────────────────┘
                      ▲
                      │ API calls
                      ▼
┌─────────────────────────────────────────────────┐
│  External Services                              │
│  - Tesla Fleet API                              │
│  - Nominatim (OpenStreetMap)                    │
└─────────────────────────────────────────────────┘
```

### 2.2 Data Flow

#### 2.2.1 Scheduled Update Flow

```
APScheduler Trigger (hourly)
    │
    ▼
ChargingScheduler.update_vehicle_data()
    │
    ├─► TeslaService.get_vehicle_status()
    │       │
    │       ├─► Tesla Fleet API (HTTPS)
    │       │       └─► vehicle_data endpoint
    │       │
    │       ├─► Reverse Geocoding (Nominatim)
    │       │       └─► GPS → Address
    │       │
    │       └─► Return VehicleStatus
    │
    ├─► IoniqService.get_vehicle_status()
    │       └─► Return VehicleStatus (mock / OBD-II)
    │
    ├─► DecisionEngine.calculate_dual_recommendations()
    │       │
    │       ├─► calculate_recommendation(tesla)
    │       ├─► calculate_recommendation(ioniq)
    │       └─► compare_vehicles() → priority
    │
    ├─► Database.save_battery_reading(tesla)
    ├─► Database.save_battery_reading(ioniq)
    ├─► Database.save_recommendation(tesla_rec)
    ├─► Database.save_recommendation(ioniq_rec)
    │
    └─► WebSocketManager.broadcast({
            "tesla": {...},
            "ioniq": {...},
            "recommendations": {...}
        })
            │
            └─► All connected WebSocket clients
                    │
                    └─► Dashboard UI updates
```

#### 2.2.2 Manual Update Flow

```
User clicks "Oppdater nå"
    │
    ▼
dashboard.js: POST /api/update
    │
    ▼
dashboard.py: trigger_update()
    │
    ▼
ChargingScheduler.trigger_manual_update()
    │
    └─► [Same flow as scheduled update]
```

#### 2.2.3 WebSocket Connection Flow

```
Browser loads dashboard
    │
    ▼
websocket.js: new WebSocket('ws://host/ws')
    │
    ▼
websocket.py: ConnectionManager.connect(websocket)
    │
    ├─► Add to active_connections list
    │
    └─► Send initial_status message
            │
            └─► dashboard.js: updateUI(data)

[Connection maintained with ping/pong]

When new data available:
    ChargingScheduler
        │
        ▼
    ConnectionManager.broadcast(data)
        │
        ├─► connection_1.send_json(data)
        ├─► connection_2.send_json(data)
        └─► connection_N.send_json(data)
```

### 2.3 Class Diagrams

#### 2.3.1 Vehicle Services

```
┌─────────────────────────────────────────┐
│  BaseVehicleService (Abstract)          │
├─────────────────────────────────────────┤
│  + vehicle_name: str                    │
│  + mock_mode: bool                      │
│  + logger: Logger                       │
├─────────────────────────────────────────┤
│  + get_vehicle_status(): VehicleStatus  │  (abstract)
│  + authenticate(): None                 │  (abstract)
│  + close(): None                        │  (abstract)
└─────────────────────────────────────────┘
                  △
                  │ inherits
       ┌──────────┴──────────┐
       │                     │
┌──────────────────┐  ┌──────────────────┐
│ TeslaFleetService│  │  IoniqService    │
├──────────────────┤  ├──────────────────┤
│ - client_id      │  │ - obd_adapter    │
│ - client_secret  │  │ - connection     │
│ - access_token   │  │                  │
│ - refresh_token  │  │                  │
│ - vehicle_id     │  │                  │
│ - http_client    │  │                  │
├──────────────────┤  ├──────────────────┤
│ + authenticate() │  │ + authenticate() │
│ + get_vehicle    │  │ + get_vehicle    │
│   _status()      │  │   _status()      │
│ - _refresh_token │  │ - _connect_obd() │
│ - _fetch_from_api│  │ - _get_mock_data │
│ - _get_mock_data │  │                  │
└──────────────────┘  └──────────────────┘
```

#### 2.3.2 Core Business Logic

```
┌─────────────────────────────────────────┐
│  DecisionEngine                         │
├─────────────────────────────────────────┤
│  - charge_threshold: float              │
│  - logger: Logger                       │
├─────────────────────────────────────────┤
│  + calculate_recommendation(            │
│      vehicle: VehicleStatus             │
│    ): Recommendation                    │
│                                         │
│  + calculate_dual_recommendations(      │
│      tesla: VehicleStatus,              │
│      ioniq: VehicleStatus               │
│    ): dict                              │
│                                         │
│  + compare_vehicles(                    │
│      a: VehicleStatus,                  │
│      b: VehicleStatus                   │
│    ): str                               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  ChargingScheduler                      │
├─────────────────────────────────────────┤
│  - tesla_service: TeslaFleetService     │
│  - ioniq_service: IoniqService          │
│  - decision_engine: DecisionEngine      │
│  - database: Database                   │
│  - scheduler: AsyncIOScheduler          │
│  - websocket_broadcast: Callable        │
│  - is_running: bool                     │
├─────────────────────────────────────────┤
│  + start(): None                        │
│  + stop(): None                         │
│  + update_vehicle_data(): None          │
│  + trigger_manual_update(): None        │
│  + cleanup_old_data(): None             │
│  + get_status(): dict                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Database                               │
├─────────────────────────────────────────┤
│  - engine: AsyncEngine                  │
│  - async_session: AsyncSession          │
├─────────────────────────────────────────┤
│  + initialize(): None                   │
│  + save_battery_reading(               │
│      status: VehicleStatus              │
│    ): None                              │
│  + save_recommendation(                 │
│      rec: Recommendation,               │
│      vehicle: str                       │
│    ): None                              │
│  + save_error(                          │
│      service, type, message             │
│    ): None                              │
│  + get_history(hours): List             │
│  + cleanup_old_data(days): None         │
│  + close(): None                        │
└─────────────────────────────────────────┘
```

## 3. Data Models

### 3.1 Domain Objects

```python
@dataclass
class VehicleStatus:
    """Immutable snapshot of vehicle state"""
    vehicle_name: str
    battery_percent: float        # 0.0 - 100.0
    range_km: float
    is_charging: bool
    location: str                 # "home" | "away"
    last_updated: datetime
    is_mock: bool
    charging_rate_kw: Optional[float]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]

    def to_dict(self) -> dict:
        """Serialize for JSON response"""
```

```python
@dataclass
class Recommendation:
    """Charging recommendation with reasoning"""
    action: ChargeAction          # Enum
    reason: str
    timestamp: datetime
    battery_percent: float
    threshold: float
    priority_score: float         # Urgency metric

    def to_dict(self) -> dict:
        """Serialize for JSON response"""
```

```python
class ChargeAction(str, Enum):
    """Possible charging actions"""
    CHARGE = "CHARGE"                    # Start charging
    NO_CHARGE = "NO_CHARGE"              # Don't charge
    CONTINUE_CHARGING = "CONTINUE_CHARGING"  # Keep charging
```

### 3.2 Database Schema

```sql
-- battery_readings
CREATE TABLE battery_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    vehicle TEXT NOT NULL,              -- "Tesla Model Y", "Hyundai Ioniq 5"
    battery_percent REAL NOT NULL,
    range_km REAL NOT NULL,
    location TEXT,                      -- "home", "away"
    is_charging BOOLEAN,
    is_mock BOOLEAN DEFAULT 0,
    charging_rate_kw REAL,
    latitude REAL,
    longitude REAL,
    address TEXT,

    INDEX idx_timestamp (timestamp),
    INDEX idx_vehicle (vehicle)
);

-- recommendations
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    vehicle TEXT NOT NULL,
    action TEXT NOT NULL,               -- "CHARGE", "NO_CHARGE", "CONTINUE_CHARGING"
    reason TEXT,
    battery_percent REAL,
    threshold REAL,
    priority_score REAL,

    INDEX idx_timestamp (timestamp),
    INDEX idx_vehicle (vehicle)
);

-- errors
CREATE TABLE errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    service TEXT NOT NULL,              -- "tesla_service", "scheduler", etc.
    error_type TEXT,                    -- Exception class name
    message TEXT,

    INDEX idx_timestamp (timestamp),
    INDEX idx_service (service)
);
```

### 3.3 Configuration Schema

```python
class Settings(BaseSettings):
    """Pydantic settings with validation"""

    # Tesla Configuration
    tesla_client_id: str
    tesla_client_secret: str
    tesla_cache_file: str = "data/tesla_cache.json"
    tesla_region: str = "EU"
    tesla_mock_mode: bool = True

    # Ioniq Configuration
    ioniq_enabled: bool = True
    ioniq_mock_mode: bool = True
    ioniq_obd_address: str = ""

    # Application Configuration
    update_interval_minutes: int = 60
    charge_threshold_percent: float = 80.0
    database_path: str = "data/charging_manager.db"

    # Web Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## 4. API Design

### 4.1 REST Endpoints

```
GET /
    Description: Serve dashboard HTML
    Response: text/html

GET /api/status
    Description: Get current vehicle status and recommendations
    Response: {
        "tesla": VehicleStatus,
        "ioniq": VehicleStatus | null,
        "tesla_recommendation": Recommendation,
        "ioniq_recommendation": Recommendation | null,
        "priority_vehicle": "Tesla Model Y" | "Hyundai Ioniq 5" | "NONE",
        "last_updated": "2024-12-28T19:45:00",
        "next_update": "2024-12-28T20:45:00"
    }

POST /api/update
    Description: Trigger manual vehicle data update
    Response: {
        "status": "update triggered"
    }

GET /api/history?hours=24
    Description: Get historical battery readings
    Query Params:
        - hours (int): Number of hours to look back
    Response: {
        "readings": [BatteryReading, ...]
    }

GET /api/settings
    Description: Get current settings
    Response: {
        "charge_threshold": 80.0,
        "update_interval_minutes": 60,
        "tesla_mock_mode": true,
        "ioniq_mock_mode": true
    }

PUT /api/settings/threshold?threshold=85
    Description: Update charge threshold
    Query Params:
        - threshold (int): 50-100
    Response: {
        "status": "success",
        "charge_threshold": 85
    }

PUT /api/settings/mock-mode/{vehicle}
    Description: Toggle mock mode for vehicle
    Path Params:
        - vehicle: "tesla" | "ioniq"
    Body: {
        "enabled": true
    }
    Response: {
        "status": "success",
        "vehicle": "tesla",
        "mock_mode": true
    }

GET /api/scheduler
    Description: Get scheduler status
    Response: {
        "is_running": true,
        "update_interval_minutes": 60,
        "next_run_time": "2024-12-28T20:45:00",
        "jobs": [
            {
                "id": "update_vehicles",
                "name": "Update vehicle data",
                "next_run_time": "2024-12-28T20:45:00"
            }
        ]
    }

GET /health
    Description: Health check
    Response: {
        "status": "healthy",
        "tesla_mock_mode": true,
        "ioniq_mock_mode": true,
        "scheduler_running": true
    }
```

### 4.2 WebSocket Protocol

```
Connection: ws://host:port/ws

Client → Server:
    {
        "type": "ping"
    }

Server → Client:
    {
        "type": "pong",
        "timestamp": "2024-12-28T19:45:00"
    }

Server → Client (on connect):
    {
        "type": "initial_status",
        "timestamp": "2024-12-28T19:45:00",
        "tesla": {...},
        "ioniq": {...},
        "tesla_recommendation": {...},
        "ioniq_recommendation": {...},
        "priority_vehicle": "..."
    }

Server → Client (on update):
    {
        "type": "status_update",
        "timestamp": "2024-12-28T19:45:00",
        "tesla": {...},
        "ioniq": {...},
        "tesla_recommendation": {...},
        "ioniq_recommendation": {...},
        "priority_vehicle": "..."
    }
```

## 5. Security Architecture

### 5.1 Authentication & Authorization

```
┌─────────────────────────────────────────┐
│  User Browser                           │
│  - No authentication required           │
│  - Assumes trusted local network        │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  FastAPI Application                    │
│  - CORS: localhost only (prod mode)     │
│  - No user authentication               │
│  - Assumes single-user deployment       │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Tesla Fleet API                        │
│  - OAuth 2.0 with PKCE                  │
│  - Access token (1 hour TTL)            │
│  - Refresh token (stored encrypted)     │
└─────────────────────────────────────────┘
```

### 5.2 OAuth 2.0 Flow (Tesla)

```
1. Authorization Request
   User → Tesla Auth Server
   - client_id
   - redirect_uri
   - scope: openid, offline_access, vehicle_device_data,
            vehicle_cmds, vehicle_charging_cmds, vehicle_location
   - code_challenge (PKCE)
   - code_challenge_method: S256

2. User Login & Consent
   Tesla Auth Server → User
   - Login prompt
   - Consent screen (scope approval)

3. Authorization Code
   Tesla Auth Server → Application (via redirect)
   - code (one-time use)
   - state (CSRF protection)

4. Token Exchange
   Application → Tesla Auth Server
   - code
   - code_verifier (PKCE)
   - client_id
   - client_secret

5. Access Token Response
   Tesla Auth Server → Application
   - access_token (1 hour TTL)
   - refresh_token (long-lived)
   - expires_in: 3600

6. API Requests
   Application → Tesla Fleet API
   - Authorization: Bearer {access_token}

7. Token Refresh (when expired)
   Application → Tesla Auth Server
   - refresh_token
   - client_id

   Response:
   - new access_token
   - new refresh_token (optional)
```

### 5.3 Secrets Management

```
Sensitive Data Storage:

1. .env file (git-ignored):
   - TESLA_CLIENT_ID
   - TESLA_CLIENT_SECRET

2. tesla_cache.json (git-ignored):
   - access_token
   - refresh_token
   - expires_at
   - vehicle_id

3. File Permissions:
   - .env: 600 (owner read/write only)
   - tesla_cache.json: 600
   - data/: 700 (owner only)

4. Git Protection:
   .gitignore:
   - .env
   - data/
   - **/*.json (token cache)
```

## 6. Performance & Scalability

### 6.1 Caching Strategy

```
┌─────────────────────────────────────────┐
│  In-Memory Cache                        │
│  - VehicleStatus (5 min TTL)            │
│  - Used when API unavailable            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  File Cache                             │
│  - OAuth tokens (tesla_cache.json)      │
│  - Persistent across restarts           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Database                               │
│  - Historical data (90 days)            │
│  - No caching (direct queries)          │
└─────────────────────────────────────────┘
```

### 6.2 Rate Limiting

```
Tesla Fleet API:
- Unknown official limit
- Mitigated by:
  - Hourly scheduled updates
  - 5-minute in-memory cache
  - Graceful 429 handling (exponential backoff)

Nominatim API:
- Limit: 1 request per second
- Mitigated by:
  - Only called when GPS changes
  - Typically < 1 call per hour
  - Error handling (fallback to coordinates)
```

### 6.3 Performance Metrics

```
Typical Response Times:

Dashboard Load (first visit):
- HTML: ~50ms
- Static files: ~20ms per file
- /api/status (cached): ~100ms
- Total: ~300ms

Dashboard Load (cached):
- Total: ~100ms (browser cache)

WebSocket Latency:
- Local network: ~10-50ms
- Same machine: ~1-5ms

API Response Times:
- /api/status (cached): ~100ms
- /api/status (fresh Tesla API): ~2-5 seconds
- /api/update (trigger): ~50ms (async)
- /api/history (24h): ~200ms

Database Queries:
- Insert (battery_reading): ~5-10ms
- Select (history, 24h): ~50-100ms
- Cleanup (>90 days): ~500ms
```

### 6.4 Scalability Constraints

```
Current Limitations:

1. Single Server:
   - No load balancing
   - No horizontal scaling
   - OK for single-user

2. SQLite Database:
   - Single writer at a time
   - ~100 requests/second max
   - Sufficient for use case

3. WebSocket Connections:
   - No clustering (single process)
   - ~100 concurrent connections max
   - Far exceeds single-user need

4. Memory Usage:
   - ~50-100MB baseline
   - Scheduler jobs minimal overhead
   - No memory leaks observed

Future Scalability (if needed):
- PostgreSQL for multi-writer
- Redis for distributed caching
- Nginx for load balancing
- Kubernetes for orchestration
```

## 7. Deployment Architecture

### 7.1 Development Environment

```
┌─────────────────────────────────────────┐
│  macOS Developer Machine                │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Python 3.9+ venv                 │ │
│  │  - FastAPI app                    │ │
│  │  - Uvicorn server                 │ │
│  │  - SQLite database                │ │
│  │  - Port: 8000                     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Browser: http://localhost:8000         │
└─────────────────────────────────────────┘
```

### 7.2 Production Environment (Planned v2.0)

```
┌─────────────────────────────────────────┐
│  Raspberry Pi 4 (Local Network)         │
│  IP: 192.168.1.100 (static)             │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  systemd Service                  │ │
│  │  - Auto-start on boot             │ │
│  │  - Restart on failure             │ │
│  │  - Log to journald                │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Python 3.9+ venv                 │ │
│  │  - FastAPI app                    │ │
│  │  - Uvicorn server                 │ │
│  │  - SQLite database                │ │
│  │  - Port: 8000                     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Bluetooth                        │ │
│  │  - OBD-II Dongle connection       │ │
│  │  - Auto-pair on boot              │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
          │
          │ Local Network
          ▼
┌─────────────────────────────────────────┐
│  User Devices                           │
│  - Laptop: http://192.168.1.100:8000    │
│  - Phone: http://charging-mgr.local:8000│
│    (mDNS)                               │
└─────────────────────────────────────────┘
```

### 7.3 Network Architecture

```
┌─────────────────────────────────────────┐
│  Internet                               │
│  - tesla.com (Fleet API)                │
│  - nominatim.org (Geocoding)            │
└─────────────────────────────────────────┘
            │ HTTPS
            ▼
┌─────────────────────────────────────────┐
│  Home Router / Firewall                 │
│  - NAT                                  │
│  - DHCP (static reservation)            │
│  - No port forwarding (security)        │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  Local Network (192.168.1.0/24)         │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Raspberry Pi (Server)           │  │
│  │  192.168.1.100:8000              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Laptop (Client)                 │  │
│  │  192.168.1.101                   │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Phone (Client)                  │  │
│  │  192.168.1.102                   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 8. Error Handling Architecture

### 8.1 Error Propagation

```
Exception Occurs
    │
    ├─► Service Layer
    │       │
    │       ├─► Log error (with traceback)
    │       ├─► Wrap in custom exception
    │       │   (TeslaAPIError, etc.)
    │       └─► Raise to caller
    │
    ├─► Core Layer
    │       │
    │       ├─► Log error
    │       ├─► Save to database (errors table)
    │       ├─► Return fallback data (if available)
    │       └─► Raise (or handle gracefully)
    │
    ├─► API Layer
    │       │
    │       ├─► Catch HTTPException
    │       ├─► Log error
    │       └─► Return JSON error response
    │
    └─► Frontend
            │
            ├─► Display user-friendly message
            ├─► Log to console
            └─► Optional retry button
```

### 8.2 Retry Strategies

```
Tesla API Failures:

1. Token Expired (401):
   - Retry: Yes (after refresh)
   - Max Retries: 1
   - Delay: Immediate

2. Rate Limit (429):
   - Retry: Yes (exponential backoff)
   - Max Retries: 3
   - Delays: 1s, 2s, 4s

3. Server Error (5xx):
   - Retry: Yes (exponential backoff)
   - Max Retries: 3
   - Delays: 2s, 4s, 8s
   - Fallback: Cached data

4. Vehicle Asleep (408):
   - Retry: No
   - Fallback: Cached data
   - Note: Don't wake vehicle

WebSocket Disconnect:
   - Auto-reconnect: Yes
   - Delay: 3 seconds
   - Max Retries: Infinite
   - Exponential: No (constant 3s)
```

## 9. Monitoring & Observability

### 9.1 Logging Architecture

```
┌─────────────────────────────────────────┐
│  Application Code                       │
│  - logger.debug("...")                  │
│  - logger.info("...")                   │
│  - logger.warning("...")                │
│  - logger.error("...", exc_info=True)   │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Python Logging                         │
│  - Formatter: timestamp + level + msg   │
│  - Filter: By log level                 │
└─────────────────────────────────────────┘
          │                │
          ▼                ▼
┌──────────────┐  ┌────────────────────┐
│  Console     │  │  File (Rotating)   │
│  - INFO+     │  │  - DEBUG+          │
│  - Real-time │  │  - 10MB max        │
│              │  │  - 3 backups       │
└──────────────┘  └────────────────────┘
                          │
                          ▼
                  ┌────────────────────┐
                  │  data/logs/app.log │
                  │  - Persistent      │
                  │  - Grep-able       │
                  └────────────────────┘
```

### 9.2 Metrics (Future)

```
Potential Metrics (not implemented):

- API Response Times (histogram)
- Database Query Times (histogram)
- WebSocket Connection Count (gauge)
- Scheduler Job Success Rate (counter)
- Cache Hit Rate (counter)
- Battery Level Over Time (gauge)
- Error Rate by Service (counter)

Tools:
- Prometheus (metrics collection)
- Grafana (visualization)
```

## 10. Design Patterns Used

### 10.1 Creational Patterns

**Abstract Factory Pattern** (services/):
- `BaseVehicleService` defines interface
- `TeslaFleetService`, `IoniqService` implement interface
- Allows swapping vehicle implementations

**Singleton Pattern** (api/app.py):
- Global service instances (tesla_service, ioniq_service)
- Initialized once in lifespan
- Shared across all requests

### 10.2 Structural Patterns

**Adapter Pattern** (services/):
- Adapts external APIs to common `VehicleStatus` interface
- Tesla Fleet API → VehicleStatus
- OBD-II → VehicleStatus

**Facade Pattern** (api/routes/):
- Simplified API for complex subsystems
- Dashboard routes hide complexity of scheduler, database, services

### 10.3 Behavioral Patterns

**Observer Pattern** (WebSocket):
- ConnectionManager maintains observer list
- Broadcast method notifies all observers
- Clients subscribe/unsubscribe dynamically

**Strategy Pattern** (decision_engine.py):
- Different recommendation strategies
- Single vehicle vs dual vehicle logic
- Configurable threshold strategy

**Template Method Pattern** (services/base_service.py):
- `get_vehicle_status()` defines template
- Subclasses implement specific steps
- Mock mode vs real mode as variations

## 11. Future Architecture Considerations

### 11.1 Microservices (v3.0+)

```
Potential Split:

┌─────────────────┐
│  API Gateway    │ ← Nginx reverse proxy
└─────────────────┘
        │
        ├──► Vehicle Service (Tesla)
        ├──► Vehicle Service (Ioniq)
        ├──► Decision Service
        ├──► Notification Service
        └──► History Service (PostgreSQL)

Benefits:
- Independent scaling
- Technology heterogeneity
- Fault isolation

Drawbacks:
- Complexity overkill for single-user
- Network latency
- Deployment overhead
```

### 11.2 Event-Driven Architecture (v3.0+)

```
Event Bus (Redis Pub/Sub or RabbitMQ):

Events:
- VehicleStatusUpdated
- RecommendationChanged
- BatteryLevelCritical
- ChargingStarted
- ChargingCompleted

Subscribers:
- WebSocket broadcaster
- Database logger
- Notification service
- Smart switch controller
```

### 11.3 Cloud Deployment (Out of Scope)

```
AWS/Azure/GCP Architecture:

┌─────────────────────────────────────┐
│  CloudFront / CDN                   │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Load Balancer (ALB)                │
└─────────────────────────────────────┘
                │
                ├──► ECS/EKS (FastAPI)
                │
┌─────────────────────────────────────┐
│  RDS PostgreSQL                     │
└─────────────────────────────────────┘

Cost: ~$50-100/month
Not justified for single-user hobbyist app
```

---

**Dokumentert**: 2025-12-28
**Versjon**: 1.0
**Forfatter**: Sigurd Instanes (med Claude Code)
