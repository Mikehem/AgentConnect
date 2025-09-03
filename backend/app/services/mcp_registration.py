"""MCP Registration Service for protocol-compliant server registration."""

import json
import uuid
import httpx
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.mcp_server import McpServer, McpCredential, McpCapability
from app.schemas.mcp_protocol import (
    McpServerSpecification, McpServerRegistration, McpCapabilityDiscovery,
    McpHandshakeRequest, McpHandshakeResponse, McpServerInfo
)
from app.schemas.mcp_server import ServerStatus, HealthStatus
from app.core.logging import get_logger
from app.core.security import validate_url_security, sanitize_metadata
from app.core.config import settings
from app.models.user import User

logger = get_logger(__name__)


class McpRegistrationService:
    """Service for MCP-compliant server registration."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_from_specification(
        self, 
        spec: McpServerSpecification, 
        endpoint_url: str,
        current_user: User,
        auth_config: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
        request_id: str = None
    ) -> McpServer:
        """Register MCP server from specification."""
        
        safe_user_id = getattr(current_user, "id", None)
        logger.info(
            "Registering MCP server from specification",
            request_id=request_id,
            user_id=str(safe_user_id) if safe_user_id else "",
            server_name=spec.server_info.name,
            endpoint_url=endpoint_url
        )
        
        try:
            # 1. Validate specification
            self._validate_specification(spec)
            
            # 2. Validate endpoint URL security
            validate_url_security(endpoint_url)
            
            # 3. Test server connectivity
            await self._test_server_connectivity(endpoint_url, auth_config)
            
            # 4. Perform MCP handshake
            handshake_response = await self._perform_handshake(endpoint_url, auth_config)
            
            # 5. Create server record
            server = self._create_server_record(spec, endpoint_url, current_user, auth_config, environment)
            
            # 6. Store capabilities
            self._store_capabilities(server, spec, handshake_response)
            
            # 7. Commit transaction
            self.db.commit()
            
            logger.info(
                "MCP server registered successfully",
                request_id=request_id,
                server_id=str(server.id),
                capabilities_count=len(spec.tools or [])
            )
            
            return server
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to register MCP server",
                request_id=request_id,
                user_id=str(safe_user_id) if safe_user_id else "",
                error=str(e)
            )
            raise
    
    async def register_from_json_file(
        self, 
        json_file_path: str,
        endpoint_url: str,
        current_user: User,
        auth_config: Optional[Dict[str, Any]] = None,
        request_id: str = None
    ) -> McpServer:
        """Register MCP server from local JSON file."""
        
        safe_user_id = getattr(current_user, "id", None)
        logger.info(
            "Registering MCP server from JSON file",
            request_id=request_id,
            user_id=str(safe_user_id) if safe_user_id else "",
            file_path=json_file_path,
            endpoint_url=endpoint_url
        )
        
        try:
            # Load and parse JSON file
            with open(json_file_path, 'r') as f:
                spec_data = json.load(f)
            
            spec = McpServerSpecification(**spec_data)
            return await self.register_from_specification(
                spec, endpoint_url, current_user, auth_config, request_id
            )
            
        except FileNotFoundError:
            raise ValueError(f"Specification file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in specification file: {e}")
        except Exception as e:
            logger.error(
                "Failed to register MCP server from file",
                request_id=request_id,
                user_id=str(safe_user_id) if safe_user_id else "",
                error=str(e)
            )
            raise
    
    async def register_from_url(
        self, 
        spec_url: str,
        endpoint_url: str,
        current_user: User,
        auth_config: Optional[Dict[str, Any]] = None,
        request_id: str = None
    ) -> McpServer:
        """Register MCP server from specification URL."""
        
        safe_user_id = getattr(current_user, "id", None)
        logger.info(
            "Registering MCP server from URL",
            request_id=request_id,
            user_id=str(safe_user_id) if safe_user_id else "",
            spec_url=spec_url,
            endpoint_url=endpoint_url
        )
        
        try:
            # Load specification from URL
            spec = await self._load_specification_from_url(spec_url)
            return await self.register_from_specification(
                spec, endpoint_url, current_user, auth_config, request_id
            )
            
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch specification from URL: {e}")
        except Exception as e:
            logger.error(
                "Failed to register MCP server from URL",
                request_id=request_id,
                user_id=str(safe_user_id) if safe_user_id else "",
                error=str(e)
            )
            raise
    
    def _validate_specification(self, spec: McpServerSpecification) -> None:
        """Validate specification against MCP standards."""
        
        # Validate server info
        if not spec.server_info.name or not spec.server_info.version:
            raise ValueError("Server name and version are required")
        
        # Validate tools
        if spec.tools:
            tool_names = [tool.name for tool in spec.tools]
            if len(tool_names) != len(set(tool_names)):
                raise ValueError("Tool names must be unique")
        
        # Validate resources
        if spec.resources:
            resource_uris = [resource.uri for resource in spec.resources]
            if len(resource_uris) != len(set(resource_uris)):
                raise ValueError("Resource URIs must be unique")
        
        # Validate schemas size
        if spec.schemas and len(json.dumps(spec.schemas)) > 65536:
            raise ValueError("Schemas size exceeds 64KB limit")
    
    async def _load_specification_from_url(self, spec_url: str) -> McpServerSpecification:
        """Load MCP specification from URL."""
        
        # Validate URL security
        validate_url_security(spec_url)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(spec_url)
            response.raise_for_status()
            spec_data = response.json()
            return McpServerSpecification(**spec_data)
    
    async def _test_server_connectivity(
        self, 
        endpoint_url: str, 
        auth_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Test server connectivity and basic health check."""
        
        headers = self._build_auth_headers(auth_config)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test basic connectivity
            try:
                response = await client.get(f"{endpoint_url}/health", headers=headers)
                response.raise_for_status()
            except httpx.HTTPError:
                # Try alternative health endpoint
                try:
                    response = await client.get(f"{endpoint_url}/", headers=headers)
                    response.raise_for_status()
                except httpx.HTTPError as e:
                    raise ValueError(f"Server connectivity test failed: {e}")
    
    async def _perform_handshake(
        self, 
        endpoint_url: str, 
        auth_config: Optional[Dict[str, Any]] = None
    ) -> McpHandshakeResponse:
        """Perform MCP handshake with server."""
        
        headers = self._build_auth_headers(auth_config)
        handshake_request = McpHandshakeRequest(
            protocol_version="1.0",
            client_info={
                "name": "SprintConnect",
                "version": "1.0.0"
            }
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{endpoint_url}/mcp/handshake",
                    headers=headers,
                    json=handshake_request.model_dump()
                )
                response.raise_for_status()
                return McpHandshakeResponse(**response.json())
            except httpx.HTTPError:
                # Try alternative handshake endpoint
                try:
                    response = await client.post(
                        f"{endpoint_url}/handshake",
                        headers=headers,
                        json=handshake_request.model_dump()
                    )
                    response.raise_for_status()
                    return McpHandshakeResponse(**response.json())
                except httpx.HTTPError as e:
                    # If handshake fails, create a minimal response
                    logger.warning(f"MCP handshake failed, using minimal response: {e}")
                    return McpHandshakeResponse(
                        protocol_version="1.0",
                        server_info=McpServerInfo(
                            name="unknown",
                            version="1.0.0"
                        ),
                        capabilities={}
                    )
    
    def _build_auth_headers(self, auth_config: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Build authentication headers for requests."""
        
        headers = {"Content-Type": "application/json"}
        
        if auth_config:
            auth_type = auth_config.get("type")
            if auth_type == "bearer_token":
                token = auth_config.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            elif auth_type == "api_key":
                api_key = auth_config.get("api_key")
                header_name = auth_config.get("header_name", "X-API-Key")
                if api_key:
                    headers[header_name] = api_key
        
        return headers
    
    def _create_server_record(
        self, 
        spec: McpServerSpecification,
        endpoint_url: str,
        current_user: User,
        auth_config: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None
    ) -> McpServer:
        """Create server record in database."""
        
        # Determine environment
        server_environment = environment or ("development" if getattr(settings, "DEBUG", True) else "production")
        
        # Check for duplicate server in same environment
        existing_server = self.db.query(McpServer).filter(
            McpServer.org_id == current_user.org_id,
            McpServer.name == spec.server_info.name,
            McpServer.environment == server_environment,
            McpServer.deleted_at.is_(None)
        ).first()
        
        if existing_server:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server with name '{spec.server_info.name}' already exists in {server_environment} environment"
            )
        
        # Create server record
        server = McpServer(
            id=uuid.uuid4(),
            org_id=current_user.org_id,
            name=spec.server_info.name,
            description=spec.server_info.description,
            environment=server_environment,
            base_url=endpoint_url,
            ws_url=None,
            tags=[],
            server_metadata=sanitize_metadata({
                "version": spec.server_info.version,
                "capabilities": spec.server_info.capabilities,
                "schemas": spec.schemas,
                "specification": spec.model_dump()
            }),
            owner_user_id=current_user.id,
            status=ServerStatus.ACTIVE.value,
            health_status=HealthStatus.HEALTHY.value
        )
        
        self.db.add(server)
        self.db.flush()  # Get the ID
        
        # Create credential if provided
        if auth_config:
            credential = McpCredential(
                id=uuid.uuid4(),
                mcp_server_id=server.id,
                credential_type=auth_config.get("type", "bearer_token"),
                vault_path=auth_config.get("vault_path", ""),
                scope=auth_config.get("scope", []),
                credential_metadata=sanitize_metadata(auth_config)
            )
            self.db.add(credential)
        
        return server
    
    def _store_capabilities(
        self,
        server: McpServer,
        spec: Optional[McpServerSpecification],
        handshake_response: McpHandshakeResponse
    ) -> None:
        """Store discovered capabilities in database."""
        
        # Store tools from specification
        if spec and spec.tools:
            for tool in spec.tools:
                capability = McpCapability(
                    id=uuid.uuid4(),
                    mcp_server_id=server.id,
                    name=tool.name,
                    description=tool.description,
                    version=spec.server_info.version,
                    schema_json=tool.input_schema.model_dump(),
                    capability_metadata=sanitize_metadata({
                        "tool_type": tool.tool_type.value,
                        "discovered_from": "specification"
                    })
                )
                self.db.add(capability)
        
        # Store resources from specification
        if spec and spec.resources:
            for resource in spec.resources:
                capability = McpCapability(
                    id=uuid.uuid4(),
                    mcp_server_id=server.id,
                    name=f"resource_{resource.name}",
                    description=f"Resource: {resource.description or resource.name}",
                    version=spec.server_info.version,
                    schema_json={
                        "type": "resource",
                        "uri": resource.uri,
                        "resource_type": resource.resource_type.value
                    },
                    capability_metadata=sanitize_metadata({
                        "resource_type": resource.resource_type.value,
                        "uri": resource.uri,
                        "discovered_from": "specification"
                    })
                )
                self.db.add(capability)
        
        # Store capabilities from handshake response
        if handshake_response.capabilities:
            for capability_name, capability_data in handshake_response.capabilities.items():
                # Handle both dictionary and boolean capability data
                if isinstance(capability_data, dict):
                    description = capability_data.get("description", "")
                    schema_data = capability_data
                else:
                    # For boolean values, create a simple schema
                    description = f"Capability: {capability_name}"
                    schema_data = {"enabled": capability_data}
                
                capability = McpCapability(
                    id=uuid.uuid4(),
                    mcp_server_id=server.id,
                    name=capability_name,
                    description=description,
                    version=handshake_response.server_info.version,
                    schema_json=schema_data,
                    capability_metadata=sanitize_metadata({
                        "discovered_from": "handshake"
                    })
                )
                self.db.add(capability)
    
    async def discover_capabilities(
        self, 
        server_id: str,
        current_user: User,
        request_id: str = None
    ) -> McpCapabilityDiscovery:
        """Discover capabilities for an existing server."""
        
        safe_user_id = getattr(current_user, "id", None)
        logger.info(
            "Discovering capabilities for server",
            request_id=request_id,
            user_id=str(safe_user_id) if safe_user_id else "",
            server_id=server_id
        )
        
        # Get server
        server = self.db.query(McpServer).filter(
            McpServer.id == server_id,
            McpServer.org_id == current_user.org_id,
            McpServer.deleted_at.is_(None)
        ).first()
        
        if not server:
            raise ValueError("Server not found")
        
        try:
            # Get auth config
            credential = self.db.query(McpCredential).filter(
                McpCredential.mcp_server_id == server_id
            ).first()
            
            auth_config = None
            if credential:
                auth_config = {
                    "type": credential.credential_type,
                    "vault_path": credential.vault_path
                }
            
            # Perform handshake
            handshake_response = await self._perform_handshake(server.base_url, auth_config)
            
            # Store new capabilities
            self._store_capabilities(server, None, handshake_response)
            
            # Update discovery timestamp
            server.last_discovery_at = datetime.now(UTC)
            self.db.commit()
            
            # Get all capabilities
            capabilities = self.db.query(McpCapability).filter(
                McpCapability.mcp_server_id == server_id
            ).all()
            
            return McpCapabilityDiscovery(
                server_id=server_id,
                discovered_at=datetime.now(UTC).isoformat(),
                capabilities=handshake_response.capabilities,
                resources=[],  # Will be populated from capabilities
                tools=[],  # Will be populated from capabilities
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to discover capabilities",
                request_id=request_id,
                server_id=server_id,
                error=str(e)
            )
            raise
