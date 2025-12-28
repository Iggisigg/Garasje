# Prosjektplan - Ladeprioriteringssystem

**Prosjektnavn**: Ladeprioriteringssystem for Elbiler
**Versjon**: 1.0
**Sist oppdatert**: 2025-12-28
**Prosjektleder**: Sigurd Instanes

## 1. Prosjektsammendrag

### 1.1 Mål
Utvikle et automatisk ladeprioriteringssystem som overvåker batterinivået til flere elbiler og anbefaler hvilken bil som bør lades først. Systemet skal være brukervennlig, pålitelig og utvidbart.

### 1.2 Suksesskriterier
- ✅ MVP (v1.0) ferdigstilt med Tesla Model Y integrasjon
- ✅ Web dashboard tilgjengelig for lokal bruk
- ✅ Sanntidsoppdateringer via WebSocket
- ✅ Mock mode for testing
- ⏳ v2.0 med Ioniq 5 OBD-II (Q2 2025)
- ⏳ Raspberry Pi deployment (Q2 2025)

### 1.3 Tidsramme
- **Start**: November 2024
- **MVP (v1.0)**: Desember 2024 ✅
- **v2.0**: Q2 2025 (planlagt)
- **v3.0**: Q4 2025 (planlagt)

## 2. Milepæler

### Fase 1: Grunnleggende Oppsett ✅
**Periode**: Uke 1-2 (November 2024)
**Status**: Fullført

**Leveranser**:
- [x] Prosjektstruktur opprettet
- [x] Git repository initialisert
- [x] .gitignore konfigurert (.env, data/, __pycache__)
- [x] requirements.txt med alle dependencies
- [x] config.py med Pydantic Settings
- [x] .env.example template
- [x] Logger setup med rotating files

**Nøkkelbeslutninger**:
- FastAPI valgt for backend (async support, WebSocket, god dokumentasjon)
- SQLite valgt for database (enkel, ingen ekstra tjenester)
- Vanilla JS + Tailwind CSS for frontend (ingen build process)
- APScheduler for background tasks

### Fase 2: Database og Modeller ✅
**Periode**: Uke 2-3 (November 2024)
**Status**: Fullført

**Leveranser**:
- [x] VehicleStatus dataklasse
- [x] Recommendation dataklasse
- [x] ChargeAction enum
- [x] SQLAlchemy database setup
- [x] Tabeller: battery_readings, recommendations, errors
- [x] Database migrations (manuell via SQLAlchemy)
- [x] CRUD operasjoner
- [x] Cleanup job for gamle data

**Tekniske detaljer**:
- Async SQLAlchemy med aiosqlite
- Indexed timestamps for ytelse
- Soft deletes (90 dagers retention)

### Fase 3: Tesla API Integrasjon ✅
**Periode**: Uke 3-5 (November-Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] BaseVehicleService abstract class
- [x] TeslaFleetService implementasjon
- [x] OAuth 2.0 PKCE flow
- [x] Token caching til fil
- [x] Auto-refresh mekanisme
- [x] Region support (EU/NA)
- [x] Mock mode for testing
- [x] scripts/setup_tesla_fleet.py
- [x] scripts/register_tesla_account.py
- [x] Error handling (401, 403, 408, 429, 5xx)

**Utfordringer møtt**:
1. **Token refresh race condition**: Løst med asyncio.Lock
2. **Vehicle asleep (408)**: Returnerer cached data
3. **Missing OAuth scopes**: Lagt til vehicle_location scope

**Mock Mode Design**:
- Sine wave oscillation: `sin(time/3600) * 20` ±20% rundt 70%
- Realistisk variasjon over tid
- Simulerer lading når batteri < 40%

### Fase 4: Beslutningslogikk ✅
**Periode**: Uke 5-6 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] DecisionEngine klasse
- [x] calculate_recommendation() - single vehicle
- [x] calculate_dual_recommendations() - two vehicles
- [x] compare_vehicles() - prioriteringslogikk
- [x] Priority score beregning
- [x] Konfigurerbar terskel

**Algoritme**:
1. Beregn urgency score: `max(0, threshold - battery_percent)`
2. Hvis under terskel → CHARGE
3. Hvis over terskel → NO_CHARGE
4. Hvis allerede lader → CONTINUE_CHARGING
5. Sammenligning: Høyeste urgency score først
6. Tiebreaker: Laveste batteriprosent

