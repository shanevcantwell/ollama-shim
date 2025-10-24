import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if present
script_dir = Path(__file__).parent
dotenv_path = script_dir / '.env'
print(f"--- Looking for .env file at: {dotenv_path} ---")
if dotenv_path.exists():
    print("--- .env file found. Content: ---")
    with open(dotenv_path, "r") as f:
        print(f.read())
    print("--- End of .env file content ---")
    load_dotenv(dotenv_path=dotenv_path, override=True)
    if "LM_STUDIO_BASE_URL" in os.environ:
        print("--- LM_STUDIO_BASE_URL found in environment. ---")
    else:
        print("--- LM_STUDIO_BASE_URL not found in environment after loading .env file. ---")
else:
    print("--- .env file not found. ---")

# --- CONFIGURATION ---
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234")
PRIMARY_MODEL_URL = f"{LM_STUDIO_BASE_URL.rstrip('/')}/v1/chat/completions"
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "30.0"))
RESPONSE_TIMEOUT = float(os.getenv("RESPONSE_TIMEOUT", "300.0"))

print(f"--- Using LM Studio Base URL: {LM_STUDIO_BASE_URL} ---")
print(f"--- Primary Model URL: {PRIMARY_MODEL_URL} ---")
