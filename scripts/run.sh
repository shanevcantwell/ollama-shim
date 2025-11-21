#!/bin/bash
# Development script to start Ollama Shim
# For production, use systemd service (see ollama-shim.service)

# Get the script's directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

# Check if already running
if pgrep -f "uvicorn src.main:app" > /dev/null; then
    echo "Error: Ollama Shim appears to be already running"
    echo "Use stop.sh to stop it first, or run: pkill -f 'uvicorn src.main:app'"
    exit 1
fi

# Activate virtual environment if it exists
for VENV_DIR in .venv venv env .venv_linux; do
    if [ -d "$VENV_DIR" ]; then
        echo "Activating virtual environment: $VENV_DIR"
        source "$VENV_DIR/bin/activate"
        break
    fi
done

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using default configuration."
    echo "Copy .env.example to .env and configure as needed."
fi

# Start server (Python/pydantic handles .env loading and validation)
echo "Starting Ollama Shim in development mode..."
echo "Press Ctrl+C to stop the server."
echo ""

# Run in foreground with auto-reload for development
python -m uvicorn src.main:app --host 0.0.0.0 --reload
