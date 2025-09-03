"""Capability discovery tests."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status

pytestmark = pytest.mark.capabilities


class TestCapabilityDiscovery:
    """Test MCP server capability discovery."""

    @patch('app.services.capabilities.discover_server_capabilities')
    def test_discover_capabilities_success(self, mock_discover, client, sample_user, sample_mcp_server):
        """Test successful capability discovery."""
        mock_discover.return_value = [
            {
                "name": "filesystem",
                "version": "1.0.0",
                "description": "File system operations"
            },
            {
                "name": "github",
                "version": "1.0.0", 
                "description": "GitHub integration"
            }
        ]
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/discover")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "capabilities" in data
        assert len(data["capabilities"]) == 2
        assert data["capabilities"][0]["name"] == "filesystem"

    @patch('app.services.capabilities.discover_server_capabilities')
    def test_discover_capabilities_server_unavailable(self, mock_discover, client, sample_user, sample_mcp_server):
        """Test capability discovery when server is unavailable."""
        mock_discover.side_effect = ConnectionError("Server unavailable")
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/discover")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "unavailable" in response.json()["detail"].lower()

    @patch('app.services.capabilities.discover_server_capabilities')
    def test_discover_capabilities_authentication_error(self, mock_discover, client, sample_user, sample_mcp_server):
        """Test capability discovery with authentication error."""
        mock_discover.side_effect = ValueError("Authentication failed")
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/discover")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "authentication" in response.json()["detail"].lower()

    def test_discover_capabilities_server_not_found(self, client, sample_user):
        """Test capability discovery with non-existent server."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post("/v1/mcp/servers/non-existent-id/discover")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_discover_capabilities_unauthorized(self, client, sample_mcp_server):
        """Test capability discovery without authentication."""
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/discover")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCapabilityValidation:
    """Test capability validation."""

    def test_validate_capability_schema(self, client, sample_user, sample_mcp_server):
        """Test capability schema validation."""
        capability_data = {
            "name": "filesystem",
            "version": "1.0.0",
            "description": "File system operations",
            "methods": [
                {
                    "name": "read_file",
                    "description": "Read file contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            ]
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/validate", 
                             json=capability_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True

    def test_validate_invalid_capability_schema(self, client, sample_user, sample_mcp_server):
        """Test invalid capability schema validation."""
        invalid_capability_data = {
            "name": "",  # Invalid: empty name
            "version": "invalid-version",  # Invalid version format
            "methods": "not-an-array"  # Invalid: should be array
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/validate", 
                             json=invalid_capability_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCapabilityTesting:
    """Test capability testing."""

    @patch('app.services.capabilities.test_capability_method')
    def test_test_capability_method_success(self, mock_test, client, sample_user, sample_mcp_server):
        """Test successful capability method testing."""
        mock_test.return_value = {
            "success": True,
            "response": {"content": "file contents"},
            "duration_ms": 150
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        test_data = {
            "capability_name": "filesystem",
            "method_name": "read_file",
            "parameters": {"path": "/test/file.txt"}
        }
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/test", 
                             json=test_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "response" in data
        assert "duration_ms" in data

    @patch('app.services.capabilities.test_capability_method')
    def test_test_capability_method_failure(self, mock_test, client, sample_user, sample_mcp_server):
        """Test capability method testing failure."""
        mock_test.return_value = {
            "success": False,
            "error": "File not found",
            "duration_ms": 50
        }
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        test_data = {
            "capability_name": "filesystem",
            "method_name": "read_file",
            "parameters": {"path": "/non-existent/file.txt"}
        }
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/test", 
                             json=test_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_test_capability_invalid_data(self, client, sample_user, sample_mcp_server):
        """Test capability testing with invalid data."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        invalid_test_data = {
            "capability_name": "",  # Invalid: empty name
            "method_name": "read_file",
            "parameters": "not-an-object"  # Invalid: should be object
        }
        
        response = client.post(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/test", 
                             json=invalid_test_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCapabilityManagement:
    """Test capability management."""

    def test_list_server_capabilities(self, client, sample_user, sample_mcp_server):
        """Test listing server capabilities."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "capabilities" in data

    def test_get_capability_details(self, client, sample_user, sample_mcp_server):
        """Test getting capability details."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/filesystem")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data

    def test_get_capability_not_found(self, client, sample_user, sample_mcp_server):
        """Test getting non-existent capability."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/non-existent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_capability_metadata(self, client, sample_user, sample_mcp_server):
        """Test updating capability metadata."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        update_data = {
            "description": "Updated description",
            "tags": ["updated", "filesystem"],
            "metadata": {"category": "storage"}
        }
        
        response = client.patch(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/filesystem", 
                              json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated description"
        assert "updated" in data["tags"]


class TestCapabilityAnalytics:
    """Test capability analytics."""

    def test_get_capability_usage_stats(self, client, sample_user, sample_mcp_server):
        """Test getting capability usage statistics."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/filesystem/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_calls" in data
        assert "success_rate" in data
        assert "average_response_time" in data
        assert "error_count" in data

    def test_get_capability_usage_timeline(self, client, sample_user, sample_mcp_server):
        """Test getting capability usage timeline."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/filesystem/timeline")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "timeline" in data
        assert isinstance(data["timeline"], list)

    def test_get_capability_error_logs(self, client, sample_user, sample_mcp_server):
        """Test getting capability error logs."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}/capabilities/filesystem/errors")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "errors" in data
        assert isinstance(data["errors"], list)
