# Ambient Smart Home TV Dashboard

A beautiful, always-on atmospheric display for a Raspberry Pi connected to a Panasonic TV. Designed to transform an unused television into a living piece of digital art displaying live climate zone temperatures, local weather for Ormond, Melbourne, and astronomical background themes.

---

## Features

1. **AirTouch 5 Live Zone Temperatures:**
   - Real room names, measured temperatures (°C), target setpoints, and AC operating mode.
   - Robust offline resilience: preserves last known readings with stale indicators if the connection drops.
   - Periodically refreshed without full page reloads.

2. **Ormond, Melbourne Local Weather:**
   - Powered by Open-Meteo API using exact Ormond coordinates (`-37.8992`, `145.0392`).
   - Current temperature, feels-like temperature, high/low range, wind speed, and precipitation chance.
   - Compact hourly forecast (next 7 hours) and 5-day outlook.

3. **Melbourne Clock & Date:**
   - Prominent typographic treatment in `Australia/Melbourne` timezone with daylight saving support.
   - Client-side execution with zero network overhead.

4. **Dynamic Evolving Atmospheric Background:**
   - Layered CSS gradients and ambient glows calculated against actual Ormond sunrise/sunset using `suntime`.
   - Transitions smoothly across Pre-dawn, Sunrise, Morning, Daytime, Sunset, Twilight, and Night palettes.

5. **Image Retention & Burn-in Precautions:**
   - Whole-layout pixel shifting (moves viewport 2–3px every 3 minutes).
   - Automatic evening visual dimming factor.
   - Predominantly dark aesthetic to protect older TV panels.

---

## Architecture

- **Backend:** Python 3 (Flask)
- **Integrations:** `airtouch4pyapi` for AirTouch 5, Open-Meteo for weather, `suntime` for astronomical calculations.
- **Frontend:** HTML5, CSS3, JavaScript (ES6+).
- **Kiosk Display:** Chromium browser in genuine `--kiosk` mode managed by `systemd`.

---

## Installation Guide for Raspberry Pi OS

### 1. Clone & Install Dependencies

```bash
cd /home/pi
git clone <your-repo-url> ambient-tv-dashboard
cd ambient-tv-dashboard

# Install required packages
sudo apt update
sudo apt install -y python3-pip chromium-browser unclutter

# Install Python requirements
pip3 install flask airtouch4pyapi requests suntime tzdata
```

### 2. Configure AirTouch IP

Set your AirTouch 5 unit's IP address in `systemd/ambient-dashboard.service` or export it as an environment variable:

```bash
export AIRTOUCH_IP=192.168.1.100
```

### 3. Set Up systemd Services

```bash
# Copy systemd service files
sudo cp systemd/ambient-dashboard.service /etc/systemd/system/
sudo cp systemd/ambient-kiosk.service /etc/systemd/system/

# Make kiosk script executable
chmod +x scripts/kiosk.sh

# Reload systemd daemon and enable services
sudo systemctl daemon-reload
sudo systemctl enable ambient-dashboard.service
sudo systemctl enable ambient-kiosk.service

# Start the dashboard backend and kiosk browser
sudo systemctl start ambient-dashboard.service
sudo systemctl start ambient-kiosk.service
```

---

## Testing

Run unit tests locally:

```bash
PYTHONPATH=. pytest tests/test_backend.py
```
