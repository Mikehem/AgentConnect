"""Service layer tests for MCP Servers feature."""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from uuid import uuid4

from app.services.mcp_server import McpServerService
from app.schemas.mcp_server import McpServerCreate, McpServerUpdate, ServerStatus, HealthStatus
from app.models.mcp_server import McpServer

pytestmark = pytest.mark.service


class TestMcpServerServiceCreate:
    """Test MCP server creation service methods."""

    def test_create_server_success(self, db_session, sample_user, valid_server_data):
        """Test successful server creation."""
        service = McpServerService(db_session)
        
        server_data = McpServerCreate(**valid_server_data)
        server = service.create_server(server_data, sample_user, "test-request-id")
        
        assert server.name == valid_server_data["name"]
        assert server.base_url == valid_server_data["base_url"]
        assert server.environment == valid_server_data["environment"]
        assert server.org_id == sample_user.org_id
        assert server.owner_user_id == sample_user.id
        assert server.status == ServerStatus.PENDING_DISCOVERY.value
        assert server.health_status == HealthStatus.UNKNOWN.value

    def test_create_server_duplicate_name(self, db_session, sample_user, sample_mcp_server, valid_server_data):
        """Test server creation with duplicate name in same environment."""
        service = McpServerService(db_session)
        
        # Try to create server with same name and environment
        duplicate_data = valid_server_data.copy()
        duplicate_data["name"] = sample_mcp_server.name
        duplicate_data["environment"] = sample_mcp_server.environment
        
        server_data = McpServerCreate(**duplicate_data)
        
        with pytest.raises(HTTPException, match="already exists"):
            service.create_server(server_data, sample_user, "test-request-id")

    def test_create_server_different_environment(self, db_session, sample_user, sample_mcp_server, valid_server_data):
        """Test creating server with same name but different environment."""
        service = McpServerService(db_session)
        
        # Create server with same name but different environment
        different_env_data = valid_server_data.copy()
        different_env_data["name"] = sample_mcp_server.name
        different_env_data["environment"] = "production"
        
        server_data = McpServerCreate(**different_env_data)
        server = service.create_server(server_data, sample_user, "test-request-id")
        
        assert server.name == sample_mcp_server.name
        assert server.environment == "production"

    @patch('app.services.mcp_server.validate_mcp_server_url')
    def test_create_server_url_validation_failure(self, mock_validate, db_session, sample_user, valid_server_data):
        """Test server creation with invalid URL."""
        mock_validate.side_effect = ValueError("URL not allowed")
        service = McpServerService(db_session)
        
        server_data = McpServerCreate(**valid_server_data)
        
        with pytest.raises(HTTPException, match="URL validation failed"):
            service.create_server(server_data, sample_user, "test-request-id")

    @patch('app.services.mcp_server.check_organization_quota')
    def test_create_server_quota_exceeded(self, mock_quota, db_session, sample_user, valid_server_data):
        """Test server creation when organization quota is exceeded."""
        mock_quota.return_value = False
        service = McpServerService(db_session)
        
        server_data = McpServerCreate(**valid_server_data)
        
        with pytest.raises(HTTPException, match="quota exceeded"):
            service.create_server(server_data, sample_user, "test-request-id")


class TestMcpServerServiceGet:
    """Test MCP server retrieval service methods."""

    def test_get_server_success(self, db_session, sample_mcp_server, sample_user):
        """Test successful server retrieval."""
        service = McpServerService(db_session)
        
        server = service.get_server(sample_mcp_server.id, sample_user)
        
        assert server.id == sample_mcp_server.id
        assert server.name == sample_mcp_server.name

    def test_get_server_not_found(self, db_session, sample_user):
        """Test server retrieval with non-existent ID."""
        service = McpServerService(db_session)
        
        with pytest.raises(HTTPException, match="not found"):
            service.get_server(uuid4(), sample_user)

    def test_get_server_deleted(self, db_session, sample_mcp_server, sample_user):
        """Test server retrieval of deleted server."""
        service = McpServerService(db_session)
        
        # Soft delete the server
        from datetime import datetime, timezone
        sample_mcp_server.deleted_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        db_session.commit()
        
        with pytest.raises(HTTPException, match="not found"):
            service.get_server(sample_mcp_server.id, sample_user)


class TestMcpServerServiceList:
    """Test MCP server listing service methods."""

    def test_list_servers_success(self, db_session, sample_user, sample_mcp_server):
        """Test successful server listing."""
        service = McpServerService(db_session)
        
        result = service.list_servers(sample_user)
        servers = result.servers
        total = result.total

        assert len(servers) >= 1
        assert total >= 1
        assert any(server.id == str(sample_mcp_server.id) for server in servers)

    def test_list_servers_empty(self, db_session, sample_user):
        """Test server listing with no servers."""
        service = McpServerService(db_session)
        
        result = service.list_servers(sample_user)
        servers = result.servers
        total = result.total
        
        assert len(servers) == 0
        assert total == 0

    def test_list_servers_with_filters(self, db_session, sample_user, sample_mcp_server):
        """Test server listing with filters."""
        service = McpServerService(db_session)
        
        result = service.list_servers(
            sample_user,
            environment=sample_mcp_server.environment,
            status=sample_mcp_server.status
        )
        servers = result.servers
        total = result.total
        
        assert len(servers) >= 1
        assert all(server.environment == sample_mcp_server.environment for server in servers)
        assert all(server.status == sample_mcp_server.status for server in servers)


