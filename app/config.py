from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database Configuration
    database_url: str
    sync_database_url: str
    
    # Application Configuration
    app_name: str = "Hotel Receptionist API"
    app_version: str = "0.0.1"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # Gemini AI Configuration
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 