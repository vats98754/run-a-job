"""Configuration management for run_a_job."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Browser settings
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    browser_viewport_width: int = Field(default=1920, env="BROWSER_VIEWPORT_WIDTH")
    browser_viewport_height: int = Field(default=1080, env="BROWSER_VIEWPORT_HEIGHT")
    browser_user_agent: Optional[str] = Field(default=None, env="BROWSER_USER_AGENT")
    
    # CAPTCHA services
    twocaptcha_api_key: Optional[str] = Field(default=None, env="TWOCAPTCHA_API_KEY")
    anticaptcha_api_key: Optional[str] = Field(default=None, env="ANTICAPTCHA_API_KEY")
    
    # LLM integration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///jobs.db", env="DATABASE_URL")
    
    # Redis for background tasks
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Security
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    allowed_hosts: list[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Job execution limits
    max_concurrent_jobs: int = Field(default=10, env="MAX_CONCURRENT_JOBS")
    job_timeout: int = Field(default=3600, env="JOB_TIMEOUT")  # 1 hour default
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()