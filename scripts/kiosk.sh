#!/usr/bin/env bash
# Chromium Genuine Kiosk Startup Script for Raspberry Pi OS

# Hide cursor after inactivity
xset s off
xset -dpms
xset s noblank

# Prevent screen saver / DPMS dimming during operation
unclutter -idle 0.5 -root &

# Wait for local dashboard service to become available
until curl -s http://localhost:5000/api/config > /dev/null; do
    echo "Waiting for Ambient Dashboard Flask service on port 5000..."
    sleep 1
done

# Launch Chromium in genuine kiosk mode
# Disable error bubbles, translation prompts, infobars, and restore session popups
exec chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --kiosk http://localhost:5000 \
    --incognito \
    --check-for-update-interval=31536000 \
    --disable-component-update \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --overscroll-history-navigation=0 \
    --fast \
    --fast-start
