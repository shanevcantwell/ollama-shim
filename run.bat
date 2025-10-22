#!/bin/bash

# Function to check and potentially release the desired network port.
check_release_port() {
  PORT=11434
  PID=$(lsof -ti :$PORT)
    if [ ! -z "$PID" ]; then:
        echo "Process ID $PID holding on this port, terminating it."
        sudo kill ${pid}
      sleep 2 # Small delay before retry.
   fi;
}

# Define script directory and ensure navigation to that point securely
SCRIPT_DIR="$( cd -- "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd -P )"
echo "Executing from ${script_dir}"

cd "${SCRIPT_DIR}" || { echo 'Failed navigating directory!'; exit 1; }

check_release_port # Ensures the port isn’t bound elsewhere before continuing
python3 -m uvicorn ollama_shim:app --host 0.0.0.0 --port 11434 &
echo "Starting server process and keeping it running..."