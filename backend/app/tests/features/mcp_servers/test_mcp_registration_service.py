"""Comprehensive tests for MCP Registration Service."""

import pytest
import uuid
import json
import tempfile
import os
import httpx
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.services.mcp_registration import McpRegistrationService
from app.schemas.mcp_protocol import (
    McpServerSpecification, McpServerInfo, McpTool, McpToolParameter,
    McpResource, McpResourceType, McpHandshakeResponse, McpCapabilityDiscovery
)
from app.models.mcp_server import McpServer, McpCredential, McpCapability
from app.models.user import User
from app.models.organization import Organization

pytestmark = pytest.mark.mcp_registration

class TestMcpRegistrationService:
    """Test MCP Registration Service."""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return User(
            id=uuid.uuid4(),
            org_id=uuid.uuid4(),
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
    def mock_handshake_response(self):
        """Create mock handshake response."""
        return McpHandshakeResponse(
            protocol_version="1.0",
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0"
            ),
            capabilities={
                "supports_websockets": True,
                "max_message_size": 1024
            }
        )
    
    @pytest.fixture
    def service(self, db_session):
        """Create MCP registration service instance."""
        return McpRegistrationService(db_session)
    
    class TestRegisterFromSpecification:
        """Test register_from_specification method."""
        
        @pytest.mark.asyncio
        async def test_successful_registration(
            self, service, mock_user, mock_specification, mock_handshake_response
        ):
            """Test successful server registration from specification."""
            
            with patch.object(service, '_test_server_connectivity', new_callable=AsyncMock) as mock_connectivity, \
                 patch.object(service, '_perform_handshake', new_callable=AsyncMock) as mock_handshake, \
                 patch.object(service, '_create_server_record', return_value=MagicMock()) as mock_create, \
                 patch.object(service, '_store_capabilities', new_callable=MagicMock) as mock_store:
                
                mock_handshake.return_value = mock_handshake_response
                mock_server = MagicMock()
                mock_server.id = "server-123"
                mock_create.return_value = mock_server
                
                result = await service.register_from_specification(
                    spec=mock_specification,
                    endpoint_url="https://example.com/mcp",
                    current_user=mock_user,
                    auth_config={"type": "bearer_token", "token": "secret"},
                    request_id="req-123"
                )
                
                # Verify method calls
                mock_connectivity.assert_called_once_with(
                    "https://example.com/mcp",
                    {"type": "bearer_token", "token": "secret"}
                )
                mock_handshake.assert_called_once_with(
                    "https://example.com/mcp",
                    {"type": "bearer_token", "token": "secret"}
                )
                mock_create.assert_called_once_with(
                    mock_specification,
                    "https://example.com/mcp",
                    mock_user,
                    {"type": "bearer_token", "token": "secret"}
                )
                mock_store.assert_called_once_with(
                    mock_server,
                    mock_specification,
                    mock_handshake_response
                )
                
                assert result == mock_server
        
        @pytest.mark.asyncio
        async def test_validation_error(self, service, mock_user, mock_specification):
            """Test registration with validation error."""
            
            with patch.object(service, '_validate_specification') as mock_validate:
                mock_validate.side_effect = ValueError("Server name cannot be empty")
                
                with pytest.raises(ValueError, match="Server name cannot be empty"):
                    await service.register_from_specification(
                        mock_specification,  # Use valid spec, let mock handle validation
                        "https://example.com/mcp",
                        mock_user
                    )
        
        @pytest.mark.asyncio
        async def test_connectivity_failure(self, service, mock_user, mock_specification):
            """Test registration with connectivity failure."""
            
            with patch.object(service, '_test_server_connectivity', 
                            new_callable=AsyncMock, side_effect=ValueError("Connection failed")):
                
                with pytest.raises(ValueError, match="Connection failed"):
                    await service.register_from_specification(
                        spec=mock_specification,
                        endpoint_url="https://example.com/mcp",
                        current_user=mock_user
                    )
        
        @pytest.mark.asyncio
        async def test_handshake_failure(self, service, mock_user, mock_specification):
            """Test registration with handshake failure."""
            
            with patch.object(service, '_test_server_connectivity', new_callable=AsyncMock), \
                 patch.object(service, '_perform_handshake', 
                            new_callable=AsyncMock, side_effect=Exception("Handshake failed")):
                
                with pytest.raises(Exception, match="Handshake failed"):
                    await service.register_from_specification(
                        spec=mock_specification,
                        endpoint_url="https://example.com/mcp",
                        current_user=mock_user
                    )
    
    class TestRegisterFromJsonFile:
        """Test register_from_json_file method."""
        
        @pytest.mark.asyncio
        async def test_successful_file_registration(
            self, service, mock_user, mock_specification, mock_handshake_response
        ):
            """Test successful registration from JSON file."""
            
            # Create temporary JSON file
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(spec_data, temp_file)
                temp_path = temp_file.name
            
            try:
                with patch.object(service, 'register_from_specification', 
                                new_callable=AsyncMock) as mock_register:
                    
                    mock_server = MagicMock()
                    mock_server.id = "server-123"
                    mock_register.return_value = mock_server
                    
                    result = await service.register_from_json_file(
                        json_file_path=temp_path,
                        endpoint_url="https://example.com/mcp",
                        current_user=mock_user,
                        auth_config={"type": "bearer_token"},
                        request_id="req-123"
                    )
                    
                    mock_register.assert_called_once()
                    assert result == mock_server
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
        
        @pytest.mark.asyncio
        async def test_file_not_found(self, service, mock_user):
            """Test registration with non-existent file."""
            
            with pytest.raises(ValueError, match="Specification file not found"):
                await service.register_from_json_file(
                    json_file_path="/non/existent/file.json",
                    endpoint_url="https://example.com/mcp",
                    current_user=mock_user
                )
        
        @pytest.mark.asyncio
        async def test_invalid_json_file(self, service, mock_user):
            """Test registration with invalid JSON file."""
            
            # Create temporary invalid JSON file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_file.write("invalid json content")
                temp_path = temp_file.name
            
            try:
                with pytest.raises(ValueError, match="Invalid JSON"):
                    await service.register_from_json_file(
                        json_file_path=temp_path,
                        endpoint_url="https://example.com/mcp",
                        current_user=mock_user
                    )
            finally:
                os.unlink(temp_path)
    
    class TestRegisterFromUrl:
        """Test register_from_url method."""
        
        @pytest.mark.asyncio
        async def test_successful_url_registration(
            self, service, mock_user, mock_specification, mock_handshake_response
        ):
            """Test successful registration from URL."""
            
            with patch.object(service, '_load_specification_from_url', 
                            new_callable=AsyncMock, return_value=mock_specification), \
                 patch.object(service, 'register_from_specification', 
                            new_callable=AsyncMock) as mock_register:
                
                mock_server = MagicMock()
                mock_server.id = "server-123"
                mock_register.return_value = mock_server
                
                result = await service.register_from_url(
                    spec_url="https://example.com/spec.json",
                    endpoint_url="https://example.com/mcp",
                    current_user=mock_user,
                    auth_config={"type": "bearer_token"},
                    request_id="req-123"
                )
                
                mock_register.assert_called_once_with(
                    mock_specification,
                    "https://example.com/mcp",
                    mock_user,
                    {"type": "bearer_token"},
                    "req-123"
                )
                assert result == mock_server
        
        @pytest.mark.asyncio
        async def test_url_fetch_failure(self, service, mock_user):
            """Test registration with URL fetch failure."""
            
            with patch.object(service, '_load_specification_from_url', 
                            new_callable=AsyncMock, side_effect=Exception("Fetch failed")):
                
                with pytest.raises(Exception, match="Fetch failed"):
                    await service.register_from_url(
                        spec_url="https://example.com/spec.json",
                        endpoint_url="https://example.com/mcp",
                        current_user=mock_user
                    )
    
    class TestValidateSpecification:
        """Test _validate_specification method."""
        
        def test_valid_specification(self, service, mock_specification):
            """Test validation of valid specification."""
            # Should not raise any exception
            service._validate_specification(mock_specification)
        
        # Note: Pydantic validation tests are handled in test_mcp_protocol.py
        # These tests are redundant since validation happens at the schema level
    
    class TestLoadSpecificationFromUrl:
        """Test _load_specification_from_url method."""
        
        @pytest.mark.asyncio
        async def test_successful_load(self, service):
            """Test successful specification loading from URL."""
            
            spec_data = {
                "server_info": {
                    "name": "test-server",
                    "version": "1.0.0"
                },
                "tools": [],
                "resources": []
            }
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = MagicMock()
                mock_response.json.return_value = spec_data
                mock_response.raise_for_status.return_value = None
                mock_client.get.return_value = mock_response
                
                result = await service._load_specification_from_url("https://example.com/spec.json")
                
                assert isinstance(result, McpServerSpecification)
                assert result.server_info.name == "test-server"
                assert result.server_info.version == "1.0.0"
        
        @pytest.mark.asyncio
        async def test_http_error(self, service):
            """Test specification loading with HTTP error."""
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = MagicMock()
                mock_response.raise_for_status.side_effect = Exception("HTTP Error")
                mock_client.get.return_value = mock_response
                
                with pytest.raises(Exception, match="HTTP Error"):
                    await service._load_specification_from_url("https://example.com/spec.json")
    
    class TestTestServerConnectivity:
        """Test _test_server_connectivity method."""
        
        @pytest.mark.asyncio
        async def test_successful_connectivity(self, service):
            """Test successful server connectivity."""
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None
                mock_client.get.return_value = mock_response
                
                # Should not raise any exception
                await service._test_server_connectivity(
                    "https://example.com/mcp",
                    {"type": "bearer_token", "token": "secret"}
                )
                
                # Verify health endpoint was called
                mock_client.get.assert_called_with(
                    "https://example.com/mcp/health",
                    headers={"Content-Type": "application/json", "Authorization": "Bearer secret"}
                )
        
        @pytest.mark.asyncio
        async def test_health_endpoint_fallback(self, service):
            """Test connectivity with health endpoint fallback."""
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                            # First call fails (health endpoint)
                mock_response1 = MagicMock()
                mock_response1.raise_for_status.side_effect = httpx.HTTPError("Health endpoint not found")
                
                # Second call succeeds (root endpoint)
                mock_response2 = MagicMock()
                mock_response2.raise_for_status.return_value = None
                
                mock_client.get.side_effect = [mock_response1, mock_response2]
                
                # Should not raise any exception
                await service._test_server_connectivity("https://example.com/mcp")
                
                            # Verify both endpoints were tried
            assert mock_client.get.call_count == 2
            mock_client.get.assert_any_call("https://example.com/mcp/health", headers={'Content-Type': 'application/json'})
            mock_client.get.assert_any_call("https://example.com/mcp/", headers={'Content-Type': 'application/json'})
        
        @pytest.mark.asyncio
        async def test_connectivity_failure(self, service):
            """Test connectivity failure."""
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                # Both calls fail
                mock_response1 = MagicMock()
                mock_response1.raise_for_status.side_effect = httpx.HTTPError("Health endpoint not found")
                
                mock_response2 = MagicMock()
                mock_response2.raise_for_status.side_effect = httpx.HTTPError("Root endpoint not found")
                
                mock_client.get.side_effect = [mock_response1, mock_response2]
                
                with pytest.raises(ValueError, match="Server connectivity test failed"):
                    await service._test_server_connectivity("https://example.com/mcp")
        
        @pytest.mark.asyncio
        async def test_handshake_fallback(self, service, mock_handshake_response):
            """Test handshake with endpoint fallback."""
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                # First call fails (mcp/handshake endpoint)
                mock_response1 = MagicMock()
                mock_response1.raise_for_status.side_effect = httpx.HTTPError("Endpoint not found")
                
                # Second call succeeds (handshake endpoint)
                mock_response2 = MagicMock()
                mock_response2.json.return_value = mock_handshake_response.model_dump()
                mock_response2.raise_for_status.return_value = None
                
                mock_client.post.side_effect = [mock_response1, mock_response2]
                
                result = await service._perform_handshake("https://example.com/mcp")
                
                assert isinstance(result, McpHandshakeResponse)
                
                # Verify both endpoints were tried
                assert mock_client.post.call_count == 2
                mock_client.post.assert_any_call(
                    "https://example.com/mcp/mcp/handshake",
                    headers={"Content-Type": "application/json"},
                    json={
                        "protocol_version": "1.0",
                        "client_info": {
                            "name": "SprintConnect",
                            "version": "1.0.0"
                        }
                    }
                )
                mock_client.post.assert_any_call(
                    "https://example.com/mcp/handshake",
                    headers={"Content-Type": "application/json"},
                    json={
                        "protocol_version": "1.0",
                        "client_info": {
                            "name": "SprintConnect",
                            "version": "1.0.0"
                        }
                    }
                )
        
        @pytest.mark.asyncio
        async def test_handshake_failure_with_minimal_response(self, service):
            """Test handshake failure with minimal response fallback."""
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                # Both calls fail
                mock_response1 = MagicMock()
                mock_response1.raise_for_status.side_effect = httpx.HTTPError("Handshake failed")
                
                mock_response2 = MagicMock()
                mock_response2.raise_for_status.side_effect = httpx.HTTPError("Handshake failed")
                
                mock_client.post.side_effect = [mock_response1, mock_response2]
                
                result = await service._perform_handshake("https://example.com/mcp")
                
                # Should return minimal response
                assert isinstance(result, McpHandshakeResponse)
                assert result.protocol_version == "1.0"
                assert result.server_info.name == "unknown"
                assert result.server_info.version == "1.0.0"
                assert result.capabilities == {}
    
    class TestBuildAuthHeaders:
        """Test _build_auth_headers method."""
        
        def test_no_auth_config(self, service):
            """Test building headers without auth config."""
            headers = service._build_auth_headers(None)
            assert headers == {"Content-Type": "application/json"}
        
        def test_bearer_token_auth(self, service):
            """Test building headers with bearer token auth."""
            auth_config = {
                "type": "bearer_token",
                "token": "secret-token"
            }
            
            headers = service._build_auth_headers(auth_config)
            
            assert headers == {
                "Content-Type": "application/json",
                "Authorization": "Bearer secret-token"
            }
        
        def test_api_key_auth(self, service):
            """Test building headers with API key auth."""
            auth_config = {
                "type": "api_key",
                "api_key": "secret-key",
                "header_name": "X-Custom-Key"
            }
            
            headers = service._build_auth_headers(auth_config)
            
            assert headers == {
                "Content-Type": "application/json",
                "X-Custom-Key": "secret-key"
            }
        
        def test_api_key_auth_default_header(self, service):
            """Test building headers with API key auth using default header."""
            auth_config = {
                "type": "api_key",
                "api_key": "secret-key"
            }
            
            headers = service._build_auth_headers(auth_config)
            
            assert headers == {
                "Content-Type": "application/json",
                "X-API-Key": "secret-key"
            }
    
    class TestCreateServerRecord:
        """Test _create_server_record method."""
        
        def test_successful_server_creation(self, service, mock_user, mock_specification):
            """Test successful server record creation."""
            
            with patch.object(service.db, 'query') as mock_query, \
                 patch.object(service.db, 'add') as mock_add, \
                 patch.object(service.db, 'flush') as mock_flush:
                
                # Mock existing server query (no duplicates)
                mock_query.return_value.filter.return_value.first.return_value = None
                
                result = service._create_server_record(
                    mock_specification,
                    "https://example.com/mcp",
                    mock_user,
                    {"type": "bearer_token", "token": "secret"}
                )
                
                assert isinstance(result, McpServer)
                mock_add.assert_called()
                mock_flush.assert_called()
        
        def test_duplicate_server_name(self, service, mock_user, mock_specification):
            """Test server creation with duplicate name."""
            
            with patch.object(service.db, 'query') as mock_query:
                # Mock existing server query (duplicate found)
                mock_query.return_value.filter.return_value.first.return_value = MagicMock()
                
                with pytest.raises(ValueError, match="already exists"):
                    service._create_server_record(
                        mock_specification,
                        "https://example.com/mcp",
                        mock_user
                    )
    
    class TestStoreCapabilities:
        """Test _store_capabilities method."""
        
        def test_store_tools_and_resources(self, service, mock_specification, mock_handshake_response):
            """Test storing tools and resources from specification."""
            
            mock_server = MagicMock()
            mock_server.id = "server-123"
            
            with patch.object(service.db, 'add') as mock_add:
                service._store_capabilities(mock_server, mock_specification, mock_handshake_response)
                
                # Should add capabilities for tools and resources
                # 1 tool + 1 resource + 2 handshake capabilities = 4 total
                assert mock_add.call_count == 4
        
        def test_store_handshake_capabilities(self, service, mock_handshake_response):
            """Test storing capabilities from handshake response."""
            
            mock_server = MagicMock()
            mock_server.id = "server-123"
            
            with patch.object(service.db, 'add') as mock_add:
                service._store_capabilities(mock_server, None, mock_handshake_response)
                
                # Should add capabilities from handshake
                assert mock_add.call_count == 2  # 2 handshake capabilities
    
    class TestDiscoverCapabilities:
        """Test discover_capabilities method."""
        
        @pytest.mark.asyncio
        async def test_successful_discovery(self, service, mock_user, mock_handshake_response):
            """Test successful capability discovery."""
            
            mock_server = MagicMock()
            mock_server.id = "server-123"
            mock_server.base_url = "https://example.com/mcp"
            
            with patch.object(service.db, 'query') as mock_query, \
                 patch.object(service, '_perform_handshake',
                            new_callable=AsyncMock, return_value=mock_handshake_response) as mock_handshake, \
                 patch.object(service, '_store_capabilities', new_callable=MagicMock) as mock_store, \
                 patch.object(service.db, 'commit') as mock_commit:
                
                # Create separate mock query chains for different queries
                mock_server_query = MagicMock()
                mock_server_query.filter.return_value.first.return_value = mock_server
                
                mock_credential_query = MagicMock()
                mock_credential_query.filter.return_value.first.return_value = None
                
                mock_capabilities_query = MagicMock()
                mock_capabilities_query.filter.return_value.all.return_value = []
                
                # Set up the query chain to return different mocks for different calls
                mock_query.side_effect = [mock_server_query, mock_credential_query, mock_capabilities_query]
                
                result = await service.discover_capabilities("server-123", mock_user)
                
                mock_handshake.assert_called_once_with("https://example.com/mcp", None)
                mock_store.assert_called_once()
                mock_commit.assert_called_once()
                
                assert result.server_id == "server-123"
                assert len(result.capabilities) == 2
        
        @pytest.mark.asyncio
        async def test_server_not_found(self, service, mock_user):
            """Test discovery with non-existent server."""
            
            with patch.object(service.db, 'query') as mock_query:
                # Mock server query (server not found)
                mock_query.return_value.filter.return_value.first.return_value = None
                
                with pytest.raises(ValueError, match="Server not found"):
                    await service.discover_capabilities("server-123", mock_user)
        
        @pytest.mark.asyncio
        async def test_discovery_failure(self, service, mock_user):
            """Test discovery failure."""
            
            mock_server = MagicMock()
            mock_server.id = "server-123"
            mock_server.base_url = "https://example.com/mcp"
            
            with patch.object(service.db, 'query') as mock_query, \
                 patch.object(service, '_perform_handshake', 
                            new_callable=AsyncMock, side_effect=Exception("Discovery failed")), \
                 patch.object(service.db, 'rollback') as mock_rollback:
                
                # Mock server query
                mock_query.return_value.filter.return_value.first.return_value = mock_server
                
                with pytest.raises(Exception, match="Discovery failed"):
                    await service.discover_capabilities("server-123", mock_user)
                
                mock_rollback.assert_called_once()

