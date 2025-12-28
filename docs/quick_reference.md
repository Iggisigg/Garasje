# Hurtigreferanse - Raspberry Pi

## 🚀 Hurtigstart

### 1. SSH inn i Pi
```bash
ssh pi@charging-manager.local
# Eller: ssh pi@192.168.1.100
```

### 2. Start/Stopp Service
```bash
# Status
sudo systemctl status charging-manager

# Start
sudo systemctl start charging-manager

# Stopp
sudo systemctl stop charging-manager

# Restart
sudo systemctl restart charging-manager

# Enable auto-start
sudo systemctl enable charging-manager

# Disable auto-start
sudo systemctl disable charging-manager
```

### 3. Se Logger
```bash
# Live logs (systemd)
sudo journalctl -u charging-manager -f

# Siste 100 linjer
sudo journalctl -u charging-manager -n 100

# App logs
tail -f ~/Garasje/data/logs/app.log

# Siste 50 linjer
tail -n 50 ~/Garasje/data/logs/app.log
```

### 4. Manuell Kjøring (Debug)
```bash
cd ~/Garasje
source venv/bin/activate
python main.py

# Med debug logging
LOG_LEVEL=DEBUG python main.py
```

### 5. Oppdater Applikasjon
```bash
cd ~/Garasje
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart charging-manager
```

### 6. Sjekk Status
```bash
# System info
htop                    # CPU/RAM
df -h                   # Disk
free -h                 # Memory
vcgencmd measure_temp   # Temperature

# Network
ip addr show wlan0      # IP-adresse
ping 8.8.8.8           # Internet

# Dashboard
curl http://localhost:8000/health
```

### 7. Reboot/Shutdown
```bash
# Reboot
sudo reboot

# Shutdown
sudo shutdown now
```

## 🔧 Vanlige Problemer

### Problem: Dashboard ikke tilgjengelig

**Sjekk service:**
```bash
sudo systemctl status charging-manager
```

**Sjekk om port 8000 lytter:**
```bash
sudo netstat -tulpn | grep 8000
```

**Test lokalt:**
```bash
curl http://localhost:8000/health
```

### Problem: Display fungerer ikke

**Sjekk display:**
```bash
tvservice -l
```

**Restart display driver:**
```bash
sudo rmmod rpi_ft5406
sudo modprobe rpi_ft5406
```

### Problem: For høy temperatur

**Sjekk temp:**
```bash
vcgencmd measure_temp
```

**Hvis > 70°C:**
- Sørg for god luftsirkulasjon
- Vurder kjølevifte
- Sjekk `htop` for CPU-bruk

### Problem: Database locked

**Sjekk prosesser:**
```bash
ps aux | grep python
```

**Kill gammel prosess:**
```bash
pkill -f "python main.py"
sudo systemctl restart charging-manager
```

## 📊 Nyttige Kommandoer

### System
```bash
# Se system info
cat /etc/os-release

# Oppdater system
sudo apt update && sudo apt upgrade -y

# Disk bruk
du -sh ~/Garasje/data/*

# Finn store filer
sudo find / -size +100M -ls 2>/dev/null
```

### Nettverk
```bash
# Se IP-adresse
hostname -I

# Test WiFi
iwconfig wlan0

# Restart nettverk
sudo systemctl restart dhcpcd
```

### Database
```bash
# Åpne database
cd ~/Garasje
source venv/bin/activate
sqlite3 data/charging_manager.db

# SQL kommandoer:
.tables                              # Vis tabeller
SELECT COUNT(*) FROM battery_readings;  # Tell rader
.quit                                # Avslutt
```

## 🔐 Sikkerhet

### Endre Passord
```bash
passwd
```

### Oppdater Firewall
```bash
# Status
sudo ufw status

# Tillat ny port
sudo ufw allow 8080/tcp

# Blokkér IP
sudo ufw deny from 192.168.1.50
```

### Backup
```bash
# Kjør backup
~/backup-charging-manager.sh

# Liste backups
ls -lh ~/backups/
```

## 📱 Fra Annen Enhet

### Åpne Dashboard
```
http://charging-manager.local:8000
http://192.168.1.100:8000
```

### SSH Tunnel (Hvis utenfor nettverket)
```bash
# På Mac/PC (eksempel)
ssh -L 8000:localhost:8000 pi@charging-manager.local

# Åpne i browser:
http://localhost:8000
```

## 🆘 Nødkommandoer

### Komplett Reset
```bash
# Stopp service
sudo systemctl stop charging-manager

# Slett database
rm ~/Garasje/data/charging_manager.db

# Slett cache
rm ~/Garasje/data/tesla_cache.json

# Start på nytt
sudo systemctl start charging-manager
```

### Factory Reset (Reinstaller App)
```bash
# Backup først!
cp -r ~/Garasje ~/Garasje.backup

# Slett alt
rm -rf ~/Garasje

# Klon på nytt
cd ~
git clone https://github.com/Iggisigg/Garasje.git
cd Garasje

# Setup (se hovedguide)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env

# Restart service
sudo systemctl restart charging-manager
```

---

**Tips**: Bookmark denne siden for rask tilgang til kommandoer!
