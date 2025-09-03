"""Pydantic schemas for MCP server API validation."""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, HttpUrl
from enum import Enum


class Environment(str, Enum):
    """MCP server environment options."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class CredentialType(str, Enum):
    """MCP server credential types."""
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    MTLS = "mtls"
    BASIC_AUTH = "basic_auth"


class ServerStatus(str, Enum):
    """MCP server status options."""
    PENDING_DISCOVERY = "pending_discovery"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DELETED = "deleted"
    MAINTENANCE = "maintenance"


class HealthStatus(str, Enum):
    """MCP server health status options."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AuthConfig(BaseModel):
    """Authentication configuration for MCP server."""
    
    type: CredentialType = Field(..., description="Type of authentication")
    vault_path: str = Field(..., min_length=1, max_length=500, description="Vault path for credentials")
    header_name: Optional[str] = Field(None, description="Custom header name for API key authentication")
    
    @field_validator('vault_path')
    @classmethod
    def validate_vault_path(cls, v: str) -> str:
        """Validate vault path format."""
        if not re.match(r'^[a-zA-Z0-9\-_/]+$', v):
            raise ValueError("Vault path must contain only alphanumeric characters, hyphens, underscores, and forward slashes")
        return v


class HealthCheckConfig(BaseModel):
    """Health check configuration for MCP server."""
    
    enabled: bool = Field(default=True, description="Enable health checks")
    interval_seconds: int = Field(default=300, ge=30, le=3600, description="Health check interval in seconds")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="Health check timeout in seconds")
    failure_threshold: int = Field(default=3, ge=1, le=10, description="Number of failures before marking unhealthy")
    endpoint: str = Field(default="/health", description="Health check endpoint path")


class McpServerCreate(BaseModel):
    """Schema for creating a new MCP server."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Server name")
    description: Optional[str] = Field(None, max_length=1000, description="Server description")
    environment: Environment = Field(..., description="Deployment environment")
    base_url: str = Field(..., description="MCP server HTTP endpoint")
    ws_url: Optional[str] = Field(None, description="MCP server WebSocket endpoint")
    tags: List[str] = Field(default_factory=list, max_length=20, description="Server tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    auth_config: Optional[AuthConfig] = Field(None, description="Authentication configuration")
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig, description="Health check configuration")
    auto_discover: bool = Field(default=True, description="Enable automatic capability discovery")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate server name format."""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError("Server name must contain only alphanumeric characters, hyphens, and underscores")
        return v
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format and security."""
        if not re.match(r'^https?://', v):
            raise ValueError("Base URL must start with http:// or https://")
        
        # Additional SSRF protection will be implemented in the service layer
        return v
    
    @field_validator('ws_url')
    @classmethod
    def validate_ws_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate WebSocket URL format."""
        if v is not None:
            if not re.match(r'^wss?://', v):
                raise ValueError("WebSocket URL must start with ws:// or wss://")
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags list."""
        for tag in v:
            if not re.match(r'^[a-zA-Z0-9\-_]+$', tag):
                raise ValueError("Tags must contain only alphanumeric characters, hyphens, and underscores")
        return [tag.lower() for tag in v]
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata size limit."""
        import json
        if len(json.dumps(v)) > 65536:  # 64KB limit
            raise ValueError("Metadata size exceeds 64KB limit")
        return v


class McpServerUpdate(BaseModel):
    """Schema for updating an MCP server."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Server name")
    description: Optional[str] = Field(None, max_length=1000, description="Server description")
    environment: Optional[Environment] = Field(None, description="Deployment environment")
    base_url: Optional[str] = Field(None, description="MCP server HTTP endpoint")
    ws_url: Optional[str] = Field(None, description="MCP server WebSocket endpoint")
    tags: Optional[List[str]] = Field(None, max_length=20, description="Server tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    auth_config: Optional[AuthConfig] = Field(None, description="Authentication configuration")
    health_check: Optional[HealthCheckConfig] = Field(None, description="Health check configuration")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate server name format."""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
                raise ValueError("Server name must contain only alphanumeric characters, hyphens, and underscores")
        return v
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate base URL format."""
        if v is not None:
            if not re.match(r'^https?://', v):
                raise ValueError("Base URL must start with http:// or https://")
        return v
    
    @field_validator('ws_url')
    @classmethod
    def validate_ws_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate WebSocket URL format."""
        if v is not None:
            if not re.match(r'^wss?://', v):
                raise ValueError("WebSocket URL must start with ws:// or wss://")
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags list."""
        if v is not None:
            for tag in v:
                if not re.match(r'^[a-zA-Z0-9\-_]+$', tag):
                    raise ValueError("Tags must contain only alphanumeric characters, hyphens, and underscores")
            return [tag.lower() for tag in v]
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate metadata size limit."""
        if v is not None:
            import json
            if len(json.dumps(v)) > 65536:  # 64KB limit
                raise ValueError("Metadata size exceeds 64KB limit")
        return v


class McpServerResponse(BaseModel):
    """Schema for MCP server response."""
    
    id: str
    name: str
    description: Optional[str]
    environment: Environment
    base_url: str
    ws_url: Optional[str]
    tags: List[str]
    server_metadata: Dict[str, Any]
    status: ServerStatus
    health_status: HealthStatus
    owner_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_health_check_at: Optional[datetime]
    last_discovery_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class McpServerListResponse(BaseModel):
    """Schema for MCP server list response with pagination."""
    
    servers: List[McpServerResponse]
    total: int
    limit: int = 10
    offset: int = 0
    has_more: bool = False
    # Compatibility fields
    page: Optional[int] = None
    size: Optional[int] = None
    pages: Optional[int] = None


class McpServerCreateResponse(BaseModel):
    """Schema for MCP server creation response."""
    
    id: UUID
    name: str
    base_url: str
    environment: Environment
    status: ServerStatus
    created_at: datetime
    discovery_job_id: Optional[str] = None
    
    model_config = {"from_attributes": True}


class McpServerDeleteResponse(BaseModel):
    """Schema for MCP server deletion response."""
    
    message: str
    deleted_at: datetime
    cleanup_job_id: Optional[str] = None
