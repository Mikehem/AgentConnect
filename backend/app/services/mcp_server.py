"""MCP Server service for business logic."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status

from app.models.mcp_server import McpServer, McpCredential
from app.models.user import User
from app.schemas.mcp_server import (
    McpServerCreate, 
    McpServerUpdate, 
    McpServerResponse,
    McpServerListResponse,
    ServerStatus,
    HealthStatus
)
from app.core.security import (
    validate_mcp_server_url, 
    check_organization_quota,
    validate_vault_path,
    sanitize_metadata,
    SSRFProtectionError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

def _normalize_uuid(value: any) -> uuid.UUID:
    """Normalize string UUIDs to UUID objects for SQLAlchemy queries."""
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )


class McpServerService:
    """Service for managing MCP servers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_server(
        self, 
        server_data: McpServerCreate, 
        current_user: User,
        request_id: str
    ) -> McpServer:
        """
        Create a new MCP server with validation and audit logging.
        
        Args:
            server_data: Server creation data
            current_user: Current authenticated user
            request_id: Request ID for tracing
            
        Returns:
            Created MCP server
            
        Raises:
            HTTPException: If validation fails or quota exceeded
        """
        try:
            # Extract identifiers early to avoid ORM lazy-load after rollbacks/deletions
            safe_user_id = str(getattr(current_user, "id", ""))
            safe_org_id = getattr(current_user, "org_id", None)
            logger.info(
                "Creating MCP server",
                request_id=request_id,
                user_id=safe_user_id,
                org_id=str(safe_org_id) if safe_org_id is not None else None,
                server_name=server_data.name
            )
            
            # Check organization quota
            if not check_organization_quota(str(safe_org_id), "servers"):
                logger.warning(
                    "Organization quota exceeded",
                    request_id=request_id,
                    org_id=str(safe_org_id)
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Organization server quota exceeded"
                )
            
            # Validate URL security
            try:
                validate_mcp_server_url(server_data.base_url, server_data.environment.value)
                if server_data.ws_url:
                    validate_mcp_server_url(server_data.ws_url, server_data.environment.value)
            except (SSRFProtectionError, ValueError) as e:
                logger.warning(
                    "SSRF protection blocked server creation",
                    request_id=request_id,
                    user_id=safe_user_id,
                    url=server_data.base_url,
                    error=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"URL validation failed: {str(e)}"
                )
            
            # Check for duplicate server name in organization
            existing_server = self.db.query(McpServer).filter(
                and_(
                    McpServer.org_id == safe_org_id,
                    McpServer.name == server_data.name,
                    McpServer.environment == server_data.environment.value,
                    McpServer.deleted_at.is_(None)
                )
            ).first()
            
            if existing_server:
                logger.warning(
                    "Duplicate server name",
                    request_id=request_id,
                    user_id=safe_user_id,
                    server_name=server_data.name,
                    environment=server_data.environment.value
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Server with name '{server_data.name}' already exists in {server_data.environment.value} environment"
                )
            
            # Validate auth config if provided
            if server_data.auth_config:
                try:
                    is_valid = validate_vault_path(server_data.auth_config.vault_path, str(safe_org_id))
                except ValueError as e:
                    is_valid = False
                if not is_valid:
                    logger.warning(
                        "Invalid vault path",
                        request_id=request_id,
                        user_id=safe_user_id,
                        vault_path=server_data.auth_config.vault_path
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid vault path format or organization scope"
                    )
            
            # Create server instance
            server = McpServer(
                id=uuid.uuid4(),
                org_id=safe_org_id,
                name=server_data.name,
                description=server_data.description,
                environment=server_data.environment.value,
                base_url=server_data.base_url,
                ws_url=server_data.ws_url,
                tags=server_data.tags,
                server_metadata=sanitize_metadata(server_data.metadata),
                owner_user_id=getattr(current_user, "id", None),
                status=ServerStatus.PENDING_DISCOVERY.value,
                health_status=HealthStatus.UNKNOWN.value
            )
            
            # Save to database
            self.db.add(server)
            self.db.flush()  # Get the ID
            
            # Create credential if provided
            if server_data.auth_config:
                credential = McpCredential(
                    id=uuid.uuid4(),
                    mcp_server_id=server.id,
                    credential_type=server_data.auth_config.type.value,
                    vault_path=server_data.auth_config.vault_path,
                    scope=[],
                    metadata={}
                )
                self.db.add(credential)
            
            # Commit transaction
            self.db.commit()
            self.db.refresh(server)
            
            logger.info(
                "MCP server created successfully",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server.id),
                server_name=server.name
            )
            
            return server
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to create MCP server",
                request_id=request_id,
                user_id=safe_user_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create MCP server"
            )
    
    def get_server(self, server_id: any, current_user: User) -> McpServer:
        """
        Get MCP server by ID with organization isolation.
        
        Args:
            server_id: Server ID
            current_user: Current authenticated user
            
        Returns:
            MCP server
            
        Raises:
            HTTPException: If server not found or access denied
        """
        safe_org_id = getattr(current_user, "org_id", None)
        server_uuid = _normalize_uuid(server_id)
        server = self.db.query(McpServer).filter(
            and_(
                McpServer.id == server_uuid,
                McpServer.org_id == safe_org_id,
                McpServer.deleted_at.is_(None)
            )
        ).first()
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP server not found"
            )
        
        return server
    
    def list_servers(
        self,
        current_user: User,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> McpServerListResponse:
        """
        List MCP servers with filtering and pagination.
        
        Args:
            current_user: Current authenticated user
            environment: Filter by environment
            status: Filter by status
            tags: Filter by tags
            search: Search in name and description
            limit: Number of results to return
            offset: Number of results to skip
            
        Returns:
            Paginated list of MCP servers
        """
        safe_org_id = getattr(current_user, "org_id", None)
        # Build query with organization isolation
        query = self.db.query(McpServer).filter(
            and_(
                McpServer.org_id == safe_org_id,
                McpServer.deleted_at.is_(None)
            )
        )
        
        # Apply filters
        if environment:
            query = query.filter(McpServer.environment == environment)
        
        if status:
            query = query.filter(McpServer.status == status)
        
        if tags:
            # Filter by any of the provided tags
            tag_filters = [McpServer.tags.contains([tag]) for tag in tags]
            query = query.filter(or_(*tag_filters))
        
        if search:
            search_filter = or_(
                McpServer.name.ilike(f"%{search}%"),
                McpServer.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        servers = query.order_by(desc(McpServer.created_at)).offset(offset).limit(limit).all()
        
        # Convert servers to response format with string UUIDs
        server_responses = []
        for server in servers:
            server_dict = {
                "id": str(server.id),
                "org_id": server.org_id,
                "name": server.name,
                "description": server.description,
                "environment": server.environment,
                "base_url": server.base_url,
                "ws_url": server.ws_url,
                "tags": server.tags or [],
                "server_metadata": server.server_metadata or {},
                "owner_user_id": str(server.owner_user_id) if server.owner_user_id else None,
                "status": server.status,
                "health_status": server.health_status,
                "last_health_check_at": server.last_health_check_at,
                "last_discovery_at": server.last_discovery_at,
                "created_at": server.created_at,
                "updated_at": server.updated_at,
                "deleted_at": server.deleted_at
            }
            server_responses.append(server_dict)
        
        return McpServerListResponse(
            servers=server_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
    
    def update_server(
        self,
        server_id: any,
        server_data: McpServerUpdate,
        current_user: User,
        request_id: str
    ) -> McpServer:
        """
        Update MCP server with validation.
        
        Args:
            server_id: Server ID
            server_data: Update data
            current_user: Current authenticated user
            request_id: Request ID for tracing
            
        Returns:
            Updated MCP server
            
        Raises:
            HTTPException: If validation fails or server not found
        """
        try:
            safe_user_id = str(getattr(current_user, "id", ""))
            # Normalize UUID and get existing server
            server_uuid = _normalize_uuid(server_id)
            server = self.get_server(server_uuid, current_user)
            
            logger.info(
                "Updating MCP server",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server_uuid)
            )
            
            # Validate URL security if base_url is being updated
            if server_data.base_url is not None:
                try:
                    validate_mcp_server_url(server_data.base_url, server.environment)
                except SSRFProtectionError as e:
                    logger.warning(
                        "SSRF protection blocked server update",
                        request_id=request_id,
                        user_id=safe_user_id,
                        url=server_data.base_url,
                        error=str(e)
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"URL validation failed: {str(e)}"
                    )
            
            if server_data.ws_url is not None:
                try:
                    validate_mcp_server_url(server_data.ws_url, server.environment)
                except SSRFProtectionError as e:
                    logger.warning(
                        "SSRF protection blocked server update",
                        request_id=request_id,
                        user_id=safe_user_id,
                        url=server_data.ws_url,
                        error=str(e)
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"WebSocket URL validation failed: {str(e)}"
                    )
            
            # Check for duplicate name if name is being updated
            if server_data.name is not None and server_data.name != server.name:
                existing_server = self.db.query(McpServer).filter(
                    and_(
                        McpServer.org_id == getattr(current_user, "org_id", None),
                        McpServer.name == server_data.name,
                        McpServer.environment == server.environment,
                        McpServer.id != server_id,
                        McpServer.deleted_at.is_(None)
                    )
                ).first()
                
                if existing_server:
                    logger.warning(
                        "Duplicate server name during update",
                        request_id=request_id,
                        user_id=safe_user_id,
                        server_name=server_data.name,
                        environment=server.environment
                    )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Server with name '{server_data.name}' already exists in {server.environment} environment"
                    )
            
            # Validate auth config if provided
            if server_data.auth_config:
                if not validate_vault_path(server_data.auth_config.vault_path, str(getattr(current_user, "org_id", None))):
                    logger.warning(
                        "Invalid vault path during update",
                        request_id=request_id,
                        user_id=safe_user_id,
                        vault_path=server_data.auth_config.vault_path
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid vault path format or organization scope"
                    )
            
            # Update fields
            update_data = server_data.model_dump(exclude_unset=True)
            
            # Sanitize metadata if provided
            if 'metadata' in update_data:
                update_data['server_metadata'] = sanitize_metadata(update_data['metadata'])
                del update_data['metadata']
            
            # Update server
            for field, value in update_data.items():
                setattr(server, field, value)
            
            server.updated_at = datetime.now(timezone.utc)
            
            # Update credential if auth_config provided
            if server_data.auth_config:
                # Remove existing credential
                self.db.query(McpCredential).filter(
                    McpCredential.mcp_server_id == server_id
                ).delete()
                
                # Create new credential
                credential = McpCredential(
                    id=uuid.uuid4(),
                    mcp_server_id=server.id,
                    credential_type=server_data.auth_config.type.value,
                    vault_path=server_data.auth_config.vault_path,
                    scope=[],
                    metadata={}
                )
                self.db.add(credential)
            
            # Commit transaction
            self.db.commit()
            self.db.refresh(server)
            
            logger.info(
                "MCP server updated successfully",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server_id)
            )
            
            return server
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to update MCP server",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update MCP server"
            )
    
    def delete_server(
        self,
        server_id: any,
        current_user: User,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Soft delete MCP server.
        
        Args:
            server_id: Server ID
            current_user: Current authenticated user
            request_id: Request ID for tracing
            
        Returns:
            Deletion response
            
        Raises:
            HTTPException: If server not found
        """
        try:
            safe_user_id = str(getattr(current_user, "id", ""))
            # Normalize UUID and get existing server
            server_uuid = _normalize_uuid(server_id)
            server = self.get_server(server_uuid, current_user)
            
            logger.info(
                "Deleting MCP server",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server_uuid)
            )
            
            # Soft delete
            server.deleted_at = datetime.now(timezone.utc)
            server.status = ServerStatus.DELETED.value
            
            # Commit transaction
            self.db.commit()
            
            logger.info(
                "MCP server deleted successfully",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server_id)
            )
            
            return {
                "message": "MCP server deleted successfully",
                "deleted_at": server.deleted_at,
                "cleanup_job_id": None  # TODO: Implement cleanup job
            }
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to delete MCP server",
                request_id=request_id,
                user_id=safe_user_id,
                server_id=str(server_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete MCP server"
            )
