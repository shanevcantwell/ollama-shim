# Installation Guide

Quick installation instructions for production deployments.

## Linux/Ubuntu (systemd)

```bash
# 1. Install to /opt
sudo mkdir -p /opt/ollama-shim
sudo cp -r . /opt/ollama-shim/
cd /opt/ollama-shim

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. Configure
cp .env.example .env
nano .env  # Edit SHIM_PORT, LM_STUDIO_BASE_URL, etc.

# 4. Install and start service
sudo cp ollama-shim.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ollama-shim

# 5. Check status
sudo systemctl status ollama-shim
sudo journalctl -u ollama-shim -f
```

## Windows (NSSM Service)

**Prerequisites:** Install NSSM from https://nssm.cc/download or `choco install nssm`

```powershell
# 1. Install to Program Files (Run as Administrator)
mkdir "C:\Program Files\ollama-shim"
# Copy project files here

# 2. Create virtual environment
cd "C:\Program Files\ollama-shim"
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# 3. Configure
copy .env.example .env
notepad .env  # Edit configuration

# 4. Create logs directory
mkdir logs

# 5. Install service
PowerShell -ExecutionPolicy Bypass -File install-windows-service.ps1

# 6. Start service
net start OllamaShim
```

## Development Mode

**Linux/WSL2:**
```bash
./scripts/run.sh  # Press Ctrl+C to stop
```

**Windows:**
```cmd
scripts\run.bat  # Press Ctrl+C to stop
```

## Configuration

Edit `.env` file:
```ini
SHIM_PORT=11434                          # Port to listen on
LM_STUDIO_BASE_URL=http://localhost:1234 # LM Studio location
API_TIMEOUT=30.0
RESPONSE_TIMEOUT=300.0
LOG_LEVEL=INFO
```

## Firewall

**Linux:**
```bash
sudo ufw allow 11434/tcp
```

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "Ollama Shim" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```