**Bug Fixes**:
- Issue #1: CONTINUE_CHARGING ikke behandlet som charging need
  - Løsning: `needs_charging()` helper function

### Fase 5: Background Scheduler ✅
**Periode**: Uke 6-7 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] ChargingScheduler klasse
- [x] APScheduler integration
- [x] Periodic update job (hourly)
- [x] Startup update job
- [x] Daily cleanup job (03:00)
- [x] Manual update trigger
- [x] Error handling (don't stop scheduler)
- [x] WebSocket broadcast integration

**Jobber**:
1. **update_vehicles**: Hver 60. minutt (konfigurerbar)
2. **startup_update**: Umiddelbart ved oppstart
3. **daily_cleanup**: Kl 03:00, sletter data > 90 dager

**Feilhåndtering**:
- Exceptions logges, men stopper ikke scheduler
- Database error logging
- Graceful degradation

### Fase 6: FastAPI Backend ✅
**Periode**: Uke 7-8 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] api/app.py - FastAPI setup
- [x] Lifespan context manager
- [x] CORS middleware
- [x] Static file serving
- [x] Jinja2 templates
- [x] REST endpoints (dashboard.py)
- [x] WebSocket endpoint (websocket.py)
- [x] Health check endpoint
- [x] Settings API (threshold, mock mode)

**Endpoints Implementert**:
- `GET /` - Dashboard HTML
- `GET /api/status` - Current status
- `POST /api/update` - Manual update
- `GET /api/history` - Historical data
- `GET /api/settings` - Get settings
- `PUT /api/settings/threshold` - Update threshold
- `PUT /api/settings/mock-mode/{vehicle}` - Toggle mock mode
- `WS /ws` - WebSocket connection
- `GET /health` - Health check

**WebSocket Implementation**:
- ConnectionManager pattern
- Broadcast to all active connections
- Ping/pong keep-alive
- Graceful disconnect handling

### Fase 7: Web Dashboard ✅
**Periode**: Uke 8-9 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] dashboard.html - Responsiv layout
- [x] dashboard.js - UI logic
- [x] websocket.js - WebSocket client
- [x] styles.css - Custom CSS
- [x] Tailwind CSS integration (CDN)
- [x] Vehicle cards (Tesla + Ioniq)
- [x] Priority recommendation banner
- [x] Settings panel (collapsible)
- [x] Manual update button
- [x] History button
- [x] WebSocket status indicator

**UI Komponenter**:
1. **Tesla Card**: Grønn/blå fargeskjema
2. **Ioniq Card**: Lilla/indigo fargeskjema
3. **Battery Gauge**: Fargekodet (grønn/gul/oransje/rød)
4. **Toggle Switches**: iOS-stil animerte switches
5. **Threshold Slider**: 50-100% med 5% steg

**Responsivt Design**:
- Mobile-first approach
- Grid layout (1 kolonne mobil, 2 kolonner desktop)
- Tailwind breakpoints (sm, md, lg, xl)

### Fase 8: Ioniq 5 Mock Support ✅
**Periode**: Uke 10 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] IoniqService klasse
- [x] Mock mode med cosine wave
- [x] Uavhengig mock data fra Tesla
- [x] Dual vehicle UI
- [x] Separate mock mode toggles
- [x] Dual recommendations i decision engine

**Mock Mode Design (Ioniq)**:
- Cosine wave: `cos(time/3600 * 1.2) * 25` ±25% rundt 65%
- Ulik frekvens fra Tesla for testing
- Simulerer lading når batteri < 35%

**UI Endringer**:
- To vehicle cards side-by-side
- Separate mock badges
- Separate recommendations
- Priority vehicle banner

### Fase 9: GPS Lokalisering ✅
**Periode**: Uke 11 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] utils/geocoding.py - Reverse geocoding
- [x] Nominatim API integration
- [x] GPS koordinater fra Tesla API
- [x] Adresse visning i UI
- [x] Error handling (ingen GPS, geocoding feil)

**Implementering**:
- Henter `latitude`/`longitude` fra `drive_state`
- Reverse geocoder med Nominatim (OpenStreetMap)
- Norsk språk for adresser
- Fallback til koordinater hvis geocoding feiler

