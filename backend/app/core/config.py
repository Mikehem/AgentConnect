"""Application configuration and settings."""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.types import SecretStr


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "SprintConnect"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    ENVIRONMENT: str = Field(default="development")

    # OAuth 2.1 / OIDC - Logto Cloud Configuration
    LOGTO_ENDPOINT: str = Field(default="https://your-tenant.logto.app", description="Logto Cloud endpoint")
    LOGTO_APP_ID: str = Field(default="", description="Logto application ID")
    LOGTO_APP_SECRET: SecretStr = Field(default=SecretStr(""), description="Logto application secret")
    
    # Derived OIDC settings from Logto
    @property
    def OIDC_ISSUER(self) -> str:
        """Get OIDC issuer from Logto endpoint."""
        return self.LOGTO_ENDPOINT
    
    @property
    def OIDC_AUDIENCE(self) -> str:
        """Get OIDC audience from Logto app ID."""
        return self.LOGTO_APP_ID
    
    @property
    def OIDC_JWKS_URL(self) -> str:
        """Get JWKS URL from Logto endpoint."""
        return f"{self.LOGTO_ENDPOINT}/oidc/jwks"
    
    ALLOWED_JWT_ALGS: str = Field(default="RS256,ES256")
    JWKS_CACHE_TTL_SECONDS: int = Field(default=300)
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./test.db")
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = Field(default=10)
    
    # Security
    SECRET_KEY: SecretStr = Field(default="dev-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # OIDC Configuration
    OIDC_CLIENT_ID: Optional[str] = Field(default=None)
    OIDC_CLIENT_SECRET: Optional[SecretStr] = Field(default=None)
    OIDC_DISCOVERY_URL: Optional[str] = Field(default=None)
    
    # API Configuration
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "SprintConnect API"
    
    # CORS
    BACKEND_CORS_ORIGINS: str = Field(default="http://localhost:3000")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST_SIZE: int = Field(default=100)
    
    # MCP Server Configuration
    ALLOWED_EGRESS_HOSTS: str = Field(
        default="api.openai.com,api.anthropic.com"
    )
    MCP_SERVER_TIMEOUT_SECONDS: int = Field(default=30)
    
    # Organization Quotas
    DEFAULT_ORG_SERVER_LIMIT: int = Field(default=50)
    
    # Auto Discovery
    AUTO_DISCOVER_ENABLED: bool = Field(default=True)
    
    # Monitoring
    PROMETHEUS_METRICS_PORT: int = Field(default=9090)
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string to list."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("ALLOWED_EGRESS_HOSTS", mode="after")
    @classmethod
    def assemble_egress_hosts(cls, v):
        """Parse egress hosts from string to list."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("ALLOWED_JWT_ALGS", mode="after")
    @classmethod
    def assemble_jwt_algs(cls, v):
        """Parse JWT algorithms from string to list."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


# Global settings instance
settings = Settings()
