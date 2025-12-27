# Ladeprioriteringssystem

Automatisk ladeprioriteringssystem for elbiler. Versjon 1.0 (MVP) støtter **Tesla Model Y** med mulighet for senere utvidelse til Hyundai Ioniq 5 via OBD-II.

## 📋 Oversikt

Dette systemet:
- ✅ Henter batteristatus fra Tesla Model Y automatisk hver time
- ✅ Anbefaler når bilen bør lades basert på konfigurerbar terskel
- ✅ Viser sanntidsdata via et responsivt web-dashboard
- ✅ Logger historikk i SQLite database
- ✅ Støtter både ekte Tesla API og mock mode for testing

## 🎯 Funksjonalitet

### Nåværende (v1.0 - Tesla MVP)
- Tesla API integrasjon med OAuth autentisering
- Automatisk henting av batteristatus hver time (konfigurerbar)
- Real-time oppdateringer via WebSocket
- Beslutningslogikk: lad hvis batteri < terskel (standard 80%)
- Web dashboard tilgjengelig på lokalt nettverk
- Mobile-vennlig responsivt design
- Database for historikk og logging
- Mock mode for testing uten bil

### Fremtidig (v2.0)
- Hyundai Ioniq 5 integrasjon via OBD-II Bluetooth
- Sammenligning av to biler for prioritering
- Smart strømbryter integrasjon for automatisk bytte
- Strømpris integrasjon
- Kalender integrasjon for planlagte turer
- Push-varsler

## 🚀 Kom i gang

### Forutsetninger

- Python 3.9 eller nyere
- Git (for kloning av repository)
- Tesla account (for ekte data, valgfritt)

### Installasjon

1. **Klon repository**
```bash
git clone <repository-url>
cd "Garasje lading"
```

2. **Opprett virtuelt miljø (anbefalt)**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# eller
venv\Scripts\activate  # Windows
```

3. **Installer avhengigheter**
```bash
pip install -r requirements.txt
```

4. **Konfigurer miljøvariabler**
```bash
# .env filen opprettes automatisk fra .env.example ved første kjøring
# Rediger .env etter behov
cp .env.example .env
```

### Konfigurasjon

Rediger `.env` filen:

```env
# Tesla Fleet API Configuration
TESLA_CLIENT_ID=din_client_id
TESLA_CLIENT_SECRET=din_client_secret

# Application Configuration
MOCK_MODE=true  # Sett til 'false' for ekte Tesla data
UPDATE_INTERVAL_MINUTES=60  # Hvor ofte data oppdateres
CHARGE_THRESHOLD_PERCENT=80  # Lad ikke hvis over denne %
LOG_LEVEL=INFO

# Web Server
HOST=0.0.0.0  # Tillat tilgang fra lokalt nettverk
PORT=8000
```

## 🔧 Bruk

### Alternativ 1: Mock Mode (Testing uten bil)

Dette er den enkleste måten å teste systemet:

```bash
# Sørg for at MOCK_MODE=true i .env
python main.py
```

Åpne browser på: `http://localhost:8000`

Du vil se simulerte Tesla-data som endrer seg over tid.

### Alternativ 2: Ekte Tesla Data

#### Forutsetninger:
- Tesla konto
- Registrert Tesla Developer app på https://developer.tesla.com

#### Setup (kun første gang):

1. **Registrer Tesla Developer App**:
   - Gå til https://developer.tesla.com
   - Opprett en ny app
   - Sett Redirect URI til: `http://localhost:8000/callback`
   - Kopier Client ID og Client Secret

2. **Konfigurer .env**:
```bash
TESLA_CLIENT_ID=<din_client_id>
TESLA_CLIENT_SECRET=<din_client_secret>
MOCK_MODE=false
```

3. **Kjør OAuth setup**:
```bash
python scripts/setup_tesla_fleet.py
```

Dette vil:
- Åpne browser for Tesla-innlogging
- Be om autorisasjon
- Lagre OAuth token til `data/tesla_cache.json`

