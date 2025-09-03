"""Comprehensive tests for MCP Protocol schemas and validation."""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError

from app.schemas.mcp_protocol import (
    McpResourceType, McpToolType, McpResourceMetadata, McpResource,
    McpToolParameter, McpTool, McpServerInfo, McpServerSpecification,
    McpServerRegistration, McpCapabilityDiscovery, McpServerStatus,
    McpHandshakeRequest, McpHandshakeResponse
)

pytestmark = pytest.mark.mcp_protocol


class TestMcpResourceType:
    """Test MCP resource type enum."""
    
    def test_resource_type_values(self):
        """Test resource type enum values."""
        assert McpResourceType.FILE == "file"
        assert McpResourceType.DIRECTORY == "directory"
    
    def test_resource_type_validation(self):
        """Test resource type validation."""
        resource = McpResource(
            uri="file:///test.txt",
            name="test.txt",
            resource_type=McpResourceType.FILE
        )
        assert resource.resource_type == McpResourceType.FILE


class TestMcpToolType:
    """Test MCP tool type enum."""
    
    def test_tool_type_values(self):
        """Test tool type enum values."""
        assert McpToolType.FUNCTION == "function"
        assert McpToolType.PROCEDURE == "procedure"
    
    def test_tool_type_default(self):
        """Test tool type default value."""
        tool = McpTool(
            name="test_tool",
            input_schema=McpToolParameter(type="object")
        )
        assert tool.tool_type == McpToolType.FUNCTION


class TestMcpResourceMetadata:
    """Test MCP resource metadata."""
    
    def test_valid_resource_metadata(self):
        """Test valid resource metadata."""
        metadata = McpResourceMetadata(
            name="test.txt",
            description="Test file",
            mime_type="text/plain",
            size=1024,
            created="2024-01-01T00:00:00Z",
            modified="2024-01-01T00:00:00Z"
        )
        
        assert metadata.name == "test.txt"
        assert metadata.description == "Test file"
        assert metadata.mime_type == "text/plain"
        assert metadata.size == 1024
        assert metadata.created == "2024-01-01T00:00:00Z"
        assert metadata.modified == "2024-01-01T00:00:00Z"
    
    def test_minimal_resource_metadata(self):
        """Test minimal resource metadata."""
        metadata = McpResourceMetadata(name="test.txt")
        assert metadata.name == "test.txt"
        assert metadata.description is None
        assert metadata.mime_type is None


