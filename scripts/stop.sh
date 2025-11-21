#!/bin/bash
# Development script to stop Ollama Shim
# For production, use: systemctl stop ollama-shim

echo "Stopping Ollama Shim..."

if ! pgrep -f "uvicorn src.main:app" > /dev/null; then
    echo "Ollama Shim is not running."
    exit 0
fi

# Kill the process
pkill -f "uvicorn src.main:app"

# Wait a moment and verify
sleep 1

if pgrep -f "uvicorn src.main:app" > /dev/null; then
    echo "Warning: Process still running. Forcing shutdown..."
    pkill -9 -f "uvicorn src.main:app"
    sleep 1
fi

if pgrep -f "uvicorn src.main:app" > /dev/null; then
    echo "Error: Failed to stop Ollama Shim"
    exit 1
else
    echo "Ollama Shim stopped successfully."
fi