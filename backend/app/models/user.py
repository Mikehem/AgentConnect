"""User model for authentication and authorization."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    oidc_subject = Column(String(255), nullable=True)
    roles = Column(JSON, nullable=False, default=list)
    settings = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="active")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    mcp_servers = relationship("McpServer", back_populates="owner")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', org_id={self.org_id})>"
