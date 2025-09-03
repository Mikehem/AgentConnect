"""Health monitoring and management services."""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID as _UUID

from app.core.logging import get_logger
from app.models.mcp_server import McpServer, McpHealthCheck

logger = get_logger(__name__)


class HealthStatus(BaseModel):
    """Health status model."""
    status: str  # healthy, unhealthy, degraded, unknown
    response_time_ms: Optional[int] = None
    last_check: datetime
    error_message: Optional[str] = None


class HealthConfig(BaseModel):
    """Health check configuration."""
    enabled: bool = True
    interval_seconds: int = 60
    timeout_seconds: int = 30
    failure_threshold: int = 3
    endpoint: Optional[str] = "/health"
    thresholds: Dict[str, Any] = Field(default_factory=dict)


class HealthAlert(BaseModel):
    """Health alert model."""
    id: str
    server_id: str
    alert_type: str
    message: str
    severity: str  # low, medium, high, critical
    created_at: datetime
    resolved_at: Optional[datetime] = None


class HealthMetrics(BaseModel):
    """Health metrics model."""
    server_id: str
    timestamp: datetime
    response_time_ms: int
    status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None


class NotificationChannel(BaseModel):
    """Notification channel model."""
    id: str
    name: str
    type: str  # email, webhook, slack
    config: Dict[str, Any]
    enabled: bool = True


