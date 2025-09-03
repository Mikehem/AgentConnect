"""API tests for MCP Servers feature."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status
from sqlalchemy.orm import Session

from app.services.mcp_server import McpServerService
from app.schemas.mcp_server import McpServerCreate, McpServerUpdate

pytestmark = pytest.mark.api


class TestMcpServerAPICreate:
    """Test MCP server creation API endpoints."""

    @patch('app.services.mcp_registration.McpRegistrationService._test_server_connectivity')
    @patch('app.services.mcp_registration.McpRegistrationService._perform_handshake')
    def test_create_server_success(self, mock_handshake, mock_connectivity, client, sample_user, valid_server_data):
        """Test successful server creation."""
        # Mock the connectivity test and handshake
        mock_connectivity.return_value = AsyncMock()
        
        # Mock handshake response with proper structure
        from app.schemas.mcp_protocol import McpHandshakeResponse, McpServerInfo
        mock_handshake_response = McpHandshakeResponse(
            protocol_version="1.0",
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0"
            ),
            capabilities={}
        )
        mock_handshake.return_value = mock_handshake_response
        
        # Mock authentication
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post("/v1/mcp/servers", json=valid_server_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == valid_server_data["name"]
        assert data["base_url"] == valid_server_data["base_url"]
        assert data["environment"] == valid_server_data["environment"]

    def test_create_server_validation_error(self, client, sample_user):
        """Test server creation with invalid data."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        invalid_data = {
            "name": "",  # Invalid: empty name
            "base_url": "invalid-url",  # Invalid URL
            "environment": "invalid-env"  # Invalid environment
        }
        
        response = client.post("/v1/mcp/servers", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()["detail"]
        assert "name" in error_detail

    @patch('app.services.mcp_registration.McpRegistrationService._test_server_connectivity')
    @patch('app.services.mcp_registration.McpRegistrationService._perform_handshake')
    def test_create_server_duplicate_name(self, mock_handshake, mock_connectivity, client, sample_user, sample_mcp_server, valid_server_data):
        """Test server creation with duplicate name in same environment."""
        # Mock the connectivity test and handshake
        mock_connectivity.return_value = AsyncMock()
        
        # Mock handshake response with proper structure
        from app.schemas.mcp_protocol import McpHandshakeResponse, McpServerInfo
        mock_handshake_response = McpHandshakeResponse(
            protocol_version="1.0",
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0"
            ),
            capabilities={}
        )
        mock_handshake.return_value = mock_handshake_response
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Try to create server with same name and environment
        duplicate_data = valid_server_data.copy()
        duplicate_data["name"] = sample_mcp_server.name
        duplicate_data["environment"] = sample_mcp_server.environment
        
        response = client.post("/v1/mcp/servers", json=duplicate_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_create_server_unauthorized(self, client, valid_server_data):
        """Test server creation without authentication."""
        response = client.post("/v1/mcp/servers", json=valid_server_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMcpServerAPIList:
    """Test MCP server listing API endpoints."""

    def test_list_servers_success(self, client, sample_user, sample_mcp_server):
        """Test successful server listing."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get("/v1/mcp/servers")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "servers" in data
        assert len(data["servers"]) >= 1
        assert data["total"] >= 1

    def test_list_servers_with_filters(self, client, sample_user, sample_mcp_server):
        """Test server listing with query parameters."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get("/v1/mcp/servers?environment=development&status=active")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "servers" in data

    def test_list_servers_unauthorized(self, client):
        """Test server listing without authentication."""
        response = client.get("/v1/mcp/servers")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMcpServerAPIGet:
    """Test MCP server retrieval API endpoints."""

    def test_get_server_success(self, client, sample_user, sample_mcp_server):
        """Test successful server retrieval."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_mcp_server.id)
        assert data["name"] == sample_mcp_server.name

    def test_get_server_not_found(self, client, sample_user):
        """Test server retrieval with non-existent ID."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Use a valid UUID that doesn't exist
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/v1/mcp/servers/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_server_unauthorized(self, client, sample_mcp_server):
        """Test server retrieval without authentication."""
        response = client.get(f"/v1/mcp/servers/{sample_mcp_server.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMcpServerAPIUpdate:
    """Test MCP server update API endpoints."""

    def test_update_server_success(self, client, sample_user, sample_mcp_server):
        """Test successful server update."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        update_data = {
            "description": "Updated description",
            "tags": ["updated", "test"]
        }
        
        response = client.patch(f"/v1/mcp/servers/{sample_mcp_server.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["tags"] == update_data["tags"]

    def test_update_server_not_found(self, client, sample_user):
        """Test server update with non-existent ID."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Use a valid UUID that doesn't exist
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"description": "Updated description"}
        
        response = client.patch(f"/v1/mcp/servers/{non_existent_id}", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_server_validation_error(self, client, sample_user, sample_mcp_server):
        """Test server update with invalid data."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        invalid_data = {
            "base_url": "invalid-url",
            "environment": "invalid-env"
        }
        
        response = client.patch(f"/v1/mcp/servers/{sample_mcp_server.id}", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMcpServerAPIDelete:
    """Test MCP server deletion API endpoints."""

    def test_delete_server_success(self, client, sample_user, sample_mcp_server):
        """Test successful server deletion."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.delete(f"/v1/mcp/servers/{sample_mcp_server.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "MCP server deleted successfully"

    def test_delete_server_not_found(self, client, sample_user):
        """Test server deletion with non-existent ID."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Use a valid UUID that doesn't exist
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/v1/mcp/servers/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_server_unauthorized(self, client, sample_mcp_server):
        """Test server deletion without authentication."""
        response = client.delete(f"/v1/mcp/servers/{sample_mcp_server.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMcpServerAPIDuplicateHandling:
    """Test MCP server duplicate name handling."""

    @patch('app.services.mcp_registration.McpRegistrationService._test_server_connectivity')
    @patch('app.services.mcp_registration.McpRegistrationService._perform_handshake')
    def test_create_server_different_environment(self, mock_handshake, mock_connectivity, client, sample_user, sample_mcp_server, valid_server_data):
        """Test creating server with same name but different environment."""
        # Mock the connectivity test and handshake
        mock_connectivity.return_value = AsyncMock()
        
        # Mock handshake response with proper structure
        from app.schemas.mcp_protocol import McpHandshakeResponse, McpServerInfo
        mock_handshake_response = McpHandshakeResponse(
            protocol_version="1.0",
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0"
            ),
            capabilities={}
        )
        mock_handshake.return_value = mock_handshake_response
        
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Create server with same name but different environment
        different_env_data = valid_server_data.copy()
        different_env_data["name"] = sample_mcp_server.name
        different_env_data["environment"] = "production"  # Different environment
        
        response = client.post("/v1/mcp/servers", json=different_env_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_mcp_server.name
        assert data["environment"] == "production"