class TestMcpRegistrationServiceIntegration:
    """Integration tests for MCP Registration Service."""
    
    @pytest.mark.asyncio
    async def test_complete_registration_workflow(self, db_session):
        """Test complete registration workflow."""
        
        # Create test user and organization
        org = Organization(
            id=uuid.uuid4(),
            name="Test Org",
            slug="test-org",
            settings={},
            subscription_tier="free",
            status="active"
        )
        db_session.add(org)
        
        user = User(
            id=uuid.uuid4(),
            org_id=org.id,
            email="test@example.com",
            name="Test User",
            roles=["admin"],
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create service
        service = McpRegistrationService(db_session)
        
        # Create specification
        spec = McpServerSpecification(
            server_info=McpServerInfo(
                name="integration-test-server",
                version="1.0.0",
                description="Integration test server"
            ),
            tools=[
                McpTool(
                    name="integration_tool",
                    description="Integration test tool",
                    input_schema=McpToolParameter(type="object")
                )
            ]
        )
        
        # Mock external dependencies
        with patch.object(service, '_test_server_connectivity', new_callable=AsyncMock), \
             patch.object(service, '_perform_handshake', new_callable=AsyncMock) as mock_handshake:
            
            mock_handshake.return_value = McpHandshakeResponse(
                protocol_version="1.0",
                server_info=McpServerInfo(name="test", version="1.0.0"),
                capabilities={}
            )
            
            # Perform registration
            server = await service.register_from_specification(
                spec=spec,
                endpoint_url="https://example.com/mcp",
                current_user=user,
                request_id="integration-test"
            )
            
            # Verify server was created
            assert server.name == "integration-test-server"
            assert server.org_id == org.id
            assert server.owner_user_id == user.id
            
            # Verify capabilities were stored
            capabilities = db_session.query(McpCapability).filter(
                McpCapability.mcp_server_id == server.id
            ).all()
            
            assert len(capabilities) == 1
            assert capabilities[0].name == "integration_tool"
