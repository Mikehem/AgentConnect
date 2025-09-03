"""Authentication and authorization services."""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    org_id: str
    email: str
    roles: List[str]
    exp: datetime


class AuthService:
    """Authentication service for OIDC and JWT token management."""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = user_data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("user_id")
            org_id: str = payload.get("org_id")
            email: str = payload.get("email")
            roles: List[str] = payload.get("roles", [])
            exp: datetime = payload.get("exp")
            
            if user_id is None or org_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return TokenData(
                user_id=user_id,
                org_id=org_id,
                email=email,
                roles=roles,
                exp=exp
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def validate_api_key(self, api_key: str, required_scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate API key and return user data."""
        # In a real implementation, this would check against a database
        # For now, we'll use a simple validation
        if not api_key or len(api_key) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Mock user data for testing
        user_data = {
            "user_id": "api-user-123",
            "org_id": "org-123",
            "email": "api@example.com",
            "roles": ["api_user"],
            "scopes": required_scopes or []
        }
        
        return user_data
    
    def check_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user has required permission."""
        # Simple role-based permission check
        if "admin" in user_roles:
            return True
        
        permission_map = {
            "mcp:servers:create": ["admin", "engineer"],
            "mcp:servers:read": ["admin", "engineer", "viewer"],
            "mcp:servers:update": ["admin", "engineer"],
            "mcp:servers:delete": ["admin"],
            "organizations:manage": ["admin"],
            "capabilities:discover": ["admin", "engineer", "viewer"],
            "health:monitor": ["admin", "engineer"]
        }
        
        allowed_roles = permission_map.get(required_permission, [])
        return any(role in user_roles for role in allowed_roles)
    
    def create_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user session."""
        session_id = f"session_{user_data['user_id']}_{datetime.now().timestamp()}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_data["user_id"],
            "org_id": user_data["org_id"],
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=8)
        }
        
        logger.info(f"Session created for user {user_data['user_id']}")
        return session_data
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate user session."""
        # In a real implementation, this would check against a session store
        if not session_id or not session_id.startswith("session_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        # Mock session validation
        return {
            "session_id": session_id,
            "user_id": "user-123",
            "org_id": "org-123",
            "valid": True
        }
    
    def logout_session(self, session_id: str) -> bool:
        """Logout user session."""
        logger.info(f"Session {session_id} logged out")
        return True


# Global auth service instance
auth_service = AuthService()
