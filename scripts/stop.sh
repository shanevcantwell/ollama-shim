#!/bin/bash
# This script stops the Ollama Shim FastAPI application.

# --- Configuration ---
PID_FILE="../ollama_shim.pid"

# --- Stop Server ---
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Found PID file. Attempting to stop server with PID: $PID..."
    
    # Check if the process is running
    if kill -0 $PID 2>/dev/null; then
        kill -9 $PID
        echo "Server stopped successfully."
    else
        echo "Process with PID $PID not found. It might have already been stopped."
    fi
    
    # --- Cleanup ---
    rm "$PID_FILE"
    echo "PID file removed."
else
    echo "PID file not found. Is the server running?"
fi
