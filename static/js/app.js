/**
 * Ambient TV Dashboard Core Frontend Controller
 * Timezone: Australia/Melbourne
 */

// Weather icon mapping
const WEATHER_ICONS = {
    "clear": "☀️",
    "partly-cloudy": "🌤️",
    "cloudy": "☁️",
    "fog": "🌫️",
    "drizzle": "🌦️",
    "rain": "🌧️",
    "snow": "❄️",
    "thunderstorm": "🌩️"
};

// Atmospheric theme color definitions (gradient start, mid, end, glow accent)
const PALETTES = {
    predawn: {
        start: "#050b18",
        mid: "#0a1628",
        end: "#111827",
        glow: "rgba(30, 58, 138, 0.2)"
    },
    sunrise: {
        start: "#1f1d36",
        mid: "#3d2c8d",
        end: "#e94560",
        glow: "rgba(255, 154, 60, 0.25)"
    },
    morning: {
        start: "#0f172a",
        mid: "#1e293b",
        end: "#0369a1",
        glow: "rgba(56, 189, 248, 0.2)"
    },
    daytime: {
        start: "#081c3b",
        mid: "#0f3460",
        end: "#16213e",
        glow: "rgba(72, 149, 239, 0.2)"
    },
    sunset: {
        start: "#1a0b2e",
        mid: "#4b1e4a",
        end: "#8b263e",
        glow: "rgba(247, 37, 133, 0.25)"
    },
    twilight: {
        start: "#0d0221",
        mid: "#0f0e17",
        end: "#190933",
        glow: "rgba(114, 9, 183, 0.2)"
    },
    night: {
        start: "#030712",
        mid: "#0b0f19",
        end: "#050814",
        glow: "rgba(30, 41, 59, 0.15)"
    }
};

class DashboardApp {
    constructor() {
        self = this;
        this.sunTimes = { sunrise_hour: 6.5, sunset_hour: 20.0 };
        this.shiftX = 0;
        this.shiftY = 0;
        this.lastAirTouchData = null;
        this.lastWeatherData = null;

        this.initClock();
        this.initPixelShift();
        this.fetchData();

        // Refresh data every 30 seconds
        setInterval(() => this.fetchData(), 30000);
    }

    /* -------------------------------------------------------------
     * 1. Live Clock & Date in Melbourne Time
     * ------------------------------------------------------------- */
    initClock() {
        const updateClock = () => {
            const now = new Date();
            // Format time HH:MM
            const timeOptions = {
                timeZone: 'Australia/Melbourne',
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            };
            const dateOptions = {
                timeZone: 'Australia/Melbourne',
                weekday: 'long',
                day: 'numeric',
                month: 'long'
            };

            const timeStr = new Intl.DateTimeFormat('en-AU', timeOptions).format(now);
            const dateStr = new Intl.DateTimeFormat('en-AU', dateOptions).format(now);

            document.getElementById('clock-time').textContent = timeStr;
            document.getElementById('clock-date').textContent = dateStr;

            // Evolve background theme dynamically
            this.updateBackgroundTheme(now);
        };

        updateClock();
        setInterval(updateClock, 1000);
    }

    /* -------------------------------------------------------------
     * 2. Dynamic Evolving Gradient Background System
     * ------------------------------------------------------------- */
    updateBackgroundTheme(now) {
        // Calculate decimal local hour in Melbourne (0.00 - 23.99)
        const melbTimeStr = new Intl.DateTimeFormat('en-US', {
            timeZone: 'Australia/Melbourne',
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric',
            hour12: false
        }).format(now);

        const parts = melbTimeStr.split(':');
        const currentDecimalHour = parseInt(parts[0], 10) + (parseInt(parts[1], 10) / 60);

        const sr = this.sunTimes.sunrise_hour || 6.5;
        const ss = this.sunTimes.sunset_hour || 20.0;

        let palette = PALETTES.night;
        let dimFactor = 1.0;

        if (currentDecimalHour < sr - 1.5) {
            palette = PALETTES.night;
            dimFactor = 0.75;
        } else if (currentDecimalHour < sr - 0.3) {
            palette = PALETTES.predawn;
            dimFactor = 0.85;
        } else if (currentDecimalHour < sr + 1.5) {
            palette = PALETTES.sunrise;
            dimFactor = 0.95;
        } else if (currentDecimalHour < sr + 4.0) {
            palette = PALETTES.morning;
            dimFactor = 1.0;
        } else if (currentDecimalHour < ss - 1.5) {
            palette = PALETTES.daytime;
            dimFactor = 1.0;
        } else if (currentDecimalHour < ss + 0.8) {
            palette = PALETTES.sunset;
            dimFactor = 0.95;
        } else if (currentDecimalHour < ss + 2.5) {
            palette = PALETTES.twilight;
            dimFactor = 0.85;
        } else {
            palette = PALETTES.night;
            dimFactor = 0.7;
        }

        const root = document.documentElement;
        root.style.setProperty('--bg-gradient-start', palette.start);
        root.style.setProperty('--bg-gradient-mid', palette.mid);
        root.style.setProperty('--bg-gradient-end', palette.end);
        root.style.setProperty('--bg-accent-glow', palette.glow);
        root.style.setProperty('--dim-factor', dimFactor.toString());
    }

    /* -------------------------------------------------------------
     * 3. Fetch Data from Backend API
     * ------------------------------------------------------------- */
    async fetchData() {
        try {
            const resp = await fetch('/api/data');
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            if (data.sun) {
                this.sunTimes = data.sun;
                document.getElementById('sun-rise').textContent = data.sun.sunrise || '06:30';
                document.getElementById('sun-set').textContent = data.sun.sunset || '20:00';
            }

            if (data.airtouch) {
                this.renderAirTouch(data.airtouch);
            }

            if (data.weather) {
                this.renderWeather(data.weather);
            }
        } catch (e) {
            console.warn('API update failed:', e);
            this.markDataStale();
        }
    }

