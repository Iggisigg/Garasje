# Raspberry Pi Setup Guide

## Hardware Oppsett - Raspberry Pi 3 Model B+ med Display v1.1

### Del 1: Montering av Display

**Komponenter du trenger:**
- Raspberry Pi 3 Model B+
- Raspberry Pi Touch Display v1.1 (7")
- Display adapter board (følger med display)
- Strømforsyning (5V 2.5A minimum)
- microSD kort (minimum 16GB, anbefalt 32GB)
- Ribbon kabel for DSI (følger med display)
- 4x jumper wires for strøm (følger med display)

**Monteringstrinn:**

1. **Display Adapter Board til Pi**
   ```
   Koble display adapter board til Raspberry Pi:
   - DSI port på Pi → Ribbon kabel → Display adapter board
   - Løft opp den lille plastikklåsen på DSI-porten på Pi
   - Sett inn ribbon kabelen (blå side mot USB-portene)
   - Trykk ned låsen for å sikre kabelen
   ```

2. **Strømforbindelser (GPIO)**
   ```
   Koble 4 jumper wires fra display adapter til Pi GPIO:
   - 5V (rød)   → GPIO Pin 2 eller 4
   - GND (svart) → GPIO Pin 6
   - 5V (rød)   → GPIO Pin 2 eller 4  (andre 5V)
   - GND (svart) → GPIO Pin 6 (andre GND)

   Alternativt: Bruk USB micro-til-micro kabel mellom Pi og display
   ```

3. **Sikre Oppsettet**
   - Fest Pi til display-backen med medfølgende skruer
   - Eller bruk et beskyttende case som støtter display

### Del 2: Installere Raspberry Pi OS

**Trinn 1: Forbered SD-kort**

1. **Last ned Raspberry Pi Imager**
   - macOS: https://www.raspberrypi.com/software/
   - Eller bruk Homebrew: `brew install --cask raspberry-pi-imager`

2. **Flash OS til SD-kort**
   ```bash
   # Åpne Raspberry Pi Imager
   # 1. Velg "Raspberry Pi OS (64-bit)" (Debian Bookworm)
   # 2. Velg SD-kort
   # 3. Trykk "Next"

   # I innstillinger (⚙️):
   # - Sett hostname: charging-manager
   # - Enable SSH (med password authentication)
   # - Sett brukernavn: pi
   # - Sett passord: [ditt passord]
   # - Konfigurer WiFi (SSID og passord)
   # - Sett locale: Europe/Oslo, nb_NO
   # - Sett keyboard: Norwegian

   # Trykk "Save" og deretter "Yes" for å skrive
   ```

3. **Boot Pi**
   - Sett SD-kort inn i Pi
   - Koble til strøm (display skal lyse opp)
   - Vent 1-2 minutter for første boot

### Del 3: Første Gangs Konfigurasjon

**Trinn 1: Koble til via SSH (fra Mac)**

```bash
# Finn Pi sin IP-adresse (sjekk router eller bruk)
ping charging-manager.local

# SSH inn i Pi
ssh pi@charging-manager.local
# Passord: [det du satte i Imager]
```

**Trinn 2: Oppdater System**

```bash
# Oppdater pakkelister
sudo apt update

# Oppgrader installerte pakker
sudo apt upgrade -y

# Installer nødvendige verktøy
sudo apt install -y git vim htop
```

**Trinn 3: Konfigurer Display**

```bash
# Display skal fungere automatisk, men hvis ikke:
sudo raspi-config

# Velg:
# 2. Display Options
#   → D1 Resolution → velg ønsket oppløsning
#   → D3 Screen Blanking → Disable (forhindre at skjerm slukker)

# Reboot
sudo reboot
```

**Trinn 4: Enable Auto-Login til Desktop (Valgfritt)**

```bash
sudo raspi-config

# Velg:
# 1. System Options
#   → S5 Boot / Auto Login
#     → B4 Desktop Autologin (Desktop GUI, automatically logged in as 'pi')

# Reboot
sudo reboot
```

### Del 4: Installere Ladeprioriteringssystemet

**Trinn 1: Klon Repository**

```bash
# Naviger til hjemmemappen
cd ~

# Klon prosjektet
git clone https://github.com/Iggisigg/Garasje.git
cd Garasje

# Sjekk ut v2.0.0
git checkout v2.0.0
```

**Trinn 2: Installer Python Dependencies**

```bash
# Installer Python 3.11+ (hvis ikke allerede installert)
python3 --version  # Sjekk versjon (skal være 3.9+)

# Opprett virtual environment
python3 -m venv venv

# Aktiver venv
source venv/bin/activate

# Oppgrader pip
pip install --upgrade pip

# Installer dependencies
pip install -r requirements.txt
```

**Trinn 3: Konfigurer .env**

```bash
# Kopier .env.example
cp .env.example .env

# Rediger .env
nano .env
```

**Innhold i .env:**
```env
# Tesla Fleet API Configuration
TESLA_CLIENT_ID=din_client_id_her
TESLA_CLIENT_SECRET=din_client_secret_her
TESLA_CACHE_FILE=data/tesla_cache.json
TESLA_REGION=EU

# Application Configuration
TESLA_MOCK_MODE=false
IONIQ_MOCK_MODE=true
UPDATE_INTERVAL_MINUTES=60
CHARGE_THRESHOLD_PERCENT=80

# Web Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_PATH=data/charging_manager.db

# Logging
LOG_LEVEL=INFO
```

**Trinn 4: Kjør OAuth Setup (hvis Tesla ekte data)**

```bash
# Aktiver venv hvis ikke allerede gjort
source venv/bin/activate

# Kjør setup script
python scripts/setup_tesla_fleet.py

# Følg instruksjonene i terminalen
# (Dette åpner browser for Tesla-innlogging)
```

**Trinn 5: Test Applikasjonen**

```bash
# Start serveren
python main.py

# Du skal se:
# ============================================================
# Ladeprioriteringssystem
# Tesla Model Y MVP
# ============================================================
#
# Configuration:
#   Tesla Mock Mode: False
#   ...
#
# Dashboard available at: http://0.0.0.0:8000
```

**Trinn 6: Test fra en annen enhet**

```bash
# På Mac/Phone, åpne browser:
http://charging-manager.local:8000

# Eller bruk Pi sin IP:
http://192.168.1.XXX:8000
```

### Del 5: Sette opp Auto-Start (systemd)

**Trinn 1: Opprett systemd Service**

```bash
# Opprett service fil
sudo nano /etc/systemd/system/charging-manager.service
```

**Innhold:**
```ini
[Unit]
Description=EV Charging Manager
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Garasje
Environment="PATH=/home/pi/Garasje/venv/bin"
ExecStart=/home/pi/Garasje/venv/bin/python /home/pi/Garasje/main.py
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/pi/Garasje/data/logs/systemd.log
StandardError=append:/home/pi/Garasje/data/logs/systemd.log

[Install]
WantedBy=multi-user.target
```

**Trinn 2: Aktiver Service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (starter automatisk ved boot)
sudo systemctl enable charging-manager.service

# Start service nå
sudo systemctl start charging-manager.service

# Sjekk status
sudo systemctl status charging-manager.service

# Følg logger live
sudo journalctl -u charging-manager.service -f
```

**Trinn 3: Test Auto-Start**

```bash
# Reboot Pi
sudo reboot

# Vent 1-2 minutter, deretter sjekk status
ssh pi@charging-manager.local
sudo systemctl status charging-manager.service

# Dashboardet skal være tilgjengelig:
# http://charging-manager.local:8000
```

### Del 6: Konfigurasjon av Touch Display Dashboard

**Alternativ 1: Chromium i Kiosk-modus (Anbefalt)**

```bash
# Installer Chromium (hvis ikke installert)
sudo apt install -y chromium-browser unclutter

# Opprett autostart script
mkdir -p ~/.config/autostart

nano ~/.config/autostart/charging-dashboard.desktop
```

**Innhold:**
```desktop
[Desktop Entry]
Type=Application
Name=Charging Dashboard
Exec=/home/pi/start-dashboard.sh
X-GNOME-Autostart-enabled=true
```

**Opprett startup script:**
```bash
nano ~/start-dashboard.sh
```

**Innhold:**
```bash
#!/bin/bash

# Vent på at serveren starter
sleep 15

# Slå av skjermblanking
xset s off
xset -dpms
xset s noblank

# Skjul musepeker etter 1 sekund
unclutter -idle 1 &

# Start Chromium i kiosk mode
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  http://localhost:8000
```

**Gjør executable:**
```bash
chmod +x ~/start-dashboard.sh
```

**Alternativ 2: Firefox i Kiosk-modus**

```bash
sudo apt install -y firefox-esr

nano ~/.config/autostart/charging-dashboard.desktop
```

**Innhold:**
```desktop
[Desktop Entry]
Type=Application
Name=Charging Dashboard
Exec=firefox --kiosk http://localhost:8000
X-GNOME-Autostart-enabled=true
```

### Del 7: Nettverkskonfigurasjon

**Sett Statisk IP (Anbefalt)**

```bash
# Rediger dhcpcd.conf
sudo nano /etc/dhcpcd.conf
```

**Legg til nederst:**
```conf
# Static IP for charging-manager
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

**Restart networking:**
```bash
sudo systemctl restart dhcpcd
```

**Test:**
```bash
# Fra Mac/Phone:
ping 192.168.1.100
curl http://192.168.1.100:8000/health
```

### Del 8: Vedlikehold og Feilsøking

**Sjekk Logs:**
```bash
# Systemd logs
sudo journalctl -u charging-manager.service -n 100

# Applikasjon logs
tail -f ~/Garasje/data/logs/app.log

# System logs
dmesg | tail
```

**Restart Service:**
```bash
sudo systemctl restart charging-manager.service
```

**Oppdater Applikasjon:**
```bash
cd ~/Garasje
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart charging-manager.service
```

**Display Feilsøking:**
```bash
# Sjekk om display er detektert
tvservice -l

# Rotere display (hvis opp-ned)
sudo nano /boot/config.txt
# Legg til: lcd_rotate=2
sudo reboot
```

**Sjekk Ressursbruk:**
```bash
htop           # CPU og minne
df -h          # Disk space
free -h        # Minne
```

### Del 9: Sikkerhet (Anbefalt)

**Endre Standard Passord:**
```bash
passwd
# Sett sterkt passord
```

**Oppdater Regelmessig:**
```bash
# Ugentlig oppdatering
sudo apt update && sudo apt upgrade -y
```

**Firewall (Valgfritt):**
```bash
sudo apt install -y ufw

# Tillat SSH
sudo ufw allow ssh

# Tillat HTTP (port 8000)
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable
```

**Automatisk Backups:**
```bash
# Opprett backup script
nano ~/backup-charging-manager.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR

# Backup database og config
tar -czf $BACKUP_DIR/charging-manager-$DATE.tar.gz \
  ~/Garasje/data/charging_manager.db \
  ~/Garasje/.env

# Slett backups eldre enn 30 dager
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

```bash
chmod +x ~/backup-charging-manager.sh

# Legg til i crontab (daglig kl 02:00)
crontab -e

# Legg til:
0 2 * * * /home/pi/backup-charging-manager.sh
```

### Del 10: Ytterligere Optimalisering

**Reduser Skjermlysstyrke (Spare strøm):**
```bash
# Installér rpi-backlight
sudo apt install -y python3-rpi-backlight

# Sett lysstyrke (0-255)
rpi-backlight --brightness 128
```

**Disable Bluetooth (Hvis ikke brukt):**
```bash
sudo nano /boot/config.txt

# Legg til:
dtoverlay=disable-bt

sudo systemctl disable hciuart.service
sudo systemctl disable bluetooth.service

sudo reboot
```

**Overvåk Temperatur:**
```bash
# Sjekk CPU temperatur
vcgencmd measure_temp

# Installer overvåkning
sudo apt install -y lm-sensors
sensors
```

## Fullstendig Setup Sjekkliste

- [ ] Hardware sammenkoblet (Display + Pi)
- [ ] Raspberry Pi OS flashet til SD-kort
- [ ] SSH konfigurert og testet
- [ ] System oppdatert (`apt update && upgrade`)
- [ ] Display fungerer
- [ ] Git repository klonet
- [ ] Python venv opprettet
- [ ] Dependencies installert
- [ ] .env konfigurert
- [ ] Tesla OAuth fullført (hvis ekte data)
- [ ] Applikasjon testet manuelt
- [ ] systemd service opprettet og enabled
- [ ] Auto-start testet (reboot)
- [ ] Kiosk-modus konfigurert (Chromium/Firefox)
- [ ] Dashboard vises på touch screen
- [ ] Statisk IP satt
- [ ] Tilgjengelig fra andre enheter på nettverket
- [ ] Backup script opprettet
- [ ] Sikkerhet (passord, firewall)

## Estimert Tidsbruk

- Hardware oppsett: 15-30 min
- OS installasjon: 20-30 min
- Systemkonfigurasjon: 30-45 min
- Applikasjonsinstallasjon: 30-60 min
- Auto-start konfigurasjon: 20-30 min
- Testing og finjustering: 30-60 min

**Total**: 2.5-4 timer (første gang)

## Support

Ved problemer:
1. Sjekk logs: `sudo journalctl -u charging-manager.service`
2. Sjekk app logs: `~/Garasje/data/logs/app.log`
3. Test manuelt: `cd ~/Garasje && source venv/bin/activate && python main.py`
4. Sjekk GitHub Issues: https://github.com/Iggisigg/Garasje/issues

---

**Guide versjon**: 1.0
**Laget for**: Raspberry Pi 3 Model B+ med Touch Display v1.1
**Testet med**: Raspberry Pi OS (64-bit) Bookworm
**Dato**: 2025-12-28
