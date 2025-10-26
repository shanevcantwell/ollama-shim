# src/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Loads configuration from environment variables and .env file.
    Pydantic will automatically find the .env file in the
    current working directory, which run.bat sets to the project root.
    """
    model_config = SettingsConfigDict(
        env_file='.env', # Look for .env in the CWD
        env_file_encoding='utf-8', 
        extra='ignore'
    )

    # This will read LM_STUDIO_BASE_URL from your root .env
    LM_STUDIO_BASE_URL: str = "http://127.0.0.1:1234"
    
    LOG_LEVEL: str = "INFO"

# Create a single settings instance for the app to import
settings = Settings()