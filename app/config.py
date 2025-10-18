import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT Authentication
    SECRET_KEY: str = "jwt-key"
    TOKEN_EXPIRE_MINUTES: int = 30
    
    # Higgsfield AI
    HIGGSFIELD_API_KEY: Optional[str] = None
    HIGGSFIELD_API_SECRET: Optional[str] = None
    HIGGSFIELD_BASE_URL: str = "https://platform.higgsfield.ai/v1"
    
    # File Upload
    TEMP_UPLOAD_DIR: str = "./temp_uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: str = "png,jpg,jpeg,webp"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

