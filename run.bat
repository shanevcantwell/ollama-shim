@echo off 
echo Starting Ollama Shim server...
cd /d "%~dp0"
python -m uvicorn ollama_shim:app --host 0.0.0.0 --port 11435
