"""MCP Protocol-compliant schemas based on official specification."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, HttpUrl
from enum import Enum
import json


class McpResourceType(str, Enum):
    """MCP resource types as per specification."""
    FILE = "file"
    DIRECTORY = "directory"


class McpToolType(str, Enum):
    """MCP tool types as per specification."""
    FUNCTION = "function"
    PROCEDURE = "procedure"


class McpResourceMetadata(BaseModel):
    """MCP resource metadata as per specification."""
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mime_type: Optional[str] = Field(None, description="MIME type for files")
    size: Optional[int] = Field(None, description="Size in bytes")
    created: Optional[str] = Field(None, description="Creation timestamp")
    modified: Optional[str] = Field(None, description="Last modification timestamp")


class McpResource(BaseModel):
    """MCP resource as per specification."""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    resource_type: McpResourceType = Field(..., description="Resource type")
    metadata: Optional[McpResourceMetadata] = Field(None, description="Resource metadata")
    
    @field_validator('uri')
    @classmethod
    def validate_uri(cls, v: str) -> str:
        """Validate resource URI format."""
        if not v.startswith(('file://', 'http://', 'https://', 'ws://', 'wss://')):
            raise ValueError("Resource URI must start with file://, http://, https://, ws://, or wss://")
        return v


class McpToolParameter(BaseModel):
    """MCP tool parameter as per specification."""
    type: str = Field(..., description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    enum: Optional[List[str]] = Field(None, description="Enum values if applicable")
    items: Optional[Dict[str, Any]] = Field(None, description="Array item schema if applicable")
    properties: Optional[Dict[str, Any]] = Field(None, description="Object properties if applicable")
    required: Optional[List[str]] = Field(None, description="Required properties if applicable")


class McpTool(BaseModel):
    """MCP tool as per specification."""
    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    input_schema: McpToolParameter = Field(..., description="Input schema")
    tool_type: McpToolType = Field(default=McpToolType.FUNCTION, description="Tool type")
    
    @field_validator('name')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Tool name cannot be empty")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Tool name must contain only alphanumeric characters, hyphens, and underscores")
        return v


class McpServerInfo(BaseModel):
    """MCP server information as per specification."""
    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    description: Optional[str] = Field(None, description="Server description")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Server capabilities")
    
    @field_validator('name')
    @classmethod
    def validate_server_name(cls, v: str) -> str:
        """Validate server name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Server name cannot be empty")
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Server name must contain only alphanumeric characters, hyphens, and underscores")
        return v
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Server version cannot be empty")
        # Basic semver validation
        parts = v.split('.')
        if len(parts) < 2:
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        return v


class McpServerSpecification(BaseModel):
    """Complete MCP server specification as per protocol."""
    server_info: McpServerInfo = Field(..., description="Server information")
    resources: Optional[List[McpResource]] = Field(default_factory=list, description="Available resources")
    tools: Optional[List[McpTool]] = Field(default_factory=list, description="Available tools")
    schemas: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional schemas")
    
    @field_validator('resources')
    @classmethod
    def validate_resources(cls, v: Optional[List[McpResource]]) -> Optional[List[McpResource]]:
        """Validate resources follow MCP standards."""
        if v is not None:
            resource_uris = [resource.uri for resource in v]
            if len(resource_uris) != len(set(resource_uris)):
                raise ValueError("Resource URIs must be unique")
        return v
    
    @field_validator('tools')
    @classmethod
    def validate_tools(cls, v: Optional[List[McpTool]]) -> Optional[List[McpTool]]:
        """Validate tools follow MCP standards."""
        if v is not None:
            tool_names = [tool.name for tool in v]
            if len(tool_names) != len(set(tool_names)):
                raise ValueError("Tool names must be unique")
        return v
    
    @field_validator('schemas')
    @classmethod
    def validate_schemas(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate schemas size limit."""
        if v is not None:
            if len(json.dumps(v)) > 65536:  # 64KB limit
                raise ValueError("Schemas size exceeds 64KB limit")
        return v


class McpServerRegistration(BaseModel):
    """MCP server registration request."""
    specification: McpServerSpecification = Field(..., description="MCP server specification")
    endpoint_url: str = Field(..., description="Server endpoint URL")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('endpoint_url')
    @classmethod
    def validate_endpoint_url(cls, v: str) -> str:
        """Validate endpoint URL format."""
        if not v.startswith(('http://', 'https://', 'ws://', 'wss://')):
            raise ValueError("Endpoint URL must start with http://, https://, ws://, or wss://")
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate metadata size limit."""
        if v is not None:
            if len(json.dumps(v)) > 32768:  # 32KB limit for metadata
                raise ValueError("Metadata size exceeds 32KB limit")
        return v


class McpCapabilityDiscovery(BaseModel):
    """MCP capability discovery result."""
    server_id: str = Field(..., description="Server ID")
    discovered_at: str = Field(..., description="Discovery timestamp")
    capabilities: Dict[str, Any] = Field(..., description="Discovered capabilities")
    resources: List[McpResource] = Field(default_factory=list, description="Discovered resources")
    tools: List[McpTool] = Field(default_factory=list, description="Discovered tools")
    errors: List[str] = Field(default_factory=list, description="Discovery errors")
    warnings: List[str] = Field(default_factory=list, description="Discovery warnings")


class McpServerStatus(BaseModel):
    """MCP server status information."""
    server_id: str = Field(..., description="Server ID")
    status: str = Field(..., description="Server status")
    health: str = Field(..., description="Health status")
    last_check: Optional[str] = Field(None, description="Last health check timestamp")
    capabilities_count: int = Field(default=0, description="Number of discovered capabilities")
    resources_count: int = Field(default=0, description="Number of available resources")
    tools_count: int = Field(default=0, description="Number of available tools")


class McpHandshakeRequest(BaseModel):
    """MCP handshake request."""
    protocol_version: str = Field(..., description="Protocol version")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client information")


class McpHandshakeResponse(BaseModel):
    """MCP handshake response."""
    protocol_version: str = Field(..., description="Protocol version")
    server_info: McpServerInfo = Field(..., description="Server information")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Server capabilities")
