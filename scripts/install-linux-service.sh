#!/bin/bash
# Script to install Ollama Shim as a systemd service on Ubuntu/Debian
#
# Run as root or with sudo:
# sudo bash install-linux-service.sh
#
# To uninstall:
# sudo bash install-linux-service.sh --uninstall

set -e

SERVICE_NAME="ollama-shim"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if .env exists
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo "ERROR: .env file not found at ${PROJECT_ROOT}/.env"
    exit 1
fi

# Load SHIM_PORT from .env
SHIM_PORT=$(grep -E "^SHIM_PORT\s*=" "${PROJECT_ROOT}/.env" | cut -d'=' -f2 | tr -d ' ')
if [ -z "$SHIM_PORT" ]; then
    echo "ERROR: SHIM_PORT is not defined in .env file"
    exit 1
fi

# Check if .venv exists
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo "ERROR: Virtual environment not found at ${PROJECT_ROOT}/.venv"
    exit 1
fi

PYTHON_EXE="${PROJECT_ROOT}/.venv/bin/python"
UVICORN_EXE="${PROJECT_ROOT}/.venv/bin/uvicorn"

if [ ! -f "$PYTHON_EXE" ]; then
    echo "ERROR: Python not found at $PYTHON_EXE"
    exit 1
fi

if [ ! -f "$UVICORN_EXE" ]; then
    echo "ERROR: Uvicorn not found at $UVICORN_EXE"
    exit 1
fi

# Parse arguments
if [ "$1" == "--uninstall" ]; then
    echo "Uninstalling ${SERVICE_NAME} service..."
    systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    systemctl disable ${SERVICE_NAME} 2>/dev/null || true
    rm -f ${SERVICE_FILE}
    systemctl daemon-reload
    echo "Service uninstalled successfully"
    exit 0
fi

echo "Installing ${SERVICE_NAME} as a systemd service..."
echo "  Project Root: ${PROJECT_ROOT}"
echo "  Port: ${SHIM_PORT}"

# Create service file
cat > ${SERVICE_FILE} <<EOF
[Unit]
Description=Ollama Shim - Ollama API to OpenAI-compatible bridge
Documentation=https://github.com/shanevcantwell/ollama-shim
After=network.target

[Service]
Type=simple
User=${SUDO_USER:-root}
WorkingDirectory=${PROJECT_ROOT}
ExecStart=${PYTHON_EXE} -m uvicorn src.main:app --host 0.0.0.0 --port ${SHIM_PORT}
Restart=always
RestartSec=5
EnvironmentFile=${PROJECT_ROOT}/.env
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}

# Start the service
systemctl start ${SERVICE_NAME}

echo ""
echo "Service installed and started successfully!"
echo ""
echo "To check service status:"
echo "  systemctl status ${SERVICE_NAME}"
echo ""
echo "To view logs:"
echo "  journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "To stop the service:"
echo "  systemctl stop ${SERVICE_NAME}"
echo ""
echo "To restart the service:"
echo "  systemctl restart ${SERVICE_NAME}"
echo ""
echo "To uninstall:"
echo "  sudo bash scripts/install-linux-service.sh --uninstall"
