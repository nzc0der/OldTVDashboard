#!/usr/bin/env bash
# Chromium Genuine Kiosk Startup Script for Raspberry Pi OS

# Hide cursor and disable screen blanking/DPMS (X11)
if command -v xset >/dev/null 2>&1; then
    xset s off 2>/dev/null || true
    xset -dpms 2>/dev/null || true
    xset s noblank 2>/dev/null || true
fi

# Prevent screen saver / DPMS dimming during operation
if command -v unclutter >/dev/null 2>&1; then
    unclutter -idle 0.5 -root >/dev/null 2>&1 &
fi

# Wait for local dashboard service to become available
until curl -s http://localhost:5000/api/config > /dev/null; do
    echo "Waiting for Ambient Dashboard Flask service on port 5000..."
    sleep 1
done

# Determine chromium executable (chromium-browser or chromium)
CHROMIUM_CMD="chromium-browser"
if ! command -v chromium-browser >/dev/null 2>&1 && command -v chromium >/dev/null 2>&1; then
    CHROMIUM_CMD="chromium"
fi

# Launch Chromium in genuine kiosk mode filling the entire display
exec $CHROMIUM_CMD \
    --noerrdialogs \
    --disable-infobars \
    --kiosk \
    --start-fullscreen \
    --window-position=0,0 \
    --start-maximized \
    --incognito \
    --no-first-run \
    --disable-translate \
    --disable-features=TranslateUI,TouchpadOverscrollHistoryNavigation \
    --disable-component-update \
    --disable-session-crashed-bubble \
    --check-for-update-interval=31536000 \
    --fast \
    --fast-start \
    http://localhost:5000
