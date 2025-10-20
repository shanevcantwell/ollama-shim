@echo off
rem This will keep the window open to show logs or errors.
python.exe -m uvicorn ollama_shim:app --host 0.0.0.0 --port 11434
pause