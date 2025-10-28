@echo off
REM This script starts the Ollama Shim FastAPI application on Windows.

REM --- Activate virtual environment ---
IF EXIST .\venv\Scripts\activate (
    echo "Activating virtual environment..."
    call .\venv\Scripts\activate
) ELSE (
    echo "Virtual environment not found."
)

REM --- Read SHIM_PORT from .env file ---
FOR /F "usebackq tokens=1,2 delims==" %%A IN (`findstr /R "^SHIM_PORT=" .env`) DO (
    FOR /F "tokens=1" %%C IN ("%%B") DO (
        SET "SHIM_PORT=%%C"
    )
)

IF NOT DEFINED SHIM_PORT (
    echo "ERROR: SHIM_PORT is not defined in the .env file."
    goto :eof
)

REM --- Start Server ---
echo "Starting Ollama Shim server on port %SHIM_PORT%..."
echo "Press Ctrl+C to stop the server."
python -m uvicorn src.main:app --host 0.0.0.0 --port %SHIM_PORT%