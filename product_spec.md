# Produktspesifikasjon - Ladeprioriteringssystem

**Versjon**: 1.0
**Dato**: 2025-12-28
**Status**: MVP Ferdigstilt

## 1. Produktoversikt

### 1.1 Formål
Et automatisk system som overvåker batterinivået til elbiler og anbefaler hvilken bil som bør prioriteres for lading. Systemet skal redusere behovet for manuell sjekk av batterinivåer og sikre at den mest kritiske bilen alltid har nok strøm.

### 1.2 Målgruppe
- Husholdninger med flere elbiler og én lader
- Brukere som ønsker automatisert overvåking av ladestatus
- Teknisk interesserte som vil eksperimentere med EV API-integrasjoner

### 1.3 Brukerhistorier

**Som bilist** vil jeg:
- Se batterinivået på begge bilene mine fra ett sted
- Få anbefaling om hvilken bil jeg bør lade
- Se hvor bilene befinner seg geografisk
- Kunne justere når systemet anbefaler lading (terskel)

**Som utvikler** vil jeg:
- Kunne teste systemet uten tilgang til ekte biler (mock mode)
- Se historisk data om batterinivåer
- Få feilmeldinger når noe går galt

## 2. Funksjonelle Krav

### 2.1 Tesla Model Y Integrasjon (v1.0)

**Krav ID**: FR-001
**Prioritet**: Høy
**Status**: ✅ Implementert

**Funksjonalitet**:
- Hente batterinivå fra Tesla Fleet API
- Vise rekkevidde i kilometer
- Vise om bilen lader eller ikke
- Vise ladhastighet (kW) når bilen lader
- Vise GPS-posisjon som adresse (reverse geocoding)
- Automatisk token-refresh når OAuth token utløper

**Tekniske detaljer**:
- OAuth 2.0 med PKCE autentisering
- Region-spesifikke endepunkter (EU/NA)
- Caching av data i 5 minutter for å redusere API-kall
- Støtte for sovende kjøretøy (408 response)

### 2.2 Hyundai Ioniq 5 Integrasjon (v1.0 - Mock Only)

**Krav ID**: FR-002
**Prioritet**: Middels
**Status**: 🟡 Delvis implementert (kun mock mode)

**Funksjonalitet**:
- Mock mode med simulerte data
- Uavhengig batterisimulering fra Tesla
- Samme datastruktur som Tesla for konsistent UI

**Planlagt (v2.0)**:
- OBD-II Bluetooth tilkobling
- Hente batterinivå via Hyundai-spesifikke PIDs
- Auto-reconnect ved mistet Bluetooth-tilkobling

### 2.3 Beslutningslogikk

**Krav ID**: FR-003
**Prioritet**: Høy
**Status**: ✅ Implementert

**Regler**:
1. **Under terskel**: Anbefal lading
2. **Over terskel**: Anbefal ikke lading
3. **Lader allerede**: Fortsett lading til terskel nås
4. **To biler under terskel**: Prioriter laveste batteri

**Prioritetsberegning**:
- Basert på "urgency score": hvor langt under terskelen
- Tiebreaker: Laveste batteriprosent
- Spesialhåndtering av CONTINUE_CHARGING tilstand

**Konfigurerbar terskel**:
- Standard: 80%
- Kan justeres i UI fra 50% til 100% (5% steg)
- Lagres i .env fil for persistens

### 2.4 Web Dashboard

**Krav ID**: FR-004
**Prioritet**: Høy
**Status**: ✅ Implementert

**Komponenter**:

1. **Kjøretøykort** (per bil):
   - Batterinivå som prosent og visuell gauge
   - Rekkevidde i kilometer
   - GPS-posisjon som adresse
   - Ladestatus (lader/lader ikke + effekt)
   - Mock mode indikator
   - Anbefaling (LAD / IKKE LAD / FORTSETT)

2. **Prioritetsbanner**:
   - Viser hvilken bil som bør lades først
   - Grønn hvis ingen trenger lading
   - Blå hvis en eller begge trenger lading

3. **Kontroller**:
   - "Oppdater nå" knapp - trigger manuell oppdatering
   - "Vis historikk" knapp - se siste 24 timer

4. **Innstillinger** (sammenleggbar):
   - Slider for ladetterskel (50-100%)
   - Toggle switches for mock mode (per bil)
   - Visning av oppdateringsintervall
   - Visning av Tesla/Ioniq modus (Ekte/Mock)

**UX-krav**:
- Responsiv design (mobil + desktop)
- Sanntidsoppdateringer uten å refreshe siden
- Visuell indikator for WebSocket-tilkobling
- Fargekodet batterinivå (grønn > 80%, gul 50-80%, oransje 20-50%, rød < 20%)