class TestMcpResource:
    """Test MCP resource validation."""
    
    def test_valid_file_resource(self):
        """Test valid file resource."""
        resource = McpResource(
            uri="file:///test.txt",
            name="test.txt",
            description="Test file",
            resource_type=McpResourceType.FILE,
            metadata=McpResourceMetadata(name="test.txt")
        )
        
        assert resource.uri == "file:///test.txt"
        assert resource.name == "test.txt"
        assert resource.resource_type == McpResourceType.FILE
    
    def test_valid_http_resource(self):
        """Test valid HTTP resource."""
        resource = McpResource(
            uri="https://example.com/data.json",
            name="data.json",
            resource_type=McpResourceType.FILE
        )
        
        assert resource.uri == "https://example.com/data.json"
        assert resource.resource_type == McpResourceType.FILE
    
    def test_valid_directory_resource(self):
        """Test valid directory resource."""
        resource = McpResource(
            uri="file:///test-dir",
            name="test-dir",
            resource_type=McpResourceType.DIRECTORY
        )
        
        assert resource.resource_type == McpResourceType.DIRECTORY
    
    def test_invalid_resource_uri(self):
        """Test invalid resource URI."""
        with pytest.raises(ValidationError) as exc_info:
            McpResource(
                uri="invalid-uri",
                name="test",
                resource_type=McpResourceType.FILE
            )
        
        errors = exc_info.value.errors()
        assert any("uri" in str(error) for error in errors)
    
    def test_ftp_resource_uri_not_allowed(self):
        """Test that FTP URIs are not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            McpResource(
                uri="ftp://example.com/file.txt",
                name="file.txt",
                resource_type=McpResourceType.FILE
            )
        
        errors = exc_info.value.errors()
        assert any("uri" in str(error) for error in errors)


class TestMcpToolParameter:
    """Test MCP tool parameter validation."""
    
    def test_valid_string_parameter(self):
        """Test valid string parameter."""
        param = McpToolParameter(
            type="string",
            description="A string parameter"
        )
        
        assert param.type == "string"
        assert param.description == "A string parameter"
    
    def test_valid_object_parameter(self):
        """Test valid object parameter."""
        param = McpToolParameter(
            type="object",
            description="An object parameter",
            properties={
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            required=["name"]
        )
        
        assert param.type == "object"
        assert param.properties["name"]["type"] == "string"
        assert param.required == ["name"]
    
    def test_valid_array_parameter(self):
        """Test valid array parameter."""
        param = McpToolParameter(
            type="array",
            description="An array parameter",
            items={"type": "string"}
        )
        
        assert param.type == "array"
        assert param.items["type"] == "string"
    
    def test_valid_enum_parameter(self):
        """Test valid enum parameter."""
        param = McpToolParameter(
            type="string",
            description="An enum parameter",
            enum=["option1", "option2", "option3"]
        )
        
        assert param.type == "string"
        assert param.enum == ["option1", "option2", "option3"]


class TestMcpTool:
    """Test MCP tool validation."""
    
    def test_valid_function_tool(self):
        """Test valid function tool."""
        tool = McpTool(
            name="get_weather",
            description="Get weather information",
            input_schema=McpToolParameter(
                type="object",
                properties={
                    "location": {"type": "string"}
                },
                required=["location"]
            ),
            tool_type=McpToolType.FUNCTION
        )
        
        assert tool.name == "get_weather"
        assert tool.description == "Get weather information"
        assert tool.tool_type == McpToolType.FUNCTION
        assert tool.input_schema.type == "object"
    
    def test_valid_procedure_tool(self):
        """Test valid procedure tool."""
        tool = McpTool(
            name="update_data",
            description="Update data",
            input_schema=McpToolParameter(type="object"),
            tool_type=McpToolType.PROCEDURE
        )
        
        assert tool.tool_type == McpToolType.PROCEDURE
    
    def test_empty_tool_name(self):
        """Test empty tool name validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpTool(
                name="",
                input_schema=McpToolParameter(type="object")
            )
        
        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)
    
    def test_invalid_tool_name(self):
        """Test invalid tool name validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpTool(
                name="invalid tool name!",
                input_schema=McpToolParameter(type="object")
            )
        
        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)
    
    def test_valid_tool_name_with_hyphens(self):
        """Test valid tool name with hyphens."""
        tool = McpTool(
            name="get-weather-data",
            input_schema=McpToolParameter(type="object")
        )
        
        assert tool.name == "get-weather-data"
    
    def test_valid_tool_name_with_underscores(self):
        """Test valid tool name with underscores."""
        tool = McpTool(
            name="get_weather_data",
            input_schema=McpToolParameter(type="object")
        )
        
        assert tool.name == "get_weather_data"


class TestMcpServerInfo:
    """Test MCP server info validation."""
    
    def test_valid_server_info(self):
        """Test valid server info."""
        server_info = McpServerInfo(
            name="weather-server",
            version="1.0.0",
            description="Weather information server",
            capabilities={"supports_websockets": True}
        )
        
        assert server_info.name == "weather-server"
        assert server_info.version == "1.0.0"
        assert server_info.description == "Weather information server"
        assert server_info.capabilities["supports_websockets"] is True
    
    def test_minimal_server_info(self):
        """Test minimal server info."""
        server_info = McpServerInfo(
            name="minimal-server",
            version="1.0.0"
        )
        
        assert server_info.name == "minimal-server"
        assert server_info.version == "1.0.0"
        assert server_info.description is None
    
    def test_empty_server_name(self):
        """Test empty server name validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerInfo(
                name="",
                version="1.0.0"
            )
        
        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)
    
    def test_invalid_server_name(self):
        """Test invalid server name validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerInfo(
                name="invalid server name!",
                version="1.0.0"
            )
        
        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)
    
    def test_empty_version(self):
        """Test empty version validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerInfo(
                name="test-server",
                version=""
            )
        
        errors = exc_info.value.errors()
        assert any("version" in str(error) for error in errors)
    
    def test_invalid_version_format(self):
        """Test invalid version format validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerInfo(
                name="test-server",
                version="1"
            )
        
        errors = exc_info.value.errors()
        assert any("version" in str(error) for error in errors)
    
    def test_valid_version_formats(self):
        """Test valid version formats."""
        # Test various valid version formats
        valid_versions = ["1.0", "1.0.0", "2.1.3", "10.20.30"]
        
        for version in valid_versions:
            server_info = McpServerInfo(
                name="test-server",
                version=version
            )
            assert server_info.version == version


class TestMcpServerSpecification:
    """Test MCP server specification validation."""
    
    def test_valid_specification(self):
        """Test valid server specification."""
        spec = McpServerSpecification(
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0",
                description="Test server"
            ),
            tools=[
                McpTool(
                    name="test_tool",
                    input_schema=McpToolParameter(type="object")
                )
            ],
            resources=[
                McpResource(
                    uri="file:///test.txt",
                    name="test.txt",
                    resource_type=McpResourceType.FILE
                )
            ],
            schemas={"custom_schema": {"type": "object"}}
        )
        
        assert spec.server_info.name == "test-server"
        assert len(spec.tools) == 1
        assert len(spec.resources) == 1
        assert "custom_schema" in spec.schemas
    
    def test_minimal_specification(self):
        """Test minimal server specification."""
        spec = McpServerSpecification(
            server_info=McpServerInfo(
                name="minimal-server",
                version="1.0.0"
            )
        )
        
        assert spec.server_info.name == "minimal-server"
        assert spec.tools == []
        assert spec.resources == []
        assert spec.schemas == {}
    
    def test_duplicate_tool_names(self):
        """Test duplicate tool names validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerSpecification(
                server_info=McpServerInfo(
                    name="test-server",
                    version="1.0.0"
                ),
                tools=[
                    McpTool(
                        name="duplicate_tool",
                        input_schema=McpToolParameter(type="object")
                    ),
                    McpTool(
                        name="duplicate_tool",
                        input_schema=McpToolParameter(type="object")
                    )
                ]
            )
        
        errors = exc_info.value.errors()
        assert any("unique" in str(error) for error in errors)
    
    def test_duplicate_resource_uris(self):
        """Test duplicate resource URIs validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerSpecification(
                server_info=McpServerInfo(
                    name="test-server",
                    version="1.0.0"
                ),
                resources=[
                    McpResource(
                        uri="file:///duplicate.txt",
                        name="file1.txt",
                        resource_type=McpResourceType.FILE
                    ),
                    McpResource(
                        uri="file:///duplicate.txt",
                        name="file2.txt",
                        resource_type=McpResourceType.FILE
                    )
                ]
            )
        
        errors = exc_info.value.errors()
        assert any("unique" in str(error) for error in errors)
    
    def test_large_schemas(self):
        """Test large schemas validation."""
        # Create a large schema that exceeds 64KB
        large_schema = {"data": "x" * 70000}
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerSpecification(
                server_info=McpServerInfo(
                    name="test-server",
                    version="1.0.0"
                ),
                schemas=large_schema
            )
        
        errors = exc_info.value.errors()
        assert any("64KB" in str(error) for error in errors)


class TestMcpServerRegistration:
    """Test MCP server registration validation."""
    
    def test_valid_registration(self):
        """Test valid server registration."""
        registration = McpServerRegistration(
            specification=McpServerSpecification(
                server_info=McpServerInfo(
                    name="test-server",
                    version="1.0.0"
                )
            ),
            endpoint_url="https://example.com/mcp",
            auth_config={
                "type": "bearer_token",
                "token": "secret-token"
            },
            metadata={"environment": "production"}
        )
        
        assert registration.endpoint_url == "https://example.com/mcp"
        assert registration.auth_config["type"] == "bearer_token"
        assert registration.metadata["environment"] == "production"
    
    def test_invalid_endpoint_url(self):
        """Test invalid endpoint URL validation."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerRegistration(
                specification=McpServerSpecification(
                    server_info=McpServerInfo(
                        name="test-server",
                        version="1.0.0"
                    )
                ),
                endpoint_url="invalid-url"
            )
        
        errors = exc_info.value.errors()
        assert any("endpoint_url" in str(error) for error in errors)
    
    def test_valid_endpoint_urls(self):
        """Test valid endpoint URL formats."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "ws://example.com",
            "wss://example.com"
        ]
        
        for url in valid_urls:
            registration = McpServerRegistration(
                specification=McpServerSpecification(
                    server_info=McpServerInfo(
                        name="test-server",
                        version="1.0.0"
                    )
                ),
                endpoint_url=url
            )
            assert registration.endpoint_url == url
    
    def test_large_metadata(self):
        """Test large metadata validation."""
        # Create large metadata that exceeds 32KB
        large_metadata = {"data": "x" * 35000}
        
        with pytest.raises(ValidationError) as exc_info:
            McpServerRegistration(
                specification=McpServerSpecification(
                    server_info=McpServerInfo(
                        name="test-server",
                        version="1.0.0"
                    )
                ),
                endpoint_url="https://example.com",
                metadata=large_metadata
            )
        
        errors = exc_info.value.errors()
        assert any("32KB" in str(error) for error in errors)


class TestMcpCapabilityDiscovery:
    """Test MCP capability discovery validation."""
    
    def test_valid_discovery_result(self):
        """Test valid capability discovery result."""
        discovery = McpCapabilityDiscovery(
            server_id="server-123",
            discovered_at="2024-01-01T00:00:00Z",
            capabilities={
                "tool1": {"type": "function"},
                "tool2": {"type": "procedure"}
            },
            resources=[
                McpResource(
                    uri="file:///test.txt",
                    name="test.txt",
                    resource_type=McpResourceType.FILE
                )
            ],
            tools=[
                McpTool(
                    name="test_tool",
                    input_schema=McpToolParameter(type="object")
                )
            ],
            errors=["Connection timeout"],
            warnings=["Deprecated API version"]
        )
        
        assert discovery.server_id == "server-123"
        assert len(discovery.capabilities) == 2
        assert len(discovery.resources) == 1
        assert len(discovery.tools) == 1
        assert len(discovery.errors) == 1
        assert len(discovery.warnings) == 1


class TestMcpServerStatus:
    """Test MCP server status validation."""
    
    def test_valid_server_status(self):
        """Test valid server status."""
        status = McpServerStatus(
            server_id="server-123",
            status="active",
            health="healthy",
            last_check="2024-01-01T00:00:00Z",
            capabilities_count=5,
            resources_count=3,
            tools_count=2
        )
        
        assert status.server_id == "server-123"
        assert status.status == "active"
        assert status.health == "healthy"
        assert status.capabilities_count == 5
        assert status.resources_count == 3
        assert status.tools_count == 2


class TestMcpHandshakeRequest:
    """Test MCP handshake request validation."""
    
    def test_valid_handshake_request(self):
        """Test valid handshake request."""
        request = McpHandshakeRequest(
            protocol_version="1.0",
            client_info={
                "name": "SprintConnect",
                "version": "1.0.0"
            }
        )
        
        assert request.protocol_version == "1.0"
        assert request.client_info["name"] == "SprintConnect"


class TestMcpHandshakeResponse:
    """Test MCP handshake response validation."""
    
    def test_valid_handshake_response(self):
        """Test valid handshake response."""
        response = McpHandshakeResponse(
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
        
        assert response.protocol_version == "1.0"
        assert response.server_info.name == "test-server"
        assert response.capabilities["supports_websockets"] is True


class TestMcpProtocolIntegration:
    """Integration tests for MCP protocol components."""
    
    def test_complete_server_specification_workflow(self):
        """Test complete server specification workflow."""
        # Create server info
        server_info = McpServerInfo(
            name="weather-server",
            version="1.0.0",
            description="Weather information provider"
        )
        
        # Create tools
        tools = [
            McpTool(
                name="get_current_weather",
                description="Get current weather for a location",
                input_schema=McpToolParameter(
                    type="object",
                    properties={
                        "location": {"type": "string"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    required=["location"]
                )
            ),
            McpTool(
                name="get_forecast",
                description="Get weather forecast",
                input_schema=McpToolParameter(
                    type="object",
                    properties={
                        "location": {"type": "string"},
                        "days": {"type": "integer", "minimum": 1, "maximum": 7}
                    },
                    required=["location"]
                )
            )
        ]
        
        # Create resources
        resources = [
            McpResource(
                uri="file:///weather-data/current",
                name="current_weather_data",
                description="Current weather data",
                resource_type=McpResourceType.FILE,
                metadata=McpResourceMetadata(
                    name="current_weather_data",
                    mime_type="application/json",
                    size=1024
                )
            )
        ]
        
        # Create specification
        spec = McpServerSpecification(
            server_info=server_info,
            tools=tools,
            resources=resources,
            schemas={
                "WeatherData": {
                    "type": "object",
                    "properties": {
                        "temperature": {"type": "number"},
                        "humidity": {"type": "number"},
                        "description": {"type": "string"}
                    }
                }
            }
        )
        
        # Create registration
        registration = McpServerRegistration(
            specification=spec,
            endpoint_url="https://weather-mcp.example.com",
            auth_config={
                "type": "bearer_token",
                "token": "weather-api-token"
            },
            metadata={
                "environment": "production",
                "region": "us-east-1"
            }
        )
        
        # Validate the complete workflow
        assert registration.specification.server_info.name == "weather-server"
        assert len(registration.specification.tools) == 2
        assert len(registration.specification.resources) == 1
        assert registration.endpoint_url == "https://weather-mcp.example.com"
        assert registration.auth_config["type"] == "bearer_token"
        assert registration.metadata["environment"] == "production"
    
    def test_specification_serialization(self):
        """Test specification serialization and deserialization."""
        spec = McpServerSpecification(
            server_info=McpServerInfo(
                name="test-server",
                version="1.0.0"
            ),
            tools=[
                McpTool(
                    name="test_tool",
                    input_schema=McpToolParameter(type="object")
                )
            ]
        )
        
        # Serialize to dict
        spec_dict = spec.model_dump()
        
        # Deserialize from dict
        spec_recreated = McpServerSpecification(**spec_dict)
        
        assert spec_recreated.server_info.name == spec.server_info.name
        assert spec_recreated.server_info.version == spec.server_info.version
        assert len(spec_recreated.tools) == len(spec.tools)
        assert spec_recreated.tools[0].name == spec.tools[0].name
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        spec = McpServerSpecification(
            server_info=McpServerInfo(
                name="json-test-server",
                version="1.0.0"
            )
        )
        
        # Serialize to JSON
        spec_json = spec.model_dump_json()
        
        # Deserialize from JSON
        spec_recreated = McpServerSpecification.model_validate_json(spec_json)
        
        assert spec_recreated.server_info.name == spec.server_info.name
        assert spec_recreated.server_info.version == spec.server_info.version
