#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
VENV_DIR="./.venv"

echo "Starting Ollama Shim server in $PROJECT_ROOT"
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment
if [ -d $VENV_DIR ]; then
    source $VENV_DIR/bin/activate
else
    echo "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Install dependencies if requirements.txt exists
# if [ -f "requirements.txt" ]; then
#     pip install -r requirements.txt --update
# fi

# Run the server
python -m uvicorn src.main:app --host 0.0.0.0 --port 11434 --reload
