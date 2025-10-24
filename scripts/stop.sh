#!/bin/bash

PORT=11434
echo "Attempting to stop the service running on port $PORT..."

PID=$(lsof -t -i:$PORT)

if [ -z "$PID" ]; then
    echo "No service found running on port $PORT."
else
    echo "Found service with PID: $PID. Stopping it now..."
    kill -9 $PID
    echo "Service stopped."
fi