### 2.5 Sanntidsoppdateringer

**Krav ID**: FR-005
**Prioritet**: Høy
**Status**: ✅ Implementert

**Funksjonalitet**:
- WebSocket-tilkobling mellom server og klient
- Automatisk broadcasting når ny data er tilgjengelig
- Ping/pong keep-alive meldinger
- Auto-reconnect ved mistet tilkobling (3s intervall)
- Visuell indikator for tilkoblingsstatus

**Meldingstyper**:
- `initial_status` - Første data ved tilkobling
- `status_update` - Nye data fra scheduler eller manuell oppdatering
- `ping/pong` - Keep-alive

### 2.6 Historikk og Logging

**Krav ID**: FR-006
**Prioritet**: Middels
**Status**: ✅ Implementert

**Database-logging**:
- Alle batterimålinger lagres i SQLite
- Alle anbefalinger logges med begrunnelse
- Alle feil lagres strukturert
- Automatisk cleanup etter 90 dager

**API-tilgang**:
- `GET /api/history?hours=24` - Hent historikk
- Filtrering på tidsperiode
- Inkludering av mock data flag

**Applikasjonslogger**:
- Console logging (INFO+)
- Fil logging (DEBUG+) med rotating files (10MB)
- Strukturert logging med timestamps og nivåer

### 2.7 Automatisk Planlegging

**Krav ID**: FR-007
**Prioritet**: Høy
**Status**: ✅ Implementert

**Scheduler-jobber**:

1. **Startup Update**:
   - Kjøres umiddelbart ved oppstart
   - Populerer dashboard med ferske data

2. **Periodic Update**:
   - Kjøres hver 60. minutt (konfigurerbar)
   - Henter data fra begge biler
   - Beregner anbefalinger
   - Broadcaster via WebSocket

3. **Daily Cleanup**:
   - Kjøres kl 03:00 hver natt
   - Sletter data eldre enn 90 dager
   - Holder database-størrelse håndterbar

**Feilhåndtering**:
- Exceptions stopper ikke scheduler
- Feil logges til database og app log
- Neste scheduled run fortsetter normalt

## 3. Ikke-funksjonelle Krav

### 3.1 Ytelse

**Krav ID**: NFR-001
**Status**: ✅ Oppfylt

- Dashboard skal laste på < 2 sekunder
- WebSocket latency < 100ms for lokalt nettverk
- API response time < 500ms for cached data
- Tesla API response time < 5 sekunder (ekstern avhengighet)

### 3.2 Pålitelighet

**Krav ID**: NFR-002
**Status**: ✅ Oppfylt

- Systemet skal håndtere Tesla API-nedtid gracefully
- Returnere cached data hvis API feiler
- Auto-retry på token refresh failures
- WebSocket auto-reconnect ved nettverksproblemer

### 3.3 Sikkerhet

**Krav ID**: NFR-003
**Status**: ✅ Oppfylt

**Implementert**:
- OAuth tokens lagres ikke i git (.env, tesla_cache.json i .gitignore)
- HTTPS brukes for alle eksterne API-kall
- CORS policy begrenset til localhost (i prod mode)
- Ingen autentisering på dashboard (kun lokalt nettverk)