    /* -------------------------------------------------------------
     * 4. Render AirTouch Room Temperatures & Status
     * ------------------------------------------------------------- */
    renderAirTouch(airtouch) {
        this.lastAirTouchData = airtouch;

        const connBadge = document.getElementById('connection-badge');
        const connText = document.getElementById('conn-text');

        if (airtouch.connected) {
            connBadge.innerHTML = '<span class="badge-dot dot-live"></span><span id="conn-text">AirTouch Live</span>';
        } else {
            connBadge.innerHTML = '<span class="badge-dot dot-stale"></span><span id="conn-text">AirTouch Stale</span>';
        }

        const acModeText = document.getElementById('ac-mode-text');
        acModeText.textContent = `AC: ${airtouch.mode || 'Standby'}`;

        const roomsContainer = document.getElementById('rooms-container');
        roomsContainer.innerHTML = '';

        const rooms = airtouch.rooms || [];
        rooms.forEach(room => {
            const card = document.createElement('div');
            card.className = `room-card ${room.is_on ? 'active-zone' : ''}`;

            const measuredDisplay = room.has_sensor && room.temperature !== null
                ? `${room.temperature}°C`
                : '--°C';

            const targetDisplay = room.target_temperature
                ? `Set ${room.target_temperature}°C`
                : (room.open_percent !== undefined ? `Open ${room.open_percent}%` : '');

            const statusText = room.is_on ? 'Active' : 'Off';

            card.innerHTML = `
                <div class="room-card-header">
                    <span class="room-name">${room.name}</span>
                    <span class="room-status-indicator">${statusText}</span>
                </div>
                <div class="room-temp-wrapper">
                    <span class="room-temp-measured">${measuredDisplay}</span>
                    <span class="room-temp-target">${targetDisplay}</span>
                </div>
            `;
            roomsContainer.appendChild(card);
        });

        document.getElementById('rooms-updated-time').textContent = airtouch.last_updated
            ? `Updated ${new Date(airtouch.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
            : 'Updated recently';
    }

    /* -------------------------------------------------------------
     * 5. Render Weather & Forecast Data
     * ------------------------------------------------------------- */
    renderWeather(weather) {
        this.lastWeatherData = weather;
        const curr = weather.current || {};

        document.getElementById('current-temp').textContent = `${curr.temperature}°`;
        document.getElementById('feels-like').textContent = `Feels like ${curr.feels_like}°`;
        document.getElementById('weather-desc').textContent = curr.condition || 'Clear';
        document.getElementById('temp-high').textContent = `${curr.high}°`;
        document.getElementById('temp-low').textContent = `${curr.low}°`;
        document.getElementById('precip-chance').textContent = `${curr.precipitation_chance}%`;
        document.getElementById('wind-speed').textContent = `${curr.wind_speed} km/h`;

        const iconSymbol = WEATHER_ICONS[curr.icon] || '🌤️';
        document.getElementById('weather-icon').textContent = iconSymbol;

        // Render Hourly Forecast
        const hourlyContainer = document.getElementById('hourly-forecast');
        hourlyContainer.innerHTML = '';
        (weather.hourly || []).slice(0, 7).forEach(item => {
            const el = document.createElement('div');
            el.className = 'hourly-item';
            const hIcon = WEATHER_ICONS[item.icon] || '🌤️';
            el.innerHTML = `
                <span class="hourly-time">${item.time}</span>
                <span class="hourly-icon">${hIcon}</span>
                <span class="hourly-temp">${item.temp}°</span>
            `;
            hourlyContainer.appendChild(el);
        });

        // Render 5-Day Forecast
        const dailyContainer = document.getElementById('daily-forecast');
        dailyContainer.innerHTML = '';
        (weather.daily || []).slice(0, 5).forEach(item => {
            const row = document.createElement('div');
            row.className = 'daily-row';
            const dIcon = WEATHER_ICONS[item.icon] || '🌤️';
            row.innerHTML = `
                <span class="daily-day">${item.day}</span>
                <span class="daily-cond">${dIcon} ${item.condition}</span>
                <div class="daily-temps">
                    <span class="daily-high">${item.high}°</span>
                    <span class="daily-low">${item.low}°</span>
                </div>
            `;
            dailyContainer.appendChild(row);
        });
    }

    markDataStale() {
        const connBadge = document.getElementById('connection-badge');
        if (connBadge) {
            connBadge.innerHTML = '<span class="badge-dot dot-stale"></span><span>Offline</span>';
        }
    }

    /* -------------------------------------------------------------
     * 6. Image Retention & Burn-in Precautions (Pixel Shifting)
     * ------------------------------------------------------------- */
    initPixelShift() {
        // Shift entire viewport by 2-3px every 3 minutes
        setInterval(() => {
            // Pick offset [-3, -2, -1, 0, 1, 2, 3]
            const offsets = [-3, -2, -1, 0, 1, 2, 3];
            this.shiftX = offsets[Math.floor(Math.random() * offsets.length)];
            this.shiftY = offsets[Math.floor(Math.random() * offsets.length)];

            document.documentElement.style.setProperty('--shift-x', `${this.shiftX}px`);
            document.documentElement.style.setProperty('--shift-y', `${this.shiftY}px`);
        }, 180000); // Every 3 minutes
    }
}

// Initialize application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DashboardApp();
});
