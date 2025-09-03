"""Health monitoring API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.services.health import HealthService, HealthConfig, HealthAlert, NotificationChannel
from app.core.database import get_db
from app.core.logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


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


@router.post("/servers/{server_id}/check")
async def manual_health_check(
    server_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform manual health check on a server."""
    try:
        service = HealthService(db)
        result = await service.perform_health_check(server_id, current_user)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform health check"
        )


@router.get("/servers/{server_id}/status")
async def get_server_health_status(
    server_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current health status of a server."""
    try:
        service = HealthService(db)
        status = service.get_server_health_status(server_id, current_user)
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get server health status"
        )


@router.patch("/servers/{server_id}/config")
async def update_health_config(
    server_id: str,
    config: HealthConfig,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update health check configuration for a server."""
    try:
        service = HealthService(db)
        result = service.update_health_config(server_id, config, current_user)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update health config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update health config"
        )


@router.get("/servers/{server_id}/config")
async def get_health_config(
    server_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health check configuration for a server."""
    try:
        service = HealthService(db)
        config = service.get_health_config(server_id, current_user)
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health config"
        )


@router.get("/servers/{server_id}/history")
async def get_health_history(
    server_id: str,
    days: int = 7,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health check history for a server."""
    try:
        service = HealthService(db)
        history = service.get_health_history(server_id, days, current_user)
        return {"history": history}
    except Exception as e:
        logger.error(f"Failed to get health history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health history"
        )


@router.get("/alerts")
async def get_health_alerts(
    server_id: Optional[str] = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health alerts."""
    try:
        service = HealthService(db)
        alerts = service.get_health_alerts(server_id, current_user)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Failed to get health alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health alerts"
        )


@router.post("/alerts")
async def create_health_alert(
    server_id: str,
    alert_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health alert."""
    try:
        service = HealthService(db)
        alert = service.create_health_alert(server_id, alert_data, current_user)
        return alert
    except Exception as e:
        logger.error(f"Failed to create health alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health alert"
        )


@router.patch("/alerts/{alert_id}")
async def update_health_alert(
    alert_id: str,
    update_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health alert."""
    try:
        service = HealthService(db)
        result = service.update_health_alert(alert_id, update_data, current_user)
        return result
    except Exception as e:
        logger.error(f"Failed to update health alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update health alert"
        )


@router.delete("/alerts/{alert_id}")
async def delete_health_alert(
    alert_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health alert."""
    try:
        service = HealthService(db)
        result = service.delete_health_alert(alert_id, current_user)
        return result
    except Exception as e:
        logger.error(f"Failed to delete health alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete health alert"
        )


@router.get("/servers/{server_id}/metrics")
async def get_health_metrics(
    server_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health metrics for a server."""
    try:
        service = HealthService(db)
        metrics = service.get_health_metrics(server_id, current_user)
        return {"metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health metrics"
        )


@router.get("/servers/{server_id}/metrics/timeline")
async def get_health_metrics_timeline(
    server_id: str,
    hours: int = 24,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health metrics timeline."""
    try:
        service = HealthService(db)
        timeline = service.get_health_metrics_timeline(server_id, hours, current_user)
        return {"timeline": timeline}
    except Exception as e:
        logger.error(f"Failed to get health metrics timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health metrics timeline"
        )


@router.get("/summary")
async def get_health_summary(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall health summary."""
    try:
        service = HealthService(db)
        summary = service.get_health_summary(current_user)
        return summary
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get health summary"
        )


@router.get("/notifications/channels")
async def get_notification_channels(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification channels."""
    try:
        service = HealthService(db)
        channels = service.get_notification_channels(current_user)
        return {"channels": channels}
    except Exception as e:
        logger.error(f"Failed to get notification channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification channels"
        )


@router.post("/notifications/channels")
async def create_notification_channel(
    channel_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification channel."""
    try:
        service = HealthService(db)
        channel = service.create_notification_channel(channel_data, current_user)
        return channel
    except Exception as e:
        logger.error(f"Failed to create notification channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification channel"
        )


@router.post("/notifications/channels/{channel_id}/test")
async def test_notification_channel(
    channel_id: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test a notification channel."""
    try:
        service = HealthService(db)
        result = service.test_notification_channel(channel_id, current_user)
        return result
    except Exception as e:
        logger.error(f"Failed to test notification channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test notification channel"
        )
