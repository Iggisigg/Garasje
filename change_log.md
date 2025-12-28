# Endringslogg - Ladeprioriteringssystem

Alle vesentlige endringer i dette prosjektet dokumenteres her.

Formatet er basert på [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
og dette prosjektet følger [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planlagt for v2.0 (Q2 2025)
- Hyundai Ioniq 5 OBD-II Bluetooth integrasjon
- Raspberry Pi deployment guide
- Smart switch integrasjon
- Geofencing for hjemmelokasjon
- Improved error notifications

### Planlagt for v3.0 (Q4 2025)
- Strømpris API integrasjon (Tibber/Nordpool)
- Kalender integrasjon for planlagte turer
- Push notifications (Pushover/Telegram)
- Historikk-grafer med Chart.js
- Kostnadstracking

## [1.0.0] - 2024-12-28

### Lagt til
- **Tesla Model Y Integrasjon**
  - Tesla Fleet API support med OAuth 2.0 + PKCE autentisering
  - Automatisk token refresh mekanisme
  - Region-spesifikk endpoint support (EU/NA)
  - Caching av vehicle data (5 min) for redusert API bruk
  - Graceful handling av sovende kjøretøy (408 response)
  - GPS lokalisering med reverse geocoding via Nominatim
  - Adresse-visning i norsk format

- **Hyundai Ioniq 5 Mock Support**
  - Mock mode med simulerte data
  - Uavhengig datavariajon fra Tesla (cosine vs sine wave)
  - Samme datastruktur som Tesla for konsistent UI
  - Separat mock mode toggle

- **Web Dashboard**
  - Responsivt design (mobil + desktop)
  - To kjøretøykort side-by-side layout
  - Batterinivå med visuell gauge og fargekoding
  - Rekkevidde i kilometer
  - GPS-posisjon som adresse
  - Ladestatus med effekt (kW)
  - Anbefaling per bil (LAD / IKKE LAD / FORTSETT)
  - Prioritetsbanner (hvilken bil først)
  - Settings panel (sammenleggbar)
  - Threshold slider (50-100%)
  - Mock mode toggle switches (iOS-stil)
  - "Oppdater nå" knapp
  - "Vis historikk" knapp
  - WebSocket tilkoblingsindikator

- **Beslutningslogikk**
  - Konfigurerbar ladetterskel (standard: 80%)
  - Enkeltbil-anbefaling: CHARGE / NO_CHARGE / CONTINUE_CHARGING
  - Dual-vehicle prioritering med urgency score
  - Tiebreaker ved lik score (laveste batteriprosent)
  - Korrekt håndtering av CONTINUE_CHARGING tilstand

- **Sanntidsoppdateringer**
  - WebSocket tilkobling for live data
  - Automatisk broadcasting ved nye data
  - Ping/pong keep-alive
  - Auto-reconnect ved mistet tilkobling (3s interval)
  - Status indikator (tilkoblet/frakoblet)

- **Background Scheduler**
  - APScheduler integrasjon
  - Hourly vehicle updates (konfigurerbar)
  - Startup update (umiddelbart)
  - Daily cleanup job (03:00)
  - Manual update trigger
  - Error handling uten scheduler-stopp
  - WebSocket broadcast integration

- **Database**
  - SQLite med SQLAlchemy async
  - battery_readings tabell - alle statusoppdateringer
  - recommendations tabell - beslutningshistorikk
  - errors tabell - strukturert feillogging
  - Automatisk cleanup (>90 dager)
  - Indexed timestamps for ytelse

- **API Endpoints**
  - `GET /` - Dashboard HTML
  - `GET /api/status` - Current vehicle status
  - `POST /api/update` - Manual update trigger
  - `GET /api/history?hours=24` - Historical data
  - `GET /api/settings` - Get settings
  - `PUT /api/settings/threshold` - Update charge threshold
  - `PUT /api/settings/mock-mode/{vehicle}` - Toggle mock mode
  - `WS /ws` - WebSocket connection
  - `GET /health` - Health check

- **Configuration Management**
  - Pydantic Settings for type-safe config
  - .env file support
  - Runtime config updates (threshold, mock mode)
  - Three-tier update: config object, service, .env file

- **Logging**
  - Structured logging med timestamps
  - Console output (INFO+)
  - File output med rotation (DEBUG+, 10MB limit)
  - Error logging til database
  - Traceback capture

- **Setup Scripts**
  - `scripts/setup_tesla_fleet.py` - OAuth flow
  - `scripts/register_tesla_account.py` - Partner registration
  - Auto .env creation fra .env.example

- **Dokumentasjon**
  - README.md - Komplett brukerdokumentasjon
  - CLAUDE.md - AI development guide
  - product_spec.md - Produktspesifikasjon
  - project_plan.md - Utviklingsplan
  - change_log.md - Dette dokumentet
  - architecture.md - Systemarkitektur
  - FastAPI auto-docs (/docs, /redoc)

### Endret
- **OAuth Scopes** - Lagt til `vehicle_location` for GPS-tilgang
- **Mock Mode** - Separert Tesla og Ioniq mock modes
- **UI Layout** - Dual vehicle grid i stedet for single card

### Fikset
- **Priority Bug** - CONTINUE_CHARGING ikke behandlet som charging need
  - Løsning: `needs_charging()` helper function
  - Dato: 2024-12-28

- **Mock Mode Toggle Persistence** - Toggles revertet ved oppdatering
  - Problem: Kun service oppdatert, ikke config eller .env
  - Løsning: Three-tier update (service + config + .env)
  - Dato: 2024-12-27

- **GPS Location Missing** - 403 Unauthorized error
  - Problem: OAuth token manglet `vehicle_location` scope
  - Løsning: Oppdatert setup scripts med korrekt scope
  - Dato: 2024-12-28

- **WebSocket Import Error** - Cannot import WebSocketState from fastapi
  - Problem: FastAPI 0.108.0 moved export til starlette
  - Løsning: Import fra `starlette.websockets`
  - Dato: 2024-12-26

- **Abstract Method Error** - IoniqService manglende authenticate()
  - Problem: BaseVehicleService krever abstract method
  - Løsning: Implementert no-op authenticate() for OBD-II
  - Dato: 2024-12-26

### Sikkerhet
- OAuth tokens ikke committet til git (.gitignore)
- CORS policy begrenset til localhost
- HTTPS for alle eksterne API-kall
- User-Agent header for Nominatim compliance

## [0.9.0] - 2024-12-20 (Beta)

### Lagt til
- Grunnleggende Tesla integrasjon (uten GPS)
- Enkel web dashboard (kun Tesla)
- Mock mode for testing
- Basic decision engine
- SQLite database setup

### Kjente Problemer
- Ingen dual vehicle support
- Ingen GPS lokalisering
- Ingen WebSocket (polling only)
- Hardkodet threshold

## [0.5.0] - 2024-12-10 (Alpha)

### Lagt til
- Prosjekt scaffold
- FastAPI setup
- Database models
- Tesla service skeleton

### Notater
- Proof of concept
- Ikke produksjonsklart

## Versjonering

### Major Releases
- **1.0** - MVP med Tesla support (2024-12-28)
- **2.0** - Ioniq 5 OBD-II + Raspberry Pi (planlagt Q2 2025)
- **3.0** - Strømpris + Kalender (planlagt Q4 2025)

### Version Number Format
`MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes eller store nye features
- **MINOR**: Nye features (backwards compatible)
- **PATCH**: Bug fixes

## Breaking Changes

### v1.0.0
**Ingen** - Første major release

### Fremtidige Breaking Changes (Varsel)

**v2.0.0** vil sannsynligvis inkludere:
- Database schema endringer (nye kolonner)
- Config format endringer (nye .env variabler)
- API endpoint endringer (nye felter i response)

**Migrering**: Migration script vil bli levert

## Deprecation Notices

**Ingen** - Første major release

## Kjente Issues

### v1.0.0

**Mindre issues**:
- [ ] History UI viser bare count, ikke detaljert graf
  - Workaround: Bruk /api/history endpoint direkte
  - Planlagt fix: v1.1.0

- [ ] Ingen notifikasjoner ved lav batteri
  - Workaround: Sjekk dashboard regelmessig
  - Planlagt fix: v3.0.0 (push notifications)

**Limitasjoner**:
- Tesla kan ta opptil 5 sek å svare (ekstern API)
- Nominatim rate limit: 1 req/s (sjelden problem)
- SQLite ikke egnet for multi-user (OK for single user)

## Database Migrations

### v1.0.0 → v1.0.1 (hvis relevant)
**Ingen migrations** - Første release

### Fremtidig (v2.0.0)
Potensielle schema endringer:
```sql
-- Eksempel (ikke implementert)
ALTER TABLE battery_readings ADD COLUMN temperature REAL;
ALTER TABLE battery_readings ADD COLUMN odometer_km REAL;
```

## Rollback Guide

### v1.0.0 → v0.9.0 (Beta)
**Ikke støttet** - Breaking schema changes

**Hvis nødvendig**:
1. Backup `.env` fil
2. Backup `data/` directory
3. Checkout tidligere git tag: `git checkout v0.9.0`
4. Reinstaller dependencies
5. Restore .env
6. Kjør database migration (hvis script finnes)

## Contributors

### v1.0.0
- **Sigurd Instanes** - Initial development
- **Claude Code** (Anthropic) - AI pair programming assistant

## Acknowledgments

Takk til følgende open source prosjekter:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Nominatim](https://nominatim.org/) / OpenStreetMap
- Tesla for Fleet API

## Support

### v1.0.0 Support Status
- **Active Support**: Ja
- **Bug Fixes**: Ja
- **New Features**: Via minor updates (1.1, 1.2, etc.)

### End of Life
**Ingen planlagt dato** - Aktivt utviklet hobby project

## Changelog Conventions

Format brukt i dette dokumentet:

- **Lagt til** - Nye features
- **Endret** - Endringer i eksisterende funksjonalitet
- **Deprecated** - Features som vil bli fjernet
- **Fjernet** - Features som er fjernet
- **Fikset** - Bug fixes
- **Sikkerhet** - Sikkerhetsforbedringer

## Release Notes URLs

- **v1.0.0**: https://github.com/[username]/[repo]/releases/tag/v1.0.0 (hvis publisert)

---

**Sist oppdatert**: 2024-12-28
**Neste planlagte release**: v2.0.0 (Q2 2025)