**OAuth Scope Issue**:
- Problem: 403 "missing scopes vehicle_location"
- Løsning: Lagt til `vehicle_location` scope i OAuth flow
- Krever re-authentication for eksisterende brukere

### Fase 10: Testing og Dokumentasjon ✅
**Periode**: Uke 12 (Desember 2024)
**Status**: Fullført

**Leveranser**:
- [x] README.md - Komplett brukerdokumentasjon
- [x] CLAUDE.md - AI development guide
- [x] product_spec.md - Produktspesifikasjon
- [x] project_plan.md - Dette dokumentet
- [x] change_log.md - Versjonhistorikk
- [x] architecture.md - Systemarkitektur
- [x] Manuell testing av alle features
- [x] Edge case testing
- [x] Mock mode testing
- [x] Tesla API testing (hvis tilgjengelig)

**Testing Gjennomført**:
- ✅ Mock mode fungerer med realistiske data
- ✅ Dashboard laster korrekt
- ✅ WebSocket oppdaterer real-time
- ✅ Manuell oppdatering fungerer
- ✅ Scheduler kjører automatisk
- ✅ Database logger korrekt
- ✅ Error handling fungerer
- ✅ Responsiv design på mobil
- ✅ GPS lokalisering (med scope fix)

## 3. Ressurser

### 3.1 Team
- **Utvikler**: Sigurd Instanes
- **AI Assistant**: Claude Code (Anthropic)

### 3.2 Teknologi Stack
- **Backend**: Python 3.9+, FastAPI, uvicorn
- **Database**: SQLite med SQLAlchemy async
- **Scheduler**: APScheduler
- **Frontend**: HTML5, JavaScript (ES6+), Tailwind CSS
- **APIs**: Tesla Fleet API, Nominatim (OpenStreetMap)
- **Deployment**: macOS (dev), Raspberry Pi (planned)

### 3.3 Verktøy
- **IDE**: VS Code
- **Version Control**: Git
- **Package Manager**: pip
- **Browser Testing**: Chrome, Safari
- **API Testing**: FastAPI /docs (Swagger UI)

## 4. Risikoanalyse

### 4.1 Tekniske Risikoer

| Risiko | Sannsynlighet | Konsekvens | Mitigering | Status |
|--------|---------------|------------|------------|--------|
| Tesla API endringer | Middels | Høy | Bruk offisiell Fleet API, følg changelog | ✅ Implementert |
| Token refresh failures | Lav | Middels | Auto-retry, fallback til cached data | ✅ Implementert |
| WebSocket ustabilitet | Lav | Lav | Auto-reconnect, fallback til polling | ✅ Implementert |
| Database corruption | Meget lav | Høy | Regular backups, cleanup jobs | ✅ Implementert |
| OBD-II Bluetooth issues | Høy | Høy | Robust retry logic, mock mode fallback | ⏳ Planlagt v2.0 |

### 4.2 Scope Creep Risikoer

**Identifisert**:
- ✅ Funksjonskryp unngått ved klar MVP-definisjon
- ✅ v2.0/v3.0 features dokumentert, men ikke implementert
- ✅ Focus på Tesla MVP først

**Tiltak**:
- Tydelig product spec med "in scope" / "out of scope"
- Versjonering av features (v1.0, v2.0, v3.0)
- Prioritering av må-ha vs nice-to-have

### 4.3 Tidsplan Risikoer

**Faktiske forsinkelser**:
- OAuth scope issue: +2 dager (GPS location)
- Priority bug fix: +1 dag
- Mock mode toggle persistence: +0.5 dag

**Total forsinkelse**: ~3 dager fra estimat
**Opprinnelig estimat**: 10-12 dager
**Faktisk tid**: 13 dager (innenfor akseptabelt avvik)

## 5. Neste Steg (v2.0)

### 5.1 Planlagte Features (Q2 2025)

#### 5.1.1 Ioniq 5 OBD-II Integrasjon
**Estimat**: 3-4 uker
**Avhengigheter**: OBD-II Bluetooth dongle

**Tasks**:
1. Research Hyundai Ioniq 5 PIDs
   - Batteriprosent PID
   - Rekkevidde PID
   - Ladestatus PID
