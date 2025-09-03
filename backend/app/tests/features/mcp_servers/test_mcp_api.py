"""Comprehensive tests for MCP API endpoints."""

import pytest
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.schemas.mcp_protocol import (
    McpServerSpecification, McpServerInfo, McpTool, McpToolParameter,
    McpResource, McpResourceType, McpServerRegistration, McpCapabilityDiscovery
)
from app.models.mcp_server import McpServer, McpCredential, McpCapability
from app.models.user import User
from app.models.organization import Organization

pytestmark = pytest.mark.api


class TestMcpServerApiEndpoints:
    """Test MCP server API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return User(
            id="user-123",
            org_id="org-123",
            email="test@example.com",
            name="Test User",
            roles=["admin"],
            status="active"
        )
    
    @pytest.fixture
    def mock_specification(self):
        """Create mock MCP specification."""
        return McpServerSpecification(
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0",
                description="Test MCP server"
            ),
            tools=[
                McpTool(
                    name="test_tool",
                    description="Test tool",
                    input_schema=McpToolParameter(type="object")
                )
            ],
            resources=[
                McpResource(
                    uri="file:///test.txt",
                    name="test.txt",
                    resource_type=McpResourceType.FILE
                )
            ]
        )
    
    @pytest.fixture
    def mock_registration(self, mock_specification):
        """Create mock MCP registration."""
        return McpServerRegistration(
            specification=mock_specification,
            endpoint_url="https://example.com/mcp",
            auth_config={
                "type": "bearer_token",
                "token": "secret-token"
            },
            metadata={
                "environment": "production",
                "region": "us-east-1"
            }
        )
    
    class TestRegisterFromSpecification:
        """Test /register/specification endpoint."""
        
        def test_successful_registration(self, client, mock_registration):
            """Test successful server registration from specification."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service

                mock_server = MagicMock()
                mock_server.id = uuid.uuid4()
                mock_server.name = "test-server"
                mock_server.status = "active"
                mock_server.created_at = "2024-01-01T00:00:00Z"
                mock_service.register_from_specification = AsyncMock(return_value=mock_server)
                
                response = client.post(
                    "/v1/mcp/servers/register/specification",
                    json=mock_registration.model_dump()
                )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert uuid.UUID(data["id"])  # Verify it's a valid UUID
            assert data["name"] == "test-server"
            assert data["status"] == "active"
            
            mock_service.register_from_specification.assert_called_once()
        
        def test_validation_error(self, client, mock_registration):
            """Test registration with validation error."""
            
            # Create invalid registration (empty server name)
            invalid_registration = mock_registration.model_dump()
            invalid_registration["specification"]["server_info"]["name"] = ""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                response = client.post(
                    "/v1/mcp/servers/register/specification",
                    json=invalid_registration
                )
                
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        def test_service_error(self, client, mock_registration):
            """Test registration with service error."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.register_from_specification = AsyncMock(side_effect=ValueError("Service error"))
                
                response = client.post(
                    "/v1/mcp/servers/register/specification",
                    json=mock_registration.model_dump()
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "Service error" in data["detail"]
        
        def test_unexpected_error(self, client, mock_registration):
            """Test registration with unexpected error."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.register_from_specification = AsyncMock(side_effect=Exception("Unexpected error"))
                
                response = client.post(
                    "/v1/mcp/servers/register/specification",
                    json=mock_registration.model_dump()
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert data["detail"] == "Internal server error"
    
    class TestRegisterFromUrl:
        """Test /register/url endpoint."""
        
        def test_successful_url_registration(self, client):
            """Test successful registration from URL."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                
                mock_server = MagicMock()
                mock_server.id = uuid.uuid4()
                mock_server.name = "test-server"
                mock_server.status = "active"
                mock_server.created_at = "2024-01-01T00:00:00Z"
                mock_service.register_from_url = AsyncMock(return_value=mock_server)
                
                response = client.post(
                    "/v1/mcp/servers/register/url",
                    data={
                        "spec_url": "https://example.com/spec.json",
                        "endpoint_url": "https://example.com/mcp",
                        "auth_config": json.dumps({
                            "type": "bearer_token",
                            "token": "secret-token"
                        })
                    }
                )
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert uuid.UUID(data["id"])  # Verify it's a valid UUID
                assert data["name"] == "test-server"
                
                mock_service.register_from_url.assert_called_once()
        
        def test_invalid_auth_config_json(self, client):
            """Test registration with invalid auth config JSON."""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                response = client.post(
                    "/v1/mcp/servers/register/url",
                    data={
                        "spec_url": "https://example.com/spec.json",
                        "endpoint_url": "https://example.com/mcp",
                        "auth_config": "invalid json"
                    }
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "Invalid authentication configuration JSON" in data["detail"]
        
        def test_service_error(self, client):
            """Test registration with service error."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.register_from_url.side_effect = ValueError("Service error")
                
                response = client.post(
                    "/v1/mcp/servers/register/url",
                    data={
                        "spec_url": "https://example.com/spec.json",
                        "endpoint_url": "https://example.com/mcp"
                    }
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "Service error" in data["detail"]
    
    class TestRegisterFromFile:
        """Test /register/file endpoint."""
        
        def test_successful_file_registration(self, client):
            """Test successful registration from file."""
            
            # Create temporary JSON file content
            spec_data = {
                "server_info": {
                    "name": "test-server",
                    "version": "1.0.0",
                    "description": "Test MCP server"
                },
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "Test tool",
                        "input_schema": {"type": "object"}
                    }
                ],
                "resources": []
            }
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()), \
                 patch('tempfile.NamedTemporaryFile') as mock_temp_file:
                
                # Mock temporary file
                mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.json"
                mock_temp_file.return_value.__enter__.return_value.write = MagicMock()
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                
                mock_server = MagicMock()
                mock_server.id = uuid.uuid4()
                mock_server.name = "test-server"
                mock_server.status = "active"
                mock_server.created_at = "2024-01-01T00:00:00Z"
                mock_service.register_from_json_file = AsyncMock(return_value=mock_server)
                
                # Create file upload
                files = {"file": ("test.json", json.dumps(spec_data), "application/json")}
                data = {
                    "endpoint_url": "https://example.com/mcp",
                    "auth_config": json.dumps({
                        "type": "bearer_token",
                        "token": "secret-token"
                    })
                }
                
                response = client.post(
                    "/v1/mcp/servers/register/file",
                    files=files,
                    data=data
                )
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert uuid.UUID(data["id"])  # Verify it's a valid UUID
                assert data["name"] == "test-server"
                
                mock_service.register_from_json_file.assert_called_once()
        
        def test_invalid_file_type(self, client):
            """Test registration with invalid file type."""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                # Create file upload with wrong extension
                files = {"file": ("test.txt", "content", "text/plain")}
                data = {"endpoint_url": "https://example.com/mcp"}
                
                response = client.post(
                    "/v1/mcp/servers/register/file",
                    files=files,
                    data=data
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "File must be a JSON file" in data["detail"]
        
        def test_invalid_auth_config_json(self, client):
            """Test registration with invalid auth config JSON."""
            
            spec_data = {
                "server_info": {
                    "name": "test-server",
                    "version": "1.0.0"
                }
            }
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                files = {"file": ("test.json", json.dumps(spec_data), "application/json")}
                data = {
                    "endpoint_url": "https://example.com/mcp",
                    "auth_config": "invalid json"
                }
                
                response = client.post(
                    "/v1/mcp/servers/register/file",
                    files=files,
                    data=data
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "Invalid authentication configuration JSON" in data["detail"]
        
        def test_service_error(self, client):
            """Test registration with service error."""
            
            spec_data = {
                "server_info": {
                    "name": "test-server",
                    "version": "1.0.0"
                }
            }
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()), \
                 patch('tempfile.NamedTemporaryFile') as mock_temp_file:
                
                # Mock temporary file
                mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.json"
                mock_temp_file.return_value.__enter__.return_value.write = MagicMock()
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.register_from_json_file.side_effect = ValueError("Service error")
                
                files = {"file": ("test.json", json.dumps(spec_data), "application/json")}
                data = {"endpoint_url": "https://example.com/mcp"}
                
                response = client.post(
                    "/v1/mcp/servers/register/file",
                    files=files,
                    data=data
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "Service error" in data["detail"]
    
    class TestDiscoverCapabilities:
        """Test /{server_id}/discover endpoint."""
        
        def test_successful_discovery(self, client):
            """Test successful capability discovery."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                
                mock_discovery = McpCapabilityDiscovery(
                    server_id="server-123",
                    discovered_at="2024-01-01T00:00:00Z",
                    capabilities={
                        "tool1": {"type": "function"},
                        "tool2": {"type": "procedure"}
                    },
                    resources=[],
                    tools=[],
                    errors=[],
                    warnings=[]
                )
                mock_service.discover_capabilities = AsyncMock(return_value=mock_discovery)
                
                response = client.post("/v1/mcp/servers/server-123/discover")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["server_id"] == "server-123"
                assert len(data["capabilities"]) == 2
                
                mock_service.discover_capabilities.assert_called_once_with(
                    server_id="server-123",
                    current_user=ANY,
                    request_id=ANY
                )
        
        def test_server_not_found(self, client):
            """Test discovery with non-existent server."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.discover_capabilities.side_effect = ValueError("Server not found")
                
                response = client.post("/v1/mcp/servers/server-123/discover")
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "Server not found" in data["detail"]
        
        def test_discovery_failure(self, client):
            """Test discovery failure."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.discover_capabilities.side_effect = Exception("Discovery failed")
                
                response = client.post("/v1/mcp/servers/server-123/discover")
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert data["detail"] == "Internal server error"
    
    class TestLegacyEndpoints:
        """Test legacy endpoints for backward compatibility."""
        
        def test_legacy_create_endpoint(self, client):
            """Test legacy / endpoint."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                
                mock_server = MagicMock()
                mock_server.id = uuid.uuid4()
                mock_server.name = "legacy-server"
                mock_server.status = "active"
                mock_server.created_at = "2024-01-01T00:00:00Z"
                mock_service.register_from_specification = AsyncMock(return_value=mock_server)
                
                legacy_data = {
                    "name": "legacy-server",
                    "version": "1.0.0",
                    "description": "Legacy server",
                    "base_url": "https://example.com/mcp"
                }
                
                response = client.post(
                    "/v1/mcp/servers/",
                    json=legacy_data
                )
                
                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert uuid.UUID(data["id"])  # Verify it's a valid UUID
                assert data["name"] == "legacy-server"
                
                mock_service.register_from_specification.assert_called_once()
        
        def test_legacy_endpoint_error(self, client):
            """Test legacy endpoint with error."""
            
            with patch('app.api.v1.mcp_servers.McpRegistrationService') as mock_service_class, \
                 patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.register_from_specification.side_effect = Exception("Legacy error")
                
                legacy_data = {
                    "name": "legacy-server",
                    "base_url": "https://example.com/mcp"
                }
                
                response = client.post(
                    "/v1/mcp/servers/",
                    json=legacy_data
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert data["detail"] == "Internal server error"
    
    class TestOtherEndpoints:
        """Test other API endpoints."""
        
        def test_list_servers(self, client):
            """Test GET / endpoint."""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                response = client.get("/v1/mcp/servers/")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["servers"] == []
                assert data["total"] == 0
                assert data["limit"] == 100
                assert data["offset"] == 0
                assert data["has_more"] is False
        
        def test_get_server_not_found(self, client):
            """Test GET /{server_id} endpoint with non-existent server."""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                response = client.get("/v1/mcp/servers/server-123")
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert data["detail"] == "Server not found"
        
        def test_update_server_not_found(self, client):
            """Test PATCH /{server_id} endpoint with non-existent server."""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                update_data = {"name": "updated-server"}
                
                response = client.patch(
                    "/v1/mcp/servers/server-123",
                    json=update_data
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert data["detail"] == "Server not found"
        
        def test_delete_server_not_found(self, client):
            """Test DELETE /{server_id} endpoint with non-existent server."""
            
            with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
                 patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
                
                response = client.delete("/v1/mcp/servers/server-123")
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert data["detail"] == "Server not found"


class TestMcpApiIntegration:
    """Integration tests for MCP API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_api_endpoints_exist(self, client):
        """Test that all API endpoints exist and are accessible."""
        
        # Test that the router is properly mounted
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    def test_openapi_schema_includes_mcp_endpoints(self, client):
        """Test that OpenAPI schema includes MCP endpoints."""
        
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        # Check that MCP endpoints are in the schema
        assert "/v1/mcp/servers/register/specification" in paths
        assert "/v1/mcp/servers/register/url" in paths
        assert "/v1/mcp/servers/register/file" in paths
        assert "/v1/mcp/servers/{server_id}/discover" in paths
        assert "/v1/mcp/servers/" in paths  # Legacy endpoint
        assert "/v1/mcp/servers/{server_id}" in paths
    
    def test_endpoint_descriptions(self, client):
        """Test that endpoints have proper descriptions."""
        
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})
        
        # Check endpoint descriptions
        spec_endpoint = paths.get("/v1/mcp/servers/register/specification", {})
        assert "post" in spec_endpoint
        assert "summary" in spec_endpoint["post"]
        assert "Register MCP Server from Specification" in spec_endpoint["post"]["summary"]
        
        url_endpoint = paths.get("/v1/mcp/servers/register/url", {})
        assert "post" in url_endpoint
        assert "summary" in url_endpoint["post"]
        assert "Register MCP Server from Specification URL" in url_endpoint["post"]["summary"]
        
        file_endpoint = paths.get("/v1/mcp/servers/register/file", {})
        assert "post" in file_endpoint
        assert "summary" in file_endpoint["post"]
        assert "Register MCP Server from JSON File" in file_endpoint["post"]["summary"]
        
        discover_endpoint = paths.get("/v1/mcp/servers/{server_id}/discover", {})
        assert "post" in discover_endpoint
        assert "summary" in discover_endpoint["post"]
        assert "Discover Server Capabilities" in discover_endpoint["post"]["summary"]
    
    def test_request_validation(self, client):
        """Test request validation for MCP endpoints."""
        
        # Test invalid specification (missing required fields)
        invalid_spec = {
            "specification": {
                "server_info": {
                    "name": "",  # Invalid empty name
                    "version": "1.0.0"
                }
            },
            "endpoint_url": "https://example.com/mcp"
        }
        
        with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
             patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
            
            response = client.post(
                "/v1/mcp/servers/register/specification",
                json=invalid_spec
            )
            
            # Should fail validation
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid endpoint URL
        invalid_url_spec = {
            "specification": {
                "server_info": {
                    "name": "test-server",
                    "version": "1.0.0"
                }
            },
            "endpoint_url": "invalid-url"  # Invalid URL
        }
        
        with patch('app.api.v1.mcp_servers.get_current_user', return_value=MagicMock()), \
             patch('app.api.v1.mcp_servers.get_db', return_value=MagicMock()):
            
            response = client.post(
                "/v1/mcp/servers/register/specification",
                json=invalid_url_spec
            )
            
            # Should fail validation
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_error_handling(self, client):
        """Test error handling for MCP endpoints."""
        
        # Test with missing authentication
        response = client.post("/v1/mcp/servers/register/specification")
        
        # Should return 422 due to missing request body
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test with invalid JSON
        response = client.post(
            "/v1/mcp/servers/register/specification",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 due to invalid JSON
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_content_type_validation(self, client):
        """Test content type validation."""
        
        # Test with wrong content type
        response = client.post(
            "/v1/mcp/servers/register/specification",
            data="test data",
            headers={"Content-Type": "text/plain"}
        )
        
        # Should return 422 due to wrong content type
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
