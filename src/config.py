# src/config.py
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
import logging

class Settings(BaseSettings):
    """
    Configuration settings for the Ollama Shim service.

    Settings are loaded from environment variables. A .env file in the root
    directory can be used for local development.
    """
    # --- LM Studio Connection ---
    # The base URL for the LM Studio instance.
    LM_STUDIO_BASE_URL: str = Field(default="http://localhost:1234", validation_alias=AliasChoices("lm_studio_url", "lm_studio_base_url"))
    AUTH_TOKEN: str | None = None

    # --- Timeouts ---
    API_TIMEOUT: float = 30.0
    RESPONSE_TIMEOUT: float = 300.0

    # --- Server Settings ---
    SHIM_PORT: int

    # --- Logging ---
    # To see the full request and response payloads, set this to DEBUG.
    # Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = "INFO"
    FILE_LOG_LEVEL: str = "INFO" # Adding this to handle the user's .env

    class Config:
        # The name of the .env file to load.
        env_file = ".env"
        # All environment variables are case-insensitive.
        case_sensitive = False

# Instantiate the settings object that will be used throughout the application.
settings = Settings()

# --- Logger Configuration ---
#
# We configure a logger here to be used across the application.
# The logger's level is set based on the LOG_LEVEL environment variable.
#
# To see the full request and response payloads being sent and received,
# set the LOG_LEVEL environment variable to "DEBUG" in your .env file.
#
# Example .env file:
#
# # .env
# LOG_LEVEL=DEBUG
#

# Get the logger for the application.
# We use "uvicorn.error" to tie into the existing FastAPI/Uvicorn logging.
logger = logging.getLogger("uvicorn.error")

# Set the logger's level based on the settings.
# The level name is converted to upper case to be safe.
logger.setLevel(settings.LOG_LEVEL.upper())
