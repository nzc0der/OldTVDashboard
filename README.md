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

## Easy 1-Step Installation for Raspberry Pi OS

Run the automated installer script from inside the project folder:

```bash
cd ambient-tv-dashboard
bash install.sh
```

The script automatically:
1. Installs all required system dependencies (`chromium`, `python3-pip`, `unclutter`, `curl`).
2. Installs required Python libraries (`flask`, `airtouch4pyapi`, `requests`, `suntime`, `tzdata`).
3. Dynamically generates and installs `systemd` background services configured for your exact project location and user account.
4. Enables and launches the dashboard backend and kiosk display automatically.

---

## Optional: Configure AirTouch 5 IP

If your AirTouch 5 system is on a specific static IP address, you can set it in `/etc/systemd/system/ambient-dashboard.service`:

```ini
Environment=AIRTOUCH_IP=192.168.1.100
```
Then restart the service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ambient-dashboard.service
```

---

## Testing

Run unit tests locally:

```bash
PYTHONPATH=. pytest tests/test_backend.py
```
