"""Security utilities for SSRF protection, URL validation, and authentication."""

import ipaddress
import re
import socket
import jwt
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timezone
import httpx
from fastapi import HTTPException, status

from app.core.config import settings
import time
import json
import urllib.request
from functools import lru_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


class SSRFProtectionError(Exception):
    """Exception raised when SSRF protection blocks a request."""
    pass


def validate_url_security(url: str, allowed_hosts: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate URL for SSRF protection.
    
    Args:
        url: URL to validate
        allowed_hosts: List of allowed hosts (defaults to settings.ALLOWED_EGRESS_HOSTS)
    
    Returns:
        Tuple of (is_allowed, reason)
    """
    if allowed_hosts is None:
        allowed_hosts = settings.ALLOWED_EGRESS_HOSTS
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ['http', 'https', 'ws', 'wss']:
            return False, f"Invalid scheme: {parsed.scheme}"
        
        # Check for required HTTPS/WSS in production
        if settings.ENVIRONMENT == "production" and parsed.scheme in ['http', 'ws']:
            return False, "HTTP/WS not allowed in production environment"
        
        # Extract hostname
        hostname = parsed.hostname
        if not hostname:
            return False, "No hostname found in URL"
        
        # Check against allowed hosts
        if hostname in allowed_hosts:
            return True, "Hostname in allowed list"
        
        # Check for IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            
            # Block private IP ranges
            if ip.is_private:
                return False, f"Private IP address not allowed: {hostname}"
            
            # Block link-local addresses
            if ip.is_link_local:
                return False, f"Link-local IP address not allowed: {hostname}"
            
            # Block multicast addresses
            if ip.is_multicast:
                return False, f"Multicast IP address not allowed: {hostname}"
            
            # Block loopback addresses
            if ip.is_loopback:
                return False, f"Loopback IP address not allowed: {hostname}"
            
            # Block reserved addresses
            if ip.is_reserved:
                return False, f"Reserved IP address not allowed: {hostname}"
            
            # For production, require explicit allowlist for IP addresses
            if settings.ENVIRONMENT == "production":
                return False, f"IP address not in allowed list: {hostname}"
            
            return True, "IP address allowed in non-production environment"
            
        except ValueError:
            # Not an IP address, check if it's a valid hostname
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', hostname):
                return False, f"Invalid hostname format: {hostname}"
            
            # Check for localhost variations
            if hostname.lower() in ['localhost', '127.0.0.1', '::1']:
                return False, f"Localhost not allowed: {hostname}"
            
            # Check for internal/private domains
            if any(domain in hostname.lower() for domain in ['.local', '.internal', '.home', '.lan']):
                return False, f"Internal domain not allowed: {hostname}"
            
            return False, f"Hostname not in allowed list: {hostname}"
    
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False, f"URL validation failed: {str(e)}"


def validate_mcp_server_url(url: str, environment: str) -> None:
    """
    Validate MCP server URL with SSRF protection.
    
    Args:
        url: URL to validate
        environment: Server environment (development, staging, production)
    
    Raises:
        SSRFProtectionError: If URL is not allowed
    """
    # Adjust allowed hosts based on environment
    allowed_hosts = settings.ALLOWED_EGRESS_HOSTS.copy()
    
    # Add environment-specific hosts
    if environment == "development":
        allowed_hosts.extend(["localhost", "127.0.0.1", "0.0.0.0"])
    elif environment == "staging":
        # Add staging-specific hosts if needed
        pass
    
    is_allowed, reason = validate_url_security(url, allowed_hosts)
    
    if not is_allowed:
        logger.warning(f"SSRF protection blocked URL: {url}, reason: {reason}")
        raise SSRFProtectionError(f"URL not allowed: {reason}")


def check_organization_quota(org_id: str, quota_type: str = "servers") -> bool:
    """
    Check if organization has quota available.
    
    Args:
        org_id: Organization ID
        quota_type: Type of quota to check
    
    Returns:
        True if quota available, False otherwise
    """
    # TODO: Implement actual quota checking logic
    # For now, return True (no quota enforcement)
    return True


def validate_vault_path(vault_path: str, org_id: str) -> bool:
    """
    Validate Vault path for organization scope.
    
    Args:
        vault_path: Vault path to validate
        org_id: Organization ID
    
    Returns:
        True if valid, False otherwise
    """
    # Ensure vault path is scoped to organization
    if not vault_path.startswith(f"mcp/{org_id}/"):
        return False
    
    # Validate path format
    if not re.match(r'^[a-zA-Z0-9\-_/]+$', vault_path):
        return False
    
    return True


def sanitize_metadata(metadata: dict) -> dict:
    """
    Sanitize metadata to remove sensitive information.
    
    Args:
        metadata: Raw metadata dictionary
    
    Returns:
        Sanitized metadata dictionary
    """
    sensitive_keys = ['password', 'secret', 'token', 'key', 'credential']
    sanitized = {}
    
    for key, value in metadata.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_metadata(value)
        else:
            sanitized[key] = value
    
    return sanitized


def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    import uuid
    return str(uuid.uuid4())


class JWKSCache:
    _cached_at: float = 0.0
    _jwks: dict[str, Any] | None = None

    @classmethod
    def get_keys(cls) -> dict[str, Any]:
        now = time.time()
        if cls._jwks and (now - cls._cached_at) < settings.JWKS_CACHE_TTL_SECONDS:
            return cls._jwks
        with urllib.request.urlopen(settings.OIDC_JWKS_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cls._jwks = data
            cls._cached_at = now
            return data


def _find_jwk(jwks: dict[str, Any], kid: str | None) -> dict[str, Any] | None:
    if not kid:
        return None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            return k
    return None


def verify_jwt_token_edge(token: str) -> Dict[str, Any]:
    """Strict JWT verification for AuthGateway.

    - Enforces issuer, audience, and allowed algorithms
    - Retrieves public keys from JWKS with caching
    """
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        alg = unverified.get("alg")
        if alg not in settings.ALLOWED_JWT_ALGS:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported token algorithm")

        jwks = JWKSCache.get_keys()
        jwk = _find_jwk(jwks, kid)
        if not jwk:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown key id")

        # PyJWT supports key objects via algorithms that accept JWK; use construct
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk)) if jwk.get("kty") == "RSA" else jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(jwk))

        payload = jwt.decode(
            token,
            public_key,
            algorithms=settings.ALLOWED_JWT_ALGS,
            audience=settings.OIDC_AUDIENCE,
            issuer=settings.OIDC_ISSUER,
            options={"require": ["exp", "iat", "nbf"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def log_security_event(event_type: str, details: dict, user_id: Optional[str] = None) -> None:
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        details: Event details
        user_id: User ID if applicable
    """
    logger.warning(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        details=details
    )


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return payload.
    
    Args:
        token: JWT token to verify
    
    Returns:
        Token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
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


def check_user_permission(user_roles: List[str], required_permission: str) -> bool:
    """
    Check if user has required permission based on roles.
    
    Args:
        user_roles: List of user roles
        required_permission: Required permission
    
    Returns:
        True if user has permission, False otherwise
    """
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


def validate_organization_access(user_org_id: str, target_org_id: str) -> bool:
    """
    Validate that user can access organization resources.
    
    Args:
        user_org_id: User's organization ID
        target_org_id: Target organization ID
    
    Returns:
        True if access is allowed, False otherwise
    """
    return user_org_id == target_org_id


def create_access_token(user_data: Dict[str, Any]) -> str:
    """
    Create JWT access token.
    
    Args:
        user_data: User data to encode in token
    
    Returns:
        JWT access token
    """
    from datetime import timedelta
    
    to_encode = user_data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(token: str) -> Dict[str, Any]:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        User data from token
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
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


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
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