2. Kjøp og test OBD-II dongle (Veepeak/OBDLink)
3. Implementer `python-obd` integration
4. Bluetooth pairing og connection management
5. Error handling (lost connection, no data)
6. Testing i ekte bil
7. Dokumentasjon

**Risikoer**:
- PIDs kan være proprietære/ukjente
- Bluetooth ustabilitet
- OBD-II ikke tilgjengelig når bil lader

#### 5.1.2 Raspberry Pi Deployment
**Estimat**: 1-2 uker
**Avhengigheter**: Raspberry Pi 4, SD-kort

**Tasks**:
1. Setup Raspberry Pi OS
2. Installer Python dependencies
3. Konfigurer systemd service
4. Setup static IP / mDNS
5. Bluetooth setup for OBD-II
6. Auto-start ved boot
7. Monitoring og logging
8. Deployment guide i README

#### 5.1.3 Smart Switch Integrasjon
**Estimat**: 2-3 uker
**Avhengigheter**: Smart switch (Shelly, Sonoff)

**Tasks**:
1. Research smart switch APIer
2. Velg og kjøp switch
3. Implementer switch control service
4. Sikkerhetshåndtering (ikke bytt mens lading)
5. Manual override funksjonalitet
6. UI for switch status og kontroll
7. Testing av switching logic

#### 5.1.4 Geofencing
**Estimat**: 1 uke

**Tasks**:
1. Definer home koordinater i .env
2. Implementer haversine distance calculation
3. Auto-detect "home" vs "away"
4. UI indikator for location
5. Conditional logic basert på location

### 5.2 v3.0 Features (Q4 2025)

#### 5.2.1 Strømpris Integrasjon
**Estimat**: 2 uker
**API**: Tibber eller Nordpool

**Tasks**:
1. API integration
2. Pris-basert ladeanbefaling
3. Optimalisering for billigste timer
4. UI visning av strømpriser
5. Kostnadsbesparelser tracking

#### 5.2.2 Kalender Integrasjon
**Estimat**: 2 uker
**API**: Google Calendar

**Tasks**:
1. OAuth for Google Calendar
2. Detekter planlagte turer
3. Lad til høyere % før lange turer
4. UI visning av kommende events

#### 5.2.3 Push Notifications
**Estimat**: 1 uke
**Service**: Pushover eller Telegram

**Tasks**:
1. Implementer notification service
2. Konfigurerbare varslinger
3. Kritiske varsler (lav batteri, ladefeil)

#### 5.2.4 Historikk Grafer
**Estimat**: 2 uker
**Library**: Chart.js

**Tasks**:
1. Implementer Chart.js
2. Batterinivå over tid
3. Ladekostnader over tid
4. Sammenligning Tesla vs Ioniq

## 6. Lærdom og Refleksjoner

### 6.1 Hva fungerte bra ✅

**Teknologivalg**:
- FastAPI var perfekt valg (async, WebSocket, /docs)
- SQLite tilstrekkelig for use case
- Vanilla JS + Tailwind = rask utvikling uten build complexity
- Pydantic Settings = type-safe config

**Arkitektur**:
- Service abstraction (BaseVehicleService) tillot enkel mock mode
- Clear separation of concerns (services, core, api, web)
- WebSocket broadcast pattern fungerer utmerket
- Scheduler design robust mot feil

**Development Process**:
- Inkrementell utvikling (fase for fase)
- Mock mode først = testing uten hardware
- Git commits ved hver milepæl
- AI pair programming (Claude Code) økte produktivitet

### 6.2 Utfordringer møtt 🔧

**OAuth Scopes**:
- Lærte: Scopes må være korrekt fra start
- Løsning: Dokumentert scope update prosess

**State Management**:
- Problem: Mock mode toggle ikke persistent
- Lærte: Must update config, service, AND .env
- Løsning: Three-tier update pattern

**WebSocket Import**:
- Problem: WebSocketState moved in FastAPI 0.108.0
- Lærte: Check starlette exports, not just FastAPI
- Løsning: Import from starlette.websockets

**Priority Logic**:
- Problem: CONTINUE_CHARGING ikke behandlet korrekt
- Lærte: Need explicit "needs charging" check
- Løsning: Helper function

### 6.3 Forbedringspotensial 🚀

