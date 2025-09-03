"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse, Response
from typing import Optional

from app.services.auth import auth_service
from app.services.logto_service import logto_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def oidc_login_redirect():
    """Redirect to OIDC provider for authentication."""
    # Mock OIDC redirect
    return RedirectResponse(url="https://auth.example.com/login?redirect_uri=/auth/callback")


@router.get("/oidc/login")
async def oidc_login_redirect_specific():
    """Redirect to Logto Cloud for authentication."""
    try:
        redirect_uri = "http://localhost:8000/v1/auth/oidc/callback"
        sign_in_url = await logto_service.get_sign_in_url(redirect_uri)
        return RedirectResponse(url=sign_in_url, status_code=302)
    except Exception as e:
        logger.error(f"Failed to get sign-in URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate authentication"
        )


@router.post("/login")
async def login(request: Request):
    """Login with email and password."""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )
    
    # Mock authentication
    if email == "test@example.com" and password == "password":
        user_data = {
            "user_id": "user-123",
            "org_id": "org-123",
            "email": email,
            "roles": ["admin"]
        }
        
        access_token = auth_service.create_access_token(user_data)
        session_data = auth_service.create_session(user_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "session_id": session_data.get("session_id"),
            "user": user_data
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.get("/callback")
async def oidc_callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle OIDC callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC authentication failed: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    # Mock token exchange
    user_data = {
        "user_id": "user-123",
        "org_id": "org-123",
        "email": "user@example.com",
        "roles": ["admin"]
    }
    
    access_token = auth_service.create_access_token(user_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/oidc/callback")
async def oidc_callback_specific(code: Optional[str] = None, error: Optional[str] = None):
    """Handle Logto OIDC callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC authentication failed: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # Handle callback with Logto
        redirect_uri = "http://localhost:8000/v1/auth/oidc/callback"
        token_data = await logto_service.handle_callback(code, redirect_uri)
        
        # Extract user information
        user_info = token_data.get("user_info", {})
        user_data = {
            "user_id": user_info.get("sub", "unknown"),
            "org_id": user_info.get("org_id", "default-org"),
            "email": user_info.get("email", ""),
            "name": user_info.get("name", ""),
            "roles": user_info.get("roles", ["user"])
        }
        
        return {
            "access_token": token_data.get("access_token"),
            "id_token": token_data.get("id_token"),
            "token_type": "bearer",
            "user": user_data,
            "expires_in": token_data.get("expires_in", 3600)
        }
    except Exception as e:
        logger.error(f"OIDC callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout():
    """Logout user session."""
    return {"message": "Logged out successfully"}


@router.post("/oidc/logout")
async def oidc_logout():
    """Logto OIDC logout endpoint."""
    try:
        post_logout_redirect_uri = "http://localhost:8000/"
        sign_out_url = await logto_service.get_sign_out_url(post_logout_redirect_uri)
        return {"logout_url": sign_out_url, "message": "Redirect to logout URL"}
    except Exception as e:
        logger.error(f"Failed to get sign-out URL: {e}")
        return {"message": "Logged out successfully"}


@router.post("/validate")
async def validate_jwt_token(request: Request):
    """Validate JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    try:
        token_data = auth_service.verify_token(token)
        return {"valid": True, "user": token_data.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


@router.post("/api-key/validate")
async def validate_api_key(request: Request):
    """Validate API key."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    try:
        user_data = auth_service.validate_api_key(api_key)
        return {"valid": True, "user": user_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key validation failed"
        )


@router.post("/permissions/check")
async def check_permission(request: Request):
    """Check user permission."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    token = auth_header.split(" ")[1]
    try:
        token_data = auth_service.verify_token(token)
        
        # Get permission from request body
        body = await request.json()
        required_permission = body.get("permission")
        
        if not required_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission required"
            )
        
        has_permission = auth_service.check_permission(
            token_data.roles, 
            required_permission
        )
        
        return {
            "has_permission": has_permission,
            "user_roles": token_data.roles,
            "required_permission": required_permission
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission check failed"
        )


@router.post("/sessions")
async def create_session(request: Request):
    """Create user session."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    token = auth_header.split(" ")[1]
    try:
        token_data = auth_service.verify_token(token)
        user_data = token_data.model_dump()
        session = auth_service.create_session(user_data)
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session creation failed"
        )


@router.get("/sessions/{session_id}")
async def validate_session(session_id: str):
    """Validate user session."""
    try:
        session_data = auth_service.validate_session(session_id)
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session validation failed"
        )


@router.delete("/sessions/{session_id}")
async def logout_session(session_id: str):
    """Logout user session."""
    try:
        success = auth_service.logout_session(session_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session logout failed"
        )
