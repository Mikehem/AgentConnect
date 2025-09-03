"""Schema validation tests for MCP Servers feature."""

import pytest
from pydantic import ValidationError

from app.schemas.mcp_server import (
    Environment, CredentialType, ServerStatus, HealthStatus,
    AuthConfig, HealthCheckConfig, McpServerCreate, McpServerUpdate,
    McpServerResponse, McpServerListResponse
)

pytestmark = pytest.mark.schema


class TestMcpServerCreateSchema:
    """Test MCP server creation schema validation."""

    def test_valid_server_data(self):
        """Test valid server creation data."""
        data = {
            "name": "test-server",
            "description": "Test MCP server",
            "environment": "development",
            "base_url": "https://api.openai.com",
            "tags": ["test", "mcp"],
            "metadata": {"version": "1.0.0"},
            "auto_discover": True
        }
        
        server = McpServerCreate(**data)
        
        assert server.name == "test-server"
        assert server.description == "Test MCP server"
        assert server.environment == Environment.DEVELOPMENT
        assert server.base_url == "https://api.openai.com"
        assert server.tags == ["test", "mcp"]
        assert server.metadata == {"version": "1.0.0"}
        assert server.auto_discover is True

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {
            "description": "Test MCP server",
            "environment": "development"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)
        assert any(error["loc"] == ("base_url",) for error in errors)

    def test_invalid_environment(self):
        """Test validation with invalid environment."""
        data = {
            "name": "test-server",
            "base_url": "https://api.openai.com",
            "environment": "invalid-env"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("environment",) for error in errors)

    def test_invalid_url(self):
        """Test validation with invalid URL."""
        data = {
            "name": "test-server",
            "base_url": "invalid-url",
            "environment": "development"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("base_url",) for error in errors)

    def test_empty_name(self):
        """Test validation with empty name."""
        data = {
            "name": "",
            "base_url": "https://api.openai.com",
            "environment": "development"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_too_long_name(self):
        """Test validation with name too long."""
        data = {
            "name": "a" * 256,  # Too long
            "base_url": "https://api.openai.com",
            "environment": "development"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_too_many_tags(self):
        """Test validation with too many tags."""
        data = {
            "name": "test-server",
            "base_url": "https://api.openai.com",
            "environment": "development",
            "tags": [f"tag{i}" for i in range(25)]  # Too many tags
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("tags",) for error in errors)

    def test_auth_config_validation(self):
        """Test validation with auth config."""
        data = {
            "name": "test-server",
            "base_url": "https://api.openai.com",
            "environment": "development",
            "auth_config": {
                "type": "bearer_token",
                "vault_path": "mcp/credentials/test-server"
            }
        }
        
        server = McpServerCreate(**data)
        
        assert server.auth_config.type == CredentialType.BEARER_TOKEN
        assert server.auth_config.vault_path == "mcp/credentials/test-server"

    def test_invalid_auth_config_type(self):
        """Test validation with invalid auth config type."""
        data = {
            "name": "test-server",
            "base_url": "https://api.openai.com",
            "environment": "development",
            "auth_config": {
                "type": "invalid_type",
                "vault_path": "mcp/credentials/test-server"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("auth_config", "type") for error in errors)


class TestMcpServerUpdateSchema:
    """Test MCP server update schema validation."""

    def test_valid_update_data(self):
        """Test valid update data."""
        data = {
            "name": "updated-server",
            "description": "Updated description",
            "tags": ["updated", "test"]
        }
        
        update = McpServerUpdate(**data)
        
        assert update.name == "updated-server"
        assert update.description == "Updated description"
        assert update.tags == ["updated", "test"]

    def test_partial_update(self):
        """Test partial update with only some fields."""
        data = {
            "description": "Updated description"
        }
        
        update = McpServerUpdate(**data)
        
        assert update.description == "Updated description"
        assert update.name is None
        assert update.tags is None

    def test_invalid_update_data(self):
        """Test validation with invalid update data."""
        data = {
            "name": "",  # Empty name
            "base_url": "invalid-url"  # Invalid URL
        }
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerUpdate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)
        assert any(error["loc"] == ("base_url",) for error in errors)


class TestAuthConfigSchema:
    """Test auth config schema validation."""

    def test_valid_bearer_token_config(self):
        """Test valid bearer token config."""
        data = {
            "type": "bearer_token",
            "vault_path": "mcp/credentials/test-server"
        }
        
        config = AuthConfig(**data)
        
        assert config.type == CredentialType.BEARER_TOKEN
        assert config.vault_path == "mcp/credentials/test-server"

    def test_valid_api_key_config(self):
        """Test valid API key config."""
        data = {
            "type": "api_key",
            "vault_path": "mcp/credentials/test-server",
            "header_name": "X-API-Key"
        }
        
        config = AuthConfig(**data)
        
        assert config.type == CredentialType.API_KEY
        assert config.vault_path == "mcp/credentials/test-server"
        assert config.header_name == "X-API-Key"

    def test_invalid_auth_type(self):
        """Test validation with invalid auth type."""
        data = {
            "type": "invalid_type",
            "vault_path": "mcp/credentials/test-server"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("type",) for error in errors)

    def test_missing_vault_path(self):
        """Test validation with missing vault path."""
        data = {
            "type": "bearer_token"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("vault_path",) for error in errors)


class TestHealthCheckConfigSchema:
    """Test health check config schema validation."""

    def test_valid_health_check_config(self):
        """Test valid health check config."""
        data = {
            "enabled": True,
            "interval_seconds": 300,
            "timeout_seconds": 30,
            "endpoint": "/health"
        }
        
        config = HealthCheckConfig(**data)
        
        assert config.enabled is True
        assert config.interval_seconds == 300
        assert config.timeout_seconds == 30
        assert config.endpoint == "/health"

    def test_default_values(self):
        """Test default values for health check config."""
        data = {
            "enabled": True
        }
        
        config = HealthCheckConfig(**data)
        
        assert config.enabled is True
        assert config.interval_seconds == 300  # Default
        assert config.timeout_seconds == 30  # Default
        assert config.endpoint == "/health"  # Default

    def test_invalid_interval(self):
        """Test validation with invalid interval."""
        data = {
            "enabled": True,
            "interval_seconds": 0  # Invalid: must be > 0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            HealthCheckConfig(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("interval_seconds",) for error in errors)

    def test_invalid_timeout(self):
        """Test validation with invalid timeout."""
        data = {
            "enabled": True,
            "timeout_seconds": 0  # Invalid: must be > 0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            HealthCheckConfig(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("timeout_seconds",) for error in errors)


class TestEnumValues:
    """Test enum value validation."""

    def test_environment_enum_values(self):
        """Test environment enum values."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"

    def test_credential_type_enum_values(self):
        """Test credential type enum values."""
        assert CredentialType.BEARER_TOKEN == "bearer_token"
        assert CredentialType.API_KEY == "api_key"
        assert CredentialType.BASIC_AUTH == "basic_auth"

    def test_server_status_enum_values(self):
        """Test server status enum values."""
        assert ServerStatus.ACTIVE == "active"
        assert ServerStatus.INACTIVE == "inactive"
        assert ServerStatus.MAINTENANCE == "maintenance"

    def test_health_status_enum_values(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNKNOWN == "unknown"


class TestSchemaSerialization:
    """Test schema serialization and deserialization."""

    def test_mcp_server_response_serialization(self):
        """Test MCP server response serialization."""
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "org_id": "456e7890-e89b-12d3-a456-426614174000",
            "name": "test-server",
            "description": "Test server",
            "environment": "development",
            "base_url": "https://api.openai.com",
            "ws_url": None,
            "tags": ["test"],
            "server_metadata": {"version": "1.0.0"},
            "owner_user_id": "789e0123-e89b-12d3-a456-426614174000",
            "policy_id": None,
            "status": "active",
            "health_status": "unknown",
            "last_health_check_at": None,
            "last_discovery_at": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "deleted_at": None
        }
        
        response = McpServerResponse(**data)
        
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.name == "test-server"
        assert response.environment == Environment.DEVELOPMENT
        assert response.status == ServerStatus.ACTIVE

    def test_mcp_server_list_response_serialization(self):
        """Test MCP server list response serialization."""
        server_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "org_id": "456e7890-e89b-12d3-a456-426614174000",
            "name": "test-server",
            "description": "Test server",
            "environment": "development",
            "base_url": "https://api.openai.com",
            "ws_url": None,
            "tags": ["test"],
            "server_metadata": {"version": "1.0.0"},
            "owner_user_id": "789e0123-e89b-12d3-a456-426614174000",
            "policy_id": None,
            "status": "active",
            "health_status": "unknown",
            "last_health_check_at": None,
            "last_discovery_at": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "deleted_at": None
        }
        
        data = {
            "servers": [server_data],
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1
        }
        
        response = McpServerListResponse(**data)
        
        assert len(response.servers) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.size == 10
        assert response.pages == 1
        assert response.servers[0].name == "test-server"
