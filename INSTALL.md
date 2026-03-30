# Installation Guide

Quick installation instructions for production deployments.

## Linux/Ubuntu (systemd)

The easiest way to install on Linux is using the automated installation script:

```bash
# 1. Clone and setup
git clone https://github.com/shanevcantwell/ollama-shim.git
cd ollama-shim

# 2. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
nano .env  # Edit SHIM_PORT, BACKEND_BASE_URL, etc.

# 4. Run the installation script (requires sudo)
sudo bash scripts/install-linux-service.sh

# 5. Check status
sudo systemctl status ollama-shim
sudo journalctl -u ollama-shim -f
```

To uninstall:
```bash
sudo bash scripts/install-linux-service.sh --uninstall
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
pip install -r requirements.txt

# 3. Configure
copy .env.example .env
notepad .env  # Edit configuration

# 4. Create logs directory
mkdir logs

# 5. Install service
PowerShell -ExecutionPolicy Bypass -File scripts\install-windows-service.ps1

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
BACKEND_BASE_URL=http://localhost:1234 # Backend (LM Studio, llama-server, etc.) location
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
