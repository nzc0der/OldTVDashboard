#!/usr/bin/env bash
# ==============================================================================
# Ambient Smart Home TV Dashboard — All-in-One Installer for Raspberry Pi OS
# ==============================================================================

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE} Ambient Smart Home TV Dashboard Setup ${NC}"
echo -e "${BLUE}=====================================================${NC}"

# Detect current working directory and user
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="${SUDO_USER:-$USER}"

echo -e "Project Directory : ${GREEN}${PROJECT_DIR}${NC}"
echo -e "Target User       : ${GREEN}${CURRENT_USER}${NC}"

# 1. Ensure executable permissions for kiosk script
echo -e "\n${BLUE}[1/5] Setting file permissions...${NC}"
chmod +x "${PROJECT_DIR}/scripts/kiosk.sh"
chmod +x "${PROJECT_DIR}/install.sh"

# 2. Install required system packages
echo -e "\n${BLUE}[2/5] Installing system dependencies (apt)...${NC}"
sudo apt update
sudo apt install -y python3-pip unclutter curl rclone

# Check for chromium browser binary
if apt-cache show chromium-browser >/dev/null 2>&1; then
    sudo apt install -y chromium-browser || sudo apt install -y chromium
else
    sudo apt install -y chromium || true
fi

# 3. Install required Python packages
echo -e "\n${BLUE}[3/5] Installing Python dependencies...${NC}"
pip3 install --break-system-packages flask airtouch4pyapi requests suntime tzdata 2>/dev/null || \
pip3 install flask airtouch4pyapi requests suntime tzdata

# 4. Generate systemd service files dynamically
echo -e "\n${BLUE}[4/5] Configuring systemd services...${NC}"

# Create backend dashboard service
sudo bash -c "cat <<EOF > /etc/systemd/system/ambient-dashboard.service
[Unit]
Description=Ambient Smart Home TV Dashboard Backend Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PORT=5000
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# Create kiosk browser service
sudo bash -c "cat <<EOF > /etc/systemd/system/ambient-kiosk.service
[Unit]
Description=Ambient Smart Home TV Dashboard Kiosk Browser
After=ambient-dashboard.service graphical.target
Wants=ambient-dashboard.service

[Service]
Type=simple
User=${CURRENT_USER}
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/${CURRENT_USER}/.Xauthority
ExecStart=${PROJECT_DIR}/scripts/kiosk.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF"

# 5. Enable and start services
echo -e "\n${BLUE}[5/5] Reloading systemd and starting dashboard...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable ambient-dashboard.service
sudo systemctl enable ambient-kiosk.service
sudo systemctl restart ambient-dashboard.service
sudo systemctl restart ambient-kiosk.service

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN} Setup Complete! ${NC}"
echo -e "${GREEN} The ambient TV dashboard is now installed & running. ${NC}"
echo -e "${GREEN} You can access it locally at: http://localhost:5000 ${NC}"
echo -e "${GREEN}=====================================================${NC}"