4. **Start applikasjonen**:
```bash
python main.py
```

5. **Åpne dashboard**:
```
http://localhost:8000
```

## 📱 Dashboard

### Funksjoner

- **Tesla Status Card**: Viser batteri%, rekkevidde, ladestatus, lokasjon
- **Anbefaling**: Klar beskjed om bilen bør lades eller ikke
- **Oppdater nå**: Manuell oppdatering av data
- **Vis historikk**: Se tidligere batterimålinger (siste 24 timer)
- **Innstillinger**: Juster ladeterskelen dynamisk

### Real-time Oppdateringer

Dashboardet bruker WebSocket for sanntidsoppdateringer:
- ✅ Grønn indikator = tilkoblet
- ❌ Rød indikator = frakoblet
- Data oppdateres automatisk hver time (eller når du trykker "Oppdater nå")

## 🏗️ Prosjektstruktur

```
charging-manager/
├── main.py                 # Hovedprogram (start her)
├── config.py              # Konfigurasjon
├── requirements.txt       # Python-avhengigheter
├── .env                   # Miljøvariabler (opprettes automatisk)
│
├── services/              # Data-tjenester
│   ├── base_service.py    # Abstract base class
│   └── tesla_service.py   # Tesla API integrasjon
│
├── models/                # Datamodeller
│   ├── vehicle.py         # VehicleStatus
│   └── recommendation.py  # Recommendation
│
├── core/                  # Kjerne forretningslogikk
│   ├── database.py        # SQLite database
│   ├── decision_engine.py # Ladelogikk
│   └── scheduler.py       # Automatisk oppdatering
│
├── api/                   # Web API (FastAPI)
│   ├── app.py            # FastAPI app
│   └── routes/
│       ├── dashboard.py   # REST endpoints
│       └── websocket.py   # WebSocket
│
├── web/                   # Frontend
│   ├── templates/
│   │   └── dashboard.html
│   └── static/
│       ├── css/styles.css
│       └── js/
│           ├── dashboard.js
│           └── websocket.js
│
├── utils/                 # Verktøy
│   ├── logger.py         # Logging
│   └── exceptions.py     # Custom exceptions
│
├── scripts/                    # Hjelpeskript
│   ├── setup_tesla_fleet.py   # Tesla Fleet API OAuth setup
│   ├── register_tesla_account.py  # Partner registrering
│   └── generate_keys.py       # Generer krypteringsnøkler
│
└── data/                       # Runtime data (opprettes automatisk)
    ├── charging_manager.db     # SQLite database
    ├── tesla_cache.json        # OAuth tokens
    ├── website/                # Public key hosting (for GitHub Pages/Vercel)
    │   ├── index.html
    │   └── .well-known/appspecific/
    │       └── com.tesla.3p.public-key.pem
    └── logs/
        └── app.log
```

## 🔌 API Endpoints

### REST API

- `GET /` - Dashboard HTML
- `GET /api/status` - Hent nåværende status
- `POST /api/update` - Trigger manuell oppdatering
- `GET /api/history?hours=24` - Hent historikk
- `GET /api/settings` - Hent innstillinger
- `PUT /api/settings/threshold?threshold=85` - Oppdater terskel
- `GET /api/scheduler` - Scheduler status
- `GET /health` - Health check

### WebSocket

- `WS /ws` - Real-time oppdateringer

**Meldingertyper**:
- `initial_status` - Første status ved tilkobling
- `status_update` - Nye data tilgjengelig
- `ping/pong` - Keep-alive

## 📊 Database

SQLite database (`data/charging_manager.db`) inneholder:

### Tabeller

1. **battery_readings**
   - timestamp, vehicle, battery_percent, range_km, location, is_charging, is_mock

2. **recommendations**
   - timestamp, vehicle, action, reason, battery_percent, threshold

3. **errors**
   - timestamp, service, error_type, message

