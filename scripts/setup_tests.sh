#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "testenv" ]; then
    python3 -m venv testenv
fi

# Activate the virtual environment and install pytest-httpx
source testenv/bin/activate
pip install --upgrade pip && pip install pytest pytest-httpx

# Run the tests with detailed output
pytest --show-capture=no -v tests/test_api.py::test_generate_non_streaming

# Deactivate to clean up
deactivate

# Return to original directory if needed
cd -