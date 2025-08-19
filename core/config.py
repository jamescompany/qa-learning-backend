from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os

class Settings(BaseSettings):
    APP_NAME: str = "QA Learning Web"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # CORS_ORIGINS as a simple string field that gets parsed in validator
    CORS_ORIGINS: str | List[str] = Field(
        default="http://localhost:3000,http://localhost:5173",
        env="CORS_ORIGINS"
    )
    
    @validator("CORS_ORIGINS", pre=False)
    def assemble_cors_origins(cls, v):
        if v is None:
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["http://localhost:3000", "http://localhost:5173"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:5173"]
    
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM: Optional[str] = Field(default=None, env="SMTP_FROM")
    
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    # ALLOWED_EXTENSIONS as a simple string field that gets parsed in validator
    ALLOWED_EXTENSIONS: str | List[str] = Field(
        default="jpg,jpeg,png,gif,pdf,doc,docx",
        env="ALLOWED_EXTENSIONS"
    )
    
    @validator("ALLOWED_EXTENSIONS", pre=False)
    def assemble_allowed_extensions(cls, v):
        if v is None:
            return ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]
    
    JWT_SECRET_KEY: Optional[str] = Field(default=None, env="JWT_SECRET_KEY")
    
    @validator("JWT_SECRET_KEY", pre=True, always=True)
    def set_jwt_secret(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v
        return values.get("SECRET_KEY", "")
    
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    PAGINATION_DEFAULT_LIMIT: int = 20
    PAGINATION_MAX_LIMIT: int = 100
    
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()