**Testing**:
- Skulle hatt unit tests (pytest)
- Integration tests for API endpoints
- Selenium tests for UI

**Sikkerhet**:
- Dashboard autentisering
- HTTPS support
- Rate limiting på API

**Ytelse**:
- PostgreSQL for produksjon (vs SQLite)
- Redis caching
- Database connection pooling

**Overvåking**:
- Prometheus metrics
- Grafana dashboards
- Alert system

## 7. Vedlikehold

### 7.1 Regelmessige Oppgaver

**Daglig** (automatisk):
- Database cleanup (03:00)
- Log rotation (10MB limit)

**Ukentlig**:
- Manuell testing av Tesla API
- Sjekk for nye Tesla Fleet API changes
- Review error logs

**Månedlig**:
- Dependency updates (`pip list --outdated`)
- Security audit
- Backup av database

**Kvartalsvis**:
- Feature review (nye behov?)
- Performance optimization
- Documentation updates

### 7.2 Oppgraderingsprosedyre

**Minor Updates** (1.0 → 1.1):
1. Pull latest code
2. `pip install -r requirements.txt --upgrade`
3. Restart service
4. Verify /health endpoint

**Major Updates** (1.0 → 2.0):
1. Backup database
2. Review CHANGELOG.md
3. Update .env with new variables
4. Run migration script (if needed)
5. Update systemd service (if changed)
6. Restart
7. Verify all features

## 8. Kontaktinformasjon

### 8.1 Support
- **GitHub Issues**: (hvis public repo)
- **Email**: (hvis relevant)
- **Dokumentasjon**: README.md, CLAUDE.md

### 8.2 Eksterne Ressurser
- **Tesla Fleet API**: https://developer.tesla.com/docs/fleet-api
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **APScheduler**: https://apscheduler.readthedocs.io/

## 9. Budsjett

### 9.1 Kostnader (Estimert)

**Utviklingskostnader**:
- Tid: ~80 timer @ hobbyprosjekt = $0
- AI Assistant (Claude): ~$20 (API usage)

**Hardware**:
- OBD-II Bluetooth Dongle: ~$30-50 (v2.0)
- Raspberry Pi 4: ~$70 (v2.0)
- SD-kort: ~$15 (v2.0)
- Smart Switch: ~$25-40 (v2.0)

**Running Costs**:
- Strøm (Raspberry Pi): ~$2/måned
- Tesla API: Gratis
- Nominatim API: Gratis (open source)

**Total estimert kostnad**:
- v1.0: ~$20
- v2.0: ~$200-250

### 9.2 ROI (Return on Investment)

**Tidsbesparelse**:
- 5 min/dag manuell sjekk → ~30 timer/år
- Verdi av fritid: Priceless 😊

**Strømbesparelse** (v3.0 med prisoptimalisering):
- Estimert: 10-20% reduksjon i ladekostnad
- ~200 kWh/måned → ~$10-20/måned besparelse

## 10. Vedlegg

### 10.1 Kanban Board Status

**Backlog**:
- [ ] Unit tests (pytest)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker containerization
- [ ] Multi-language support (English)

**In Progress**:
- [x] GPS location (DONE)
- [x] Dual vehicle support (DONE)

**Done**:
- [x] Tesla API integration
- [x] Web dashboard
- [x] WebSocket real-time
- [x] Mock mode
- [x] Decision engine
- [x] Database
- [x] Scheduler

### 10.2 Git Workflow

**Branches**:
- `main` - Production-ready code
- `develop` - Integration branch (hvis team)
- `feature/*` - Feature branches (hvis complex features)

**Commit Convention**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance

**Eksempel**:
```
feat: add GPS location display for Tesla
fix: priority bug when both vehicles charging
docs: update README with OAuth setup
```

### 10.3 Version Numbering

**Semantic Versioning**: MAJOR.MINOR.PATCH

- **MAJOR** (1.0, 2.0): Breaking changes
- **MINOR** (1.1, 1.2): New features (backwards compatible)
- **PATCH** (1.0.1, 1.0.2): Bug fixes

**Nåværende versjon**: 1.0.0 (MVP)

---

**Prosjektstatus**: ✅ MVP Fullført
**Neste milepæl**: v2.0 - Ioniq 5 OBD-II (Q2 2025)
**Oppdatert**: 2025-12-28
