#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Starting Ollama Shim server in $SCRIPT_DIR"
cd "$SCRIPT_DIR" || exit 1 # Navigate to the script's directory or exit if failed.

python3 -m uvicorn main:app --host 0.0.0.0 --port 11434 --reload
