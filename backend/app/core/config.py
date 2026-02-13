from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Database Settings
    USE_SQLITE: bool = False
    DATABASE_URL: str = "postgresql://commander:commander@localhost:5432/commander"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Scryfall API
    SCRYFALL_API_URL: str = "https://api.scryfall.com"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MTG Commander Online"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