**Planlagt (v2.0)**:
- Dashboard autentisering for ekstern tilgang
- HTTPS for dashboard (Let's Encrypt)

### 3.4 Vedlikeholdbarhet

**Krav ID**: NFR-004
**Status**: ✅ Oppfylt

- Tydelig separasjon av concerns (services, core, api, web)
- Alle services implementerer samme interface (BaseVehicleService)
- Type hints på alle funksjoner
- Strukturert logging for debugging
- Mock mode for testing uten hardware

### 3.5 Skalerbarhet

**Krav ID**: NFR-005
**Status**: 🟡 Delvis oppfylt

**Nåværende begrensninger**:
- Hardkodet for to biler
- SQLite database (ikke for high-traffic)
- Ingen load balancing

**Tilstrekkelig for målgruppe**:
- Single-user system
- < 100 requests per time
- Lokalt nettverk deployment

### 3.6 Portabilitet

**Krav ID**: NFR-006
**Status**: ✅ Oppfylt

**Testet på**:
- macOS (development)
- Python 3.9+

**Planlagt**:
- Raspberry Pi (Linux ARM)
- Windows (for testing)

## 4. Systemgrenser

### 4.1 I Scope (v1.0)
- ✅ Tesla Model Y batteriovervåking
- ✅ Ioniq 5 mock mode
- ✅ Web dashboard
- ✅ Automatisk oppdatering
- ✅ GPS-lokalisering (Tesla)
- ✅ Mock mode for begge biler

### 4.2 Out of Scope (v1.0, men planlagt v2.0+)
- ❌ Ioniq 5 OBD-II integrasjon
- ❌ Smart switch automatisk kontroll
- ❌ Strømpris integrasjon
- ❌ Push-notifikasjoner
- ❌ Kalender integrasjon
- ❌ Historikk-grafer i UI
- ❌ Mobile app

### 4.3 Aldri i Scope
- Direkte kontroll av Tesla lading (krever spesielle API-rettigheter)
- Cloud deployment (kun lokal/Raspberry Pi)
- Multi-bruker system

## 5. Brukergrensesnitt

### 5.1 Design-prinsipper
- **Enkelhet**: All kritisk info på én skjerm
- **Klarhet**: Tydelige anbefalinger uten tolkningsbehov
- **Responsivt**: Fungerer på mobil og desktop
- **Sanntid**: Oppdateringer uten manuell refresh

### 5.2 Fargepalette
- **Tesla**: Grønn (#10B981) / Blå (#3B82F6)
- **Ioniq**: Lilla (#A855F7) / Indigo (#6366F1)
- **Batterinivå**:
  - Grønn: ≥ 80%
  - Gul: 50-79%
  - Oransje: 20-49%
  - Rød: < 20%
- **Anbefaling**:
  - Grønn: "IKKE LAD" (over terskel)
  - Blå: "LAD" (under terskel)

### 5.3 Typografi
- **Framework**: Tailwind CSS
- **Font**: System font stack for ytelse
- **Størrelser**: Responsive (text-sm til text-3xl)

## 6. API Spesifikasjon

### 6.1 Eksterne APIer

**Tesla Fleet API**:
- **Base URL**: https://fleet-api.prd.eu.vn.cloud.tesla.com (EU)
- **Autentisering**: OAuth 2.0 med PKCE
- **Rate Limits**: Ukjent, men time-basert caching reduserer kall
- **Endpoints**:
  - `GET /api/1/vehicles` - List vehicles
  - `GET /api/1/vehicles/{id}/vehicle_data` - Get vehicle state

**Nominatim (OpenStreetMap)**:
- **Base URL**: https://nominatim.openstreetmap.org
- **Autentisering**: Ingen (User-Agent påkrevd)
- **Rate Limits**: 1 request per sekund
- **Endpoint**:
  - `GET /reverse?lat={lat}&lon={lon}` - Reverse geocoding

### 6.2 Interne APIer (REST)

Se CLAUDE.md "API Endpoints Reference" for fullstendig liste.

**Hovedendepunkter**:
- `GET /` - Dashboard
- `GET /api/status` - Current status
- `POST /api/update` - Manual update
- `GET /api/history` - Historical data
- `PUT /api/settings/threshold` - Update threshold
- `PUT /api/settings/mock-mode/{vehicle}` - Toggle mock mode

## 7. Dataobjekter

### 7.1 VehicleStatus
```python
@dataclass
class VehicleStatus:
    vehicle_name: str           # "Tesla Model Y", "Hyundai Ioniq 5"
    battery_percent: float      # 0.0 - 100.0
    range_km: float            # Rekkevidde i kilometer
    is_charging: bool          # True hvis lader nå
    location: str              # "home", "away"
    last_updated: datetime     # Timestamp
    is_mock: bool              # True hvis mock data
    charging_rate_kw: float    # kW hvis lader, None ellers
    latitude: float            # GPS breddegrad
    longitude: float           # GPS lengdegrad
    address: str               # Reverse geocoded adresse
```

### 7.2 Recommendation
```python
@dataclass
class Recommendation:
    action: ChargeAction       # CHARGE, NO_CHARGE, CONTINUE_CHARGING
    reason: str                # Forklaring på norsk
    timestamp: datetime        # Når anbefaling ble gitt
    battery_percent: float     # Batterinivå ved anbefaling
    threshold: float           # Terskelverdien som ble brukt
    priority_score: float      # Urgency-score for sammenligning
```

## 8. Feilhåndtering

### 8.1 Feilkategorier

**Tesla API Feil**:
- 401 Unauthorized → Trigger re-authentication
- 403 Forbidden (missing scope) → Log error, instruér bruker
- 408 Request Timeout (vehicle asleep) → Returner cached data
- 429 Rate Limit → Exponential backoff
- 5xx Server Error → Retry 3 ganger, deretter cached data

**Database Feil**:
- Connection error → Log til console, fortsett uten persistens
- Write error → Log, men ikke stopp application

**WebSocket Feil**:
- Client disconnect → Fjern fra active connections
- Broadcast error → Log, fortsett for andre clients

### 8.2 Feilmeldinger til Bruker

**UI Feilmeldinger** (Norwegian):
- "Kunne ikke laste data. Prøv å oppdatere siden."
- "Oppdatering mislyktes. Prøv igjen."
- "Kunne ikke hente historikk."
- "Kunne ikke oppdatere innstillinger."

**Server Feilmeldinger** (Logs):
- Strukturert logging med traceback
- Error severity levels (WARNING, ERROR, CRITICAL)
- Lagres til database for analyse

## 9. Testing

### 9.1 Mock Mode Testing
- **Tesla Mock**: Sine wave oscillation ±20% rundt 70%
- **Ioniq Mock**: Cosine wave oscillation ±25% rundt 65%
- Uavhengige mønstre for å teste dual-vehicle logic

### 9.2 Manuel Testing Checklist
- [ ] Dashboard laster korrekt
- [ ] WebSocket tilkobler og viser status
- [ ] Mock mode viser realistiske data
- [ ] Manuell oppdatering fungerer
- [ ] Threshold-slider oppdaterer anbefaling
- [ ] Mock mode toggles persisterer
- [ ] Historikk viser korrekt data
- [ ] Responsivt design fungerer på mobil
- [ ] Tesla OAuth flow fungerer (hvis tilgjengelig)
- [ ] GPS-lokasjon vises korrekt

### 9.3 Edge Cases
- Begge biler på nøyaktig samme batterinivå
- Tesla sovende (408 response)
- Mistet WebSocket-tilkobling
- Token refresh under oppdatering
- Database cleanup under aktiv bruk

## 10. Deployment

### 10.1 Development (v1.0)
- **Platform**: macOS
- **Python**: 3.9+
- **Dependencies**: pip install -r requirements.txt
- **Config**: .env file
- **Access**: http://localhost:8000

### 10.2 Production (Planlagt v2.0)
- **Platform**: Raspberry Pi 4
- **OS**: Raspberry Pi OS
- **Service**: systemd
- **Networking**: Static IP eller mDNS
- **Access**: http://charging-manager.local:8000

## 11. Dokumentasjon

### 11.1 Bruker-dokumentasjon
- README.md - Installasjon og bruk
- .env.example - Konfigurasjon
- Inline help i UI (tooltips)

### 11.2 Utvikler-dokumentasjon
- CLAUDE.md - AI development guide
- architecture.md - System architecture
- product_spec.md - Dette dokumentet
- project_plan.md - Utviklingsplan
- change_log.md - Versjonhistorikk

### 11.3 API-dokumentasjon
- FastAPI automatisk docs: /docs (Swagger UI)
- /redoc (ReDoc)

## 12. Fremtidige Funksjoner

### Versjon 2.0 (Q2 2025)
- OBD-II Bluetooth integrasjon for Ioniq 5
- Raspberry Pi deployment guide
- Smart switch integrasjon
- Geofencing for home detection

### Versjon 3.0 (Q4 2025)
- Strømpris API integrasjon (Tibber/Nordpool)
- Kalender integrasjon for turer
- Push notifications
- Historikk-grafer i dashboard

### Versjon 4.0 (2026)
- Mobile app (React Native)
- Flere bilmerker (Volkswagen ID, Polestar, etc.)
- Cloud sync (optional)
- Værdata integrasjon

## 13. Suksesskriterier

### MVP (v1.0) - ✅ Oppnådd
- [x] Viser Tesla batterinivå automatisk
- [x] Gir korrekt anbefaling basert på terskel
- [x] Dashboard fungerer på mobil og desktop
- [x] WebSocket sanntidsoppdateringer
- [x] Mock mode for testing uten bil
- [x] GPS-lokasjon for Tesla
- [x] Dual-vehicle support (Tesla + Ioniq mock)

### v2.0 - Planlagt
- [ ] Ioniq 5 ekte data via OBD-II
- [ ] Kjører på Raspberry Pi
- [ ] 99% uptime over 30 dager

### v3.0 - Planlagt
- [ ] Strømpris-optimalisering
- [ ] < 1kr per måned i strømbesparelse

## 14. Vedlegg

### 14.1 Ordliste
- **OAuth**: Open Authorization - sikker autentiseringsprotokoll
- **PKCE**: Proof Key for Code Exchange - OAuth sikkerhetsforbedring
- **WebSocket**: Toveis sanntidskommunikasjon mellom klient og server
- **Reverse Geocoding**: Konvertering av GPS-koordinater til adresser
- **Mock Mode**: Simuleringsmodus for testing uten ekte data

### 14.2 Referanser
- Tesla Fleet API: https://developer.tesla.com/docs/fleet-api
- FastAPI: https://fastapi.tiangolo.com/
- Tailwind CSS: https://tailwindcss.com/
- Nominatim: https://nominatim.org/

### 14.3 Lisens
Personlig hobbyprosjekt - ingen formell lisens.