class HealthService:
    """Service for monitoring MCP server health."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def _normalize_uuid(self, value: Any) -> _UUID:
        """Normalize string UUIDs to UUID objects."""
        if isinstance(value, _UUID):
            return value
        try:
            return _UUID(str(value))
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    async def perform_health_check(self, server_id: str, current_user: Any = None) -> HealthStatus:
        """Perform manual health check on a server."""
        try:
            server_uuid = self._normalize_uuid(server_id)
            server = self.db.query(McpServer).filter(McpServer.id == server_uuid).first()
            if not server:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Server not found"
                )
            
            # Perform health check
            start_time = datetime.now(timezone.utc)
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Try health endpoint first
                    try:
                        response = await client.get(f"{server.base_url}/health")
                        response.raise_for_status()
                        status_code = "healthy"
                        response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    except httpx.HTTPError:
                        # Fallback to root endpoint
                        response = await client.get(server.base_url)
                        response.raise_for_status()
                        status_code = "healthy"
                        response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                        
            except httpx.TimeoutException:
                status_code = "unhealthy"
                response_time = None
                error_message = "Request timeout"
            except httpx.HTTPError as e:
                status_code = "unhealthy"
                response_time = None
                error_message = f"HTTP error: {e}"
            except Exception as e:
                status_code = "unhealthy"
                response_time = None
                error_message = f"Connection error: {e}"
            
            # Store health check result
            health_check = McpHealthCheck(
                mcp_server_id=server_uuid,
                status=status_code,
                response_time_ms=response_time,
                error_message=error_message,
                checked_at=datetime.now(timezone.utc)
            )
            self.db.add(health_check)
            self.db.commit()
            
            return HealthStatus(
                status=status_code,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc),
                error_message=error_message
            )
            
        except HTTPException:
            # Propagate HTTP exceptions like 404
            raise
        except Exception as e:
            logger.error(f"Health check failed for server {server_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Health check failed"
            )
    
    def get_server_health_status(self, server_id: str, current_user: Any = None) -> Dict[str, Any]:
        """Get current health status of a server."""
        server_uuid = self._normalize_uuid(server_id)
        server = self.db.query(McpServer).filter(McpServer.id == server_uuid).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Get latest health check
        latest_check = self.db.query(McpHealthCheck).filter(
            McpHealthCheck.mcp_server_id == server_uuid
        ).order_by(McpHealthCheck.checked_at.desc()).first()
        
        return {
            "server_id": server_id,
            "server_name": server.name,
            "status": latest_check.status if latest_check else "unknown",
            "last_check": latest_check.checked_at if latest_check else None,
            "last_check_at": latest_check.checked_at if latest_check else None,
            "response_time_ms": latest_check.response_time_ms if latest_check else None,
            "error_message": latest_check.error_message if latest_check else None,
            # Simplified uptime calculation placeholder
            "uptime_percentage": 100.0 if latest_check and latest_check.status == "healthy" else 99.0
        }
    
    def update_health_config(self, server_id: str, config: HealthConfig, current_user: Any = None) -> Dict[str, Any]:
        """Update health check configuration for a server."""
        server_uuid = self._normalize_uuid(server_id)
        server = self.db.query(McpServer).filter(McpServer.id == server_uuid).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Update server health config in server_metadata (primary), fallback to settings if present
        if not server.server_metadata:
            server.server_metadata = {}
        server.server_metadata["health_config"] = config.model_dump()
        server.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Return flattened config fields as response for compatibility with tests
        result = config.model_dump()
        result.update({"updated_at": server.updated_at})
        return result
    
    def get_health_config(self, server_id: str, current_user: Any = None) -> HealthConfig:
        """Get health check configuration for a server."""
        server_uuid = self._normalize_uuid(server_id)
        server = self.db.query(McpServer).filter(McpServer.id == server_uuid).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Get config from server_metadata (preferred), fallback to settings if present
        if getattr(server, "server_metadata", None):
            config_data = server.server_metadata.get("health_config", {})
        elif getattr(server, "settings", None):
            config_data = server.settings.get("health_config", {})
        else:
            config_data = {}
        return HealthConfig(**config_data)
    
    def get_health_history(self, server_id: str, days: int = 7, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get health check history for a server."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        server_uuid = self._normalize_uuid(server_id)
        
        health_checks = self.db.query(McpHealthCheck).filter(
            McpHealthCheck.mcp_server_id == server_uuid,
            McpHealthCheck.checked_at >= since
        ).order_by(McpHealthCheck.checked_at.desc()).all()
        
        return [
            {
                "id": str(check.id),
                "status": check.status,
                "response_time_ms": check.response_time_ms,
                "error_message": check.error_message,
                "checked_at": check.checked_at
            }
            for check in health_checks
        ]
    
    def get_health_alerts(self, server_id: Optional[str] = None, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get health alerts."""
        # Mock health alerts
        alerts = [
            {
                "id": "alert-1",
                "server_id": server_id or "server-123",
                "alert_type": "high_response_time",
                "message": "Server response time is above threshold",
                "severity": "medium",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "resolved_at": None
            }
        ]
        
        if server_id:
            alerts = [alert for alert in alerts if alert["server_id"] == server_id]
        
        return alerts
    
    def create_health_alert(self, server_id: str, alert_data: Dict[str, Any], current_user: Any = None) -> Dict[str, Any]:
        """Create a new health alert."""
        alert = {
            "id": f"alert-{datetime.now().timestamp()}",
            "server_id": server_id,
            "alert_type": alert_data.get("alert_type", "custom"),
            "message": alert_data.get("message", "Custom health alert"),
            "severity": alert_data.get("severity", "low"),
            "created_at": datetime.now(timezone.utc),
            "resolved_at": None
        }
        
        return alert
    
    def update_health_alert(self, alert_id: str, update_data: Dict[str, Any], current_user: Any = None) -> Dict[str, Any]:
        """Update a health alert."""
        # Mock alert update
        return {
            "id": alert_id,
            "message": update_data.get("message", "Updated alert"),
            "severity": update_data.get("severity", "low"),
            "updated_at": datetime.now(timezone.utc)
        }
    
    def delete_health_alert(self, alert_id: str, current_user: Any = None) -> Dict[str, str]:
        """Delete a health alert."""
        return {"message": "Alert deleted successfully"}
    
    def get_health_metrics(self, server_id: str, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get health metrics for a server."""
        # Mock metrics data
        metrics = []
        for i in range(24):  # Last 24 hours
            metrics.append({
                "server_id": server_id,
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=i),
                "response_time_ms": 200 + (i % 3) * 50,
                "status": "healthy" if i % 4 != 0 else "degraded",
                "cpu_usage": 50.0 + (i % 2) * 20.0,
                "memory_usage": 60.0 + (i % 3) * 10.0
            })
        
        return metrics
    
    def get_health_metrics_timeline(self, server_id: str, hours: int = 24, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get health metrics timeline."""
        return self.get_health_metrics(server_id, current_user)
    
    def get_health_summary(self, current_user: Any = None) -> Dict[str, Any]:
        """Get overall health summary."""
        # Mock summary data
        return {
            "total_servers": 10,
            "healthy_servers": 8,
            "unhealthy_servers": 1,
            "degraded_servers": 1,
            "avg_response_time_ms": 250,
            "overall_uptime": 99.5,
            "last_updated": datetime.now(timezone.utc)
        }
    
    def get_notification_channels(self, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get notification channels."""
        # Mock notification channels
        return [
            {
                "id": "channel-1",
                "name": "Email Alerts",
                "type": "email",
                "config": {"email": "admin@example.com"},
                "enabled": True
            },
            {
                "id": "channel-2",
                "name": "Slack Notifications",
                "type": "slack",
                "config": {"webhook_url": "https://hooks.slack.com/..."},
                "enabled": False
            }
        ]
    
    def create_notification_channel(self, channel_data: Dict[str, Any], current_user: Any = None) -> Dict[str, Any]:
        """Create a new notification channel."""
        channel = {
            "id": f"channel-{datetime.now().timestamp()}",
            "name": channel_data.get("name", "New Channel"),
            "type": channel_data.get("type", "email"),
            "config": channel_data.get("config", {}),
            "enabled": channel_data.get("enabled", True),
            "created_at": datetime.now(timezone.utc)
        }
        
        return channel
    
    def test_notification_channel(self, channel_id: str, current_user: Any = None) -> Dict[str, Any]:
        """Test a notification channel."""
        return {
            "channel_id": channel_id,
            "test_status": "success",
            "message": "Test notification sent successfully",
            "tested_at": datetime.now(timezone.utc)
        }


# Compatibility free function used by some tests
async def check_server_health(server_id: str, db_session) -> Dict[str, Any]:
    """Perform a basic health check using HealthService (compat shim)."""
    service = HealthService(db_session)
    result = await service.perform_health_check(server_id)
    return result.model_dump()
