#!/bin/bash
# This script starts the Ollama Shim FastAPI application, for use in a Linux/WSL environment.

# --- Load .env file if it exists ---
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
fi

# --- Configuration ---
# SHIM_PORT is now expected to be loaded from the .env file.
# The script will fail if it's not set.
if [ -z "$SHIM_PORT" ]; then
    echo "Error: SHIM_PORT is not set. Please define it in your .env file."
    exit 1
fi

# Activate Linux virtual environment if it exists
if [ -d ".venv_linux" ]; then
  echo "Activating Linux virtual environment..."
  source .venv_linux/bin/activate
else
  echo "Warning: .venv_linux not found. Using system Python."
fi

# --- Start Server ---
echo "Starting Ollama Shim server on port $SHIM_PORT..."
echo "Press Ctrl+C to stop the server."
# Running in the foreground to provide direct feedback and avoid orphaned processes.
python -m uvicorn src.main:app --host 0.0.0.0 --port $SHIM_PORT