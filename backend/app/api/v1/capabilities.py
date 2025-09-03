"""Capabilities API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.services.capabilities import CapabilitiesService
from app.core.database import get_db
from app.core.logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


# Temporary mock for authentication - replace with proper auth
def get_current_user() -> Any:
    """Temporary mock for current user."""
    from app.models.user import User
    import uuid
    
    user = User(
        id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        roles=["admin"],
        status="active"
    )
    
    return user


@router.post("/discover/{server_id}")
async def discover_capabilities(
    server_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discover capabilities for an MCP server."""
    try:
        service = CapabilitiesService(db)
        result = await service.discover_capabilities(server_id, current_user)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discover capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover capabilities"
        )


@router.post("/validate")
async def validate_capability_schema(
    capability_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate capability schema."""
    try:
        service = CapabilitiesService(db)
        is_valid = service.validate_capability_schema(capability_data)
        
        if is_valid:
            return {"valid": True, "message": "Capability schema is valid"}
        else:
            return {"valid": False, "message": "Invalid capability schema"}
    except Exception as e:
        logger.error(f"Failed to validate capability schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate capability schema"
        )


@router.post("/test/{capability_id}")
async def test_capability(
    capability_id: str,
    test_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test a specific capability."""
    try:
        service = CapabilitiesService(db)
        result = await service.test_capability(capability_id, test_data)
        return result
    except Exception as e:
        logger.error(f"Failed to test capability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test capability"
        )


@router.get("/servers/{server_id}")
async def list_server_capabilities(
    server_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all capabilities for a server."""
    try:
        service = CapabilitiesService(db)
        capabilities = service.list_server_capabilities(server_id, current_user)
        return {"capabilities": capabilities}
    except Exception as e:
        logger.error(f"Failed to list server capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list server capabilities"
        )


@router.get("/{capability_id}")
async def get_capability_details(
    capability_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a capability."""
    try:
        service = CapabilitiesService(db)
        details = service.get_capability_details(capability_id, current_user)
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get capability details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capability details"
        )


@router.patch("/{capability_id}/metadata")
async def update_capability_metadata(
    capability_id: str,
    metadata: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update capability metadata."""
    try:
        service = CapabilitiesService(db)
        result = service.update_capability_metadata(capability_id, metadata, current_user)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update capability metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update capability metadata"
        )


@router.get("/{capability_id}/stats")
async def get_capability_usage_stats(
    capability_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a capability."""
    try:
        service = CapabilitiesService(db)
        stats = service.get_capability_usage_stats(capability_id, current_user)
        return stats
    except Exception as e:
        logger.error(f"Failed to get capability usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capability usage stats"
        )


@router.get("/{capability_id}/timeline")
async def get_capability_usage_timeline(
    capability_id: str,
    days: int = 30,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage timeline for a capability."""
    try:
        service = CapabilitiesService(db)
        timeline = service.get_capability_usage_timeline(capability_id, days, current_user)
        return {"timeline": timeline}
    except Exception as e:
        logger.error(f"Failed to get capability usage timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capability usage timeline"
        )


@router.get("/{capability_id}/errors")
async def get_capability_error_logs(
    capability_id: str,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get error logs for a capability."""
    try:
        service = CapabilitiesService(db)
        logs = service.get_capability_error_logs(capability_id, limit, current_user)
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Failed to get capability error logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capability error logs"
        )