### Cleanup

Gamle data (>90 dager) slettes automatisk hver natt kl 03:00.

## 🐛 Feilsøking

### "Tesla authentication failed"
- Sørg for at du har kjørt `python scripts/setup_tesla_fleet.py`
- Sjekk at `TESLA_CLIENT_ID` og `TESLA_CLIENT_SECRET` er korrekt i `.env`
- Token kan ha utløpt - kjør setup på nytt

### "Account must be registered in the current region"
- Tesla Fleet API krever partner registrering
- Dette krever et offentlig domene for å hoste en public key
- Se seksjonen om Tesla Fleet API setup i README

### "WebSocket frakoblet"
- Sjekk nettverkstilkobling
- Browser kan ha blokkert WebSocket - se console log
- Restart applikasjonen

### "No module named 'fastapi'"
- Installer avhengigheter: `pip install -r requirements.txt`
- Aktiver virtual environment hvis du bruker det

### Dashboard viser ikke data
- Sjekk at serveren kjører på riktig port
- Åpne Developer Console (F12) for å se JavaScript-feil
- Sjekk loggfil: `data/logs/app.log`

## 📝 Logging

Logger skrives til:
- **Console**: INFO-nivå og høyere (for kjøring)
- **Fil**: `data/logs/app.log` (alle nivåer, roteres ved 10MB)

Endre lognivå i `.env`:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🚧 Utvidelse til v2.0 (Ioniq 5)

Når du vil legge til Hyundai Ioniq 5:

1. **Kjøp OBD-II Bluetooth dongle**
   - Anbefaling: Veepeak eller OBDLink

2. **Implementer Ioniq service**
   - Opprett `services/ioniq_service.py`
   - Bruk `python-obd` bibliotek
   - Finn Ioniq 5-spesifikke PIDs for batterinivå

3. **Oppdater decision engine**
   - Sammenlign begge biler
   - Prioriter laveste batteri

4. **Oppdater dashboard**
   - To kort (Tesla + Ioniq)
   - Anbefaling indikerer hvilken bil

5. **Deploy til Raspberry Pi**
   - Se planfil for deployment-instruksjoner

## 🔐 Sikkerhet

- `.env` filen inneholder sensitiv informasjon (Tesla token) - ALDRI commit til git
- `tesla_cache.json` lagrer OAuth token - beskytt denne filen
- Kjør systemet kun på pålitelig nettverk
- Standard konfigurasjon tillater tilgang fra lokalt nettverk (`HOST=0.0.0.0`)
- For produksjonsbruk, vurder å legge til autentisering på web-dashboardet

## 📄 Lisens

Dette er et personlig hobbyprosjekt.

## 🙏 Takk til

- [TeslaPy](https://github.com/tdorssers/TeslaPy) - Utmerket Tesla API bibliotek
- [FastAPI](https://fastapi.tiangolo.com/) - Moderne Python web framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework

## 💡 Bidrag

Dette er et personlig prosjekt, men forslag og forbedringer er velkomne!

## 📞 Support

For spørsmål eller problemer, sjekk:
1. Denne README
2. Loggfiler i `data/logs/`
3. Console output når serveren kjører

## 🗺️ Roadmap

### v1.0 (Nåværende) ✅
- Tesla MVP med mock mode
- Web dashboard
- Automatisk oppdatering
- Database logging

### v2.0 (Planlagt)
- [ ] Hyundai Ioniq 5 OBD-II integrasjon
- [ ] To-bils sammenligning
- [ ] Raspberry Pi deployment guide
- [ ] Smart switch integrasjon

### v3.0 (Fremtidig)
- [ ] Strømpris integrasjon (Tibber/Nordpool)
- [ ] Kalender integrasjon
- [ ] Push-varsler
- [ ] Historikk-grafer
- [ ] Mobile app

---

**Versjon**: 1.0.0 (Tesla MVP)
**Sist oppdatert**: 2025-12-27
# Garasje
