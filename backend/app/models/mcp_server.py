"""MCP Server model for server registration and management."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class McpServer(Base):
    """MCP Server model for server registration and management."""
    
    __tablename__ = "mcp_servers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String(50), nullable=False)  # development, staging, production
    base_url = Column(String(500), nullable=False)
    ws_url = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    server_metadata = Column(JSON, nullable=False, default=dict)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    policy_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default="pending_discovery")
    health_status = Column(String(20), nullable=False, default="unknown")
    last_health_check_at = Column(DateTime, nullable=True)
    last_discovery_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="mcp_servers")
    owner = relationship("User", back_populates="mcp_servers")
    credentials = relationship("McpCredential", back_populates="server", cascade="all, delete-orphan")
    capabilities = relationship("McpCapability", back_populates="server", cascade="all, delete-orphan")
    health_checks = relationship("McpHealthCheck", back_populates="server", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<McpServer(id={self.id}, name='{self.name}', environment='{self.environment}')>"


class McpCredential(Base):
    """MCP Server credentials stored as Vault references."""
    
    __tablename__ = "mcp_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mcp_server_id = Column(UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False)
    credential_type = Column(String(50), nullable=False)  # bearer_token, oauth2, api_key, mtls, basic_auth
    vault_path = Column(String(500), nullable=False)
    scope = Column(JSON, nullable=False, default=list)
    credential_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    rotated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    server = relationship("McpServer", back_populates="credentials")
    
    def __repr__(self) -> str:
        return f"<McpCredential(id={self.id}, type='{self.credential_type}', server_id={self.mcp_server_id})>"


class McpCapability(Base):
    """MCP Server capabilities discovered from introspection."""
    
    __tablename__ = "mcp_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mcp_server_id = Column(UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)
    schema_json = Column(JSON, nullable=False)
    capability_metadata = Column(JSON, nullable=False, default=dict)
    enabled = Column(String(20), nullable=False, default=True)
    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    server = relationship("McpServer", back_populates="capabilities")
    
    def __repr__(self) -> str:
        return f"<McpCapability(id={self.id}, name='{self.name}', server_id={self.mcp_server_id})>"


class McpHealthCheck(Base):
    """MCP Server health check results."""
    
    __tablename__ = "mcp_health_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mcp_server_id = Column(UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False)
    status = Column(String(20), nullable=False)  # healthy, unhealthy, timeout, error
    response_time_ms = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    check_details = Column(JSON, nullable=False, default=dict)
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    server = relationship("McpServer", back_populates="health_checks")
    
    def __repr__(self) -> str:
        return f"<McpHealthCheck(id={self.id}, status='{self.status}', server_id={self.mcp_server_id})>"
