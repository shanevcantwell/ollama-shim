# Create scripts directory if it doesn't exist (silently)
mkdir -p scripts 2>/dev/null || true

# Create run_tests.sh with proper content
cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash

# Create virtual environment if needed
if [ ! -d "testenv" ]; then
    python3 -m venv testenv
fi

# Activate the virtual environment and install pytest-httpx
source testenv/bin/activate || exit 1
pip install --upgrade pip && pip install pytest pytest-httpx || { deactivate; exit 1; }

# Run the specific test with detailed output
pytest -v --show-capture=no tests/test_api.py::test_generate_non_streaming

# Record and return the result
TEST_RESULT=$?
deactivate
exit $TEST_RESULT
EOF

# Make it executable and run
chmod +x scripts/run_tests.sh && ./scripts/run_tests.sh || echo "Test execution failed, please check output above"