"""Configuration management with security best practices."""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and security."""
    
    # Telegram Configuration
    telegram_bot_token: str = Field(..., min_length=10)
    telegram_group_ids: str = Field(..., description="Comma-separated group IDs")
    
    # Database Configuration
    database_url: str = Field(..., pattern=r"^postgresql://.*")
    db_password: str = Field(..., min_length=8)
    
    # Brand Detection
    brand_keywords: str = Field(default="visa,mastercard,paypal,stripe")
    
    # Monitoring Configuration
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    rate_limit_requests: int = Field(default=100, gt=0)
    rate_limit_window: int = Field(default=3600, gt=0)
    
    # OCR Configuration
    ocr_languages: str = Field(default="eng")
    ocr_confidence_threshold: int = Field(default=60, ge=0, le=100)
    
    model_config = {
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    @field_validator("telegram_group_ids")
    @classmethod
    def validate_group_ids(cls, v):
        """Validate telegram group IDs format."""
        if not v:
            raise ValueError("At least one group ID must be provided")
        
        ids = [id_.strip() for id_ in v.split(",")]
        for id_ in ids:
            if not id_.startswith("-"):
                raise ValueError(f"Invalid group ID format: {id_}")
        return v
    
    @property
    def telegram_groups(self) -> List[int]:
        """Get telegram group IDs as integers."""
        return [int(id_.strip()) for id_ in self.telegram_group_ids.split(",")]
    
    @property
    def keywords_list(self) -> List[str]:
        """Get brand keywords as list."""
        return [kw.strip().lower() for kw in self.brand_keywords.split(",")]


# Global settings instance
settings = Settings()

