"""Organization Pydantic schemas."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=1, max_length=100, description="Organization slug")
    subscription_tier: str = Field(default="free", description="Subscription tier")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate organization slug format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, description="Organization slug")
    subscription_tier: Optional[str] = Field(None, description="Subscription tier")
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate organization slug format."""
        if v is not None:
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
            return v.lower()
        return v


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    
    id: UUID = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    slug: str = Field(..., description="Organization slug")
    subscription_tier: str = Field(..., description="Subscription tier")
    status: str = Field(..., description="Organization status")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseModel):
    """Schema for organization list response."""
    
    organizations: List[OrganizationResponse] = Field(..., description="List of organizations")
    total: int = Field(..., description="Total number of organizations")
    limit: int = Field(..., description="Number of records returned")
    offset: int = Field(..., description="Number of records skipped")
    has_more: bool = Field(..., description="Whether there are more records")


class OrganizationQuotas(BaseModel):
    """Schema for organization quotas."""
    
    server_limit: int = Field(..., ge=1, description="Maximum number of servers")
    user_limit: int = Field(..., ge=1, description="Maximum number of users")
    storage_limit_gb: int = Field(..., ge=1, description="Storage limit in GB")
    api_rate_limit: int = Field(..., ge=1, description="API rate limit per hour")
    current_servers: int = Field(default=0, ge=0, description="Current number of servers")
    current_users: int = Field(default=0, ge=0, description="Current number of users")


class OrganizationSettings(BaseModel):
    """Schema for organization settings."""
    
    settings: Dict[str, Any] = Field(default_factory=dict, description="Organization settings")
    
    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings structure."""
        if not isinstance(v, dict):
            raise ValueError("Settings must be a dictionary")
        return v