class TestMcpServerServiceUpdate:
    """Test MCP server update service methods."""

    def test_update_server_success(self, db_session, sample_mcp_server, sample_user):
        """Test successful server update."""
        service = McpServerService(db_session)
        
        update_data = McpServerUpdate(
            description="Updated description",
            tags=["updated", "test"]
        )
        
        server = service.update_server(sample_mcp_server.id, update_data, sample_user, "test-request-id")
        
        assert server.description == "Updated description"
        assert server.tags == ["updated", "test"]

    def test_update_server_not_found(self, db_session, sample_user):
        """Test server update with non-existent ID."""
        service = McpServerService(db_session)
        
        update_data = McpServerUpdate(description="Updated description")
        
        with pytest.raises(HTTPException, match="not found"):
            service.update_server(uuid4(), update_data, sample_user, "test-request-id")

    def test_update_server_partial_update(self, db_session, sample_mcp_server, sample_user):
        """Test partial server update."""
        service = McpServerService(db_session)
        
        original_description = sample_mcp_server.description
        update_data = McpServerUpdate(tags=["new", "tags"])
        
        server = service.update_server(sample_mcp_server.id, update_data, sample_user, "test-request-id")
        
        assert server.description == original_description  # Unchanged
        assert server.tags == ["new", "tags"]  # Updated


class TestMcpServerServiceDelete:
    """Test MCP server deletion service methods."""

    def test_delete_server_success(self, db_session, sample_mcp_server, sample_user):
        """Test successful server deletion."""
        service = McpServerService(db_session)
        
        result = service.delete_server(sample_mcp_server.id, sample_user, "test-request-id")
        
        assert result["message"] == "MCP server deleted successfully"
        assert result["deleted_at"] is not None
        
        # Verify soft delete
        db_session.refresh(sample_mcp_server)
        assert sample_mcp_server.deleted_at is not None

    def test_delete_server_not_found(self, db_session, sample_user):
        """Test server deletion with non-existent ID."""
        service = McpServerService(db_session)
        
        with pytest.raises(HTTPException, match="not found"):
            service.delete_server(uuid4(), sample_user, "test-request-id")

    def test_delete_server_already_deleted(self, db_session, sample_mcp_server, sample_user):
        """Test deletion of already deleted server."""
        service = McpServerService(db_session)
        
        # Soft delete the server first
        from datetime import datetime, timezone
        sample_mcp_server.deleted_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        db_session.commit()
        
        with pytest.raises(HTTPException, match="not found"):
            service.delete_server(sample_mcp_server.id, sample_user, "test-request-id")


class TestMcpServerServiceSecurity:
    """Test MCP server service security features."""

    @patch('app.services.mcp_server.validate_mcp_server_url')
    def test_create_server_ssrf_protection(self, mock_validate, db_session, sample_user, valid_server_data):
        """Test SSRF protection during server creation."""
        mock_validate.side_effect = ValueError("SSRF protection blocked")
        service = McpServerService(db_session)
        
        server_data = McpServerCreate(**valid_server_data)
        
        with pytest.raises(HTTPException, match="URL validation failed"):
            service.create_server(server_data, sample_user, "test-request-id")

    def test_create_server_metadata_sanitization(self, db_session, sample_user, valid_server_data):
        """Test metadata sanitization during server creation."""
        service = McpServerService(db_session)
        
        # Add potentially malicious metadata
        malicious_data = valid_server_data.copy()
        malicious_data["metadata"] = {
            "script": "<script>alert('xss')</script>",
            "sql": "'; DROP TABLE users; --",
            "normal": "safe_value"
        }
        
        server_data = McpServerCreate(**malicious_data)
        server = service.create_server(server_data, sample_user, "test-request-id")
        
        # Metadata should be sanitized (only sensitive keys are redacted)
        assert server.server_metadata.get("script") == "<script>alert('xss')</script>"
        assert server.server_metadata.get("sql") == "'; DROP TABLE users; --"
        assert server.server_metadata.get("normal") == "safe_value"

    @patch('app.services.mcp_server.validate_vault_path')
    def test_create_server_vault_path_validation(self, mock_validate, db_session, sample_user, valid_server_data):
        """Test Vault path validation during server creation."""
        mock_validate.side_effect = ValueError("Invalid Vault path")
        service = McpServerService(db_session)
        
        # Add auth config with Vault path
        auth_data = valid_server_data.copy()
        auth_data["auth_config"] = {
            "type": "bearer_token",
            "vault_path": "invalid/path"
        }
        
        server_data = McpServerCreate(**auth_data)
        
        with pytest.raises(HTTPException, match="Invalid vault path format"):
            service.create_server(server_data, sample_user, "test-request-id")
