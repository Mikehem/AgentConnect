"""Health monitoring tests."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status

pytestmark = pytest.mark.health


class TestHealthChecks:
    """Test MCP server health checks."""

    @patch('app.services.health.check_server_health')
    def test_manual_health_check_success(self, mock_check, client, sample_user, sample_mcp_server):
        """Test successful manual health check."""
        mock_check.return_value = {
            "status": "healthy",
            "response_time_ms": 150,
            "timestamp": "2024-01-01T00:00:00Z",
            "details": {
                "endpoint": "/health",
                "status_code": 200
            }
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/check")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "response_time_ms" in data
        assert "timestamp" in data

    @patch('app.services.health.check_server_health')
    def test_manual_health_check_unhealthy(self, mock_check, client, sample_user, sample_mcp_server):
        """Test health check when server is unhealthy."""
        mock_check.return_value = {
            "status": "unhealthy",
            "response_time_ms": None,
            "timestamp": "2024-01-01T00:00:00Z",
            "details": {
                "error": "Connection timeout",
                "status_code": None
            }
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/check")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data["details"]

    @patch('app.services.health.check_server_health')
    def test_manual_health_check_degraded(self, mock_check, client, sample_user, sample_mcp_server):
        """Test health check when server is degraded."""
        mock_check.return_value = {
            "status": "degraded",
            "response_time_ms": 5000,  # Slow response
            "timestamp": "2024-01-01T00:00:00Z",
            "details": {
                "endpoint": "/health",
                "status_code": 200,
                "warning": "Response time exceeds threshold"
            }
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/check")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"
        assert "warning" in data["details"]

    def test_health_check_server_not_found(self, client, sample_user):
        """Test health check with non-existent server."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post("/v1/mcp/servers/non-existent-id/health/check")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_health_check_unauthorized(self, client, sample_mcp_server):
        """Test health check without authentication."""
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/check")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHealthStatus:
    """Test health status management."""

    def test_get_server_health_status(self, client, sample_user, sample_mcp_server):
        """Test getting server health status."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "last_check_at" in data
        assert "uptime_percentage" in data

    def test_get_health_status_not_found(self, client, sample_user):
        """Test getting health status for non-existent server."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get("/v1/mcp/servers/non-existent-id/health/status")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_health_config(self, client, sample_user, sample_mcp_server):
        """Test updating health check configuration."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        config_data = {
            "enabled": True,
            "interval_seconds": 300,
            "timeout_seconds": 30,
            "endpoint": "/health",
            "thresholds": {
                "response_time_ms": 5000,
                "success_rate": 0.95
            }
        }
        
        response = client.patch(f"/v1/mcp/servers/{sample_mcp_server.id}/health/config", 
                              json=config_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enabled"] is True
        assert data["interval_seconds"] == 300
        assert data["thresholds"]["response_time_ms"] == 5000

    def test_get_health_config(self, client, sample_user, sample_mcp_server):
        """Test getting health check configuration."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/config")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "enabled" in data
        assert "interval_seconds" in data
        assert "timeout_seconds" in data


class TestHealthHistory:
    """Test health check history."""

    def test_get_health_history(self, client, sample_user, sample_mcp_server):
        """Test getting health check history."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/history")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)

    def test_get_health_history_with_filters(self, client, sample_user, sample_mcp_server):
        """Test getting health check history with filters."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/history?status=healthy&limit=10")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "history" in data

    def test_get_health_history_date_range(self, client, sample_user, sample_mcp_server):
        """Test getting health check history with date range."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/history?start_date=2024-01-01&end_date=2024-01-31")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "history" in data


class TestHealthAlerts:
    """Test health monitoring alerts."""

    def test_get_health_alerts(self, client, sample_user, sample_mcp_server):
        """Test getting health alerts."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/alerts")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_create_health_alert(self, client, sample_user, sample_mcp_server):
        """Test creating health alert."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        alert_data = {
            "type": "response_time",
            "threshold": 5000,
            "condition": "greater_than",
            "enabled": True,
            "notification_channels": ["email", "webhook"]
        }
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/alerts", 
                             json=alert_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == "response_time"
        assert data["threshold"] == 5000
        assert data["enabled"] is True

    def test_update_health_alert(self, client, sample_user, sample_mcp_server):
        """Test updating health alert."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        update_data = {
            "enabled": False,
            "threshold": 3000
        }
        
        response = client.patch(f"/v1/mcp/servers/{sample_mcp_server.id}/health/alerts/alert-id", 
                              json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enabled"] is False
        assert data["threshold"] == 3000

    def test_delete_health_alert(self, client, sample_user, sample_mcp_server):
        """Test deleting health alert."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.delete(f"/v1/mcp/servers/{sample_mcp_server.id}/health/alerts/alert-id")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Alert deleted successfully"


class TestHealthMetrics:
    """Test health metrics and analytics."""

    def test_get_health_metrics(self, client, sample_user, sample_mcp_server):
        """Test getting health metrics."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/metrics")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "uptime_percentage" in data
        assert "average_response_time" in data
        assert "success_rate" in data
        assert "total_checks" in data

    def test_get_health_metrics_timeline(self, client, sample_user, sample_mcp_server):
        """Test getting health metrics timeline."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/metrics/timeline")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "timeline" in data
        assert isinstance(data["timeline"], list)

    def test_get_health_summary(self, client, sample_user):
        """Test getting health summary for all servers."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get("/v1/health/summary")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_servers" in data
        assert "healthy_servers" in data
        assert "unhealthy_servers" in data
        assert "degraded_servers" in data
        assert "overall_uptime" in data


class TestHealthNotifications:
    """Test health notification system."""

    def test_get_notification_channels(self, client, sample_user, sample_mcp_server):
        """Test getting notification channels."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/health/notifications/channels")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)

    def test_create_notification_channel(self, client, sample_user, sample_mcp_server):
        """Test creating notification channel."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        channel_data = {
            "type": "webhook",
            "name": "Slack Alerts",
            "config": {
                "url": "https://hooks.slack.com/services/xxx/yyy/zzz",
                "channel": "#alerts"
            },
            "enabled": True
        }
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/notifications/channels", 
                             json=channel_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == "webhook"
        assert data["name"] == "Slack Alerts"
        assert data["enabled"] is True

    def test_test_notification_channel(self, client, sample_user, sample_mcp_server):
        """Test testing notification channel."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/health/notifications/channels/channel-id/test")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data
