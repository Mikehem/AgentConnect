"""Capability discovery and management services."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger
from app.schemas.mcp_protocol import McpTool, McpResource, McpCapabilityDiscovery
from app.models.mcp_server import McpServer
from app.models.mcp_server import McpCapability

logger = get_logger(__name__)


class CapabilityTestResult(BaseModel):
    """Result of capability testing."""
    capability_id: str
    success: bool
    response_time_ms: int
    error_message: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None


class CapabilityUsageStats(BaseModel):
    """Capability usage statistics."""
    capability_id: str
    total_calls: int
    success_rate: float
    avg_response_time_ms: float
    last_used: Optional[datetime] = None


class CapabilitiesService:
    """Service for managing MCP server capabilities."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def discover_capabilities(self, server_id: str, current_user: Any) -> McpCapabilityDiscovery:
        """Discover capabilities for an MCP server."""
        try:
            # Get server from database
            server = self.db.query(McpServer).filter(McpServer.id == server_id).first()
            if not server:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Server not found"
                )
            
            # Get capabilities from database
            capabilities = self.db.query(McpCapability).filter(
                McpCapability.mcp_server_id == server_id
            ).all()
            
            # Convert to discovery response
            tools = []
            resources = []
            
            for cap in capabilities:
                if cap.capability_type == "tool":
                    try:
                        tool_data = json.loads(cap.capability_data) if cap.capability_data else {}
                        tools.append(McpTool(**tool_data))
                    except (json.JSONDecodeError, ValidationError):
                        logger.warning(f"Invalid tool data for capability {cap.id}")
                elif cap.capability_type == "resource":
                    try:
                        resource_data = json.loads(cap.capability_data) if cap.capability_data else {}
                        resources.append(McpResource(**resource_data))
                    except (json.JSONDecodeError, ValidationError):
                        logger.warning(f"Invalid resource data for capability {cap.id}")
            
            return McpCapabilityDiscovery(
                server_id=server_id,
                server_name=server.name,
                discovered_at=datetime.now(timezone.utc),
                tools=tools,
                resources=resources,
                total_capabilities=len(capabilities)
            )
            
        except Exception as e:
            logger.error(f"Failed to discover capabilities: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to discover capabilities"
            )
    
    def validate_capability_schema(self, capability_data: Dict[str, Any]) -> bool:
        """Validate capability schema."""
        try:
            if capability_data.get("type") == "tool":
                McpTool(**capability_data)
            elif capability_data.get("type") == "resource":
                McpResource(**capability_data)
            else:
                return False
            return True
        except ValidationError:
            return False
    
    async def test_capability(self, capability_id: str, test_data: Dict[str, Any]) -> CapabilityTestResult:
        """Test a specific capability."""
        try:
            # Get capability from database
            capability = self.db.query(McpCapability).filter(
                McpCapability.id == capability_id
            ).first()
            
            if not capability:
                return CapabilityTestResult(
                    capability_id=capability_id,
                    success=False,
                    response_time_ms=0,
                    error_message="Capability not found"
                )
            
            # Mock capability testing
            import time
            start_time = time.time()
            
            # Simulate capability execution
            if capability.capability_type == "tool":
                # Mock tool execution
                result = {"status": "success", "output": "Mock tool output"}
            else:
                # Mock resource access
                result = {"status": "success", "data": "Mock resource data"}
            
            response_time = int((time.time() - start_time) * 1000)
            
            return CapabilityTestResult(
                capability_id=capability_id,
                success=True,
                response_time_ms=response_time,
                test_data=result
            )
            
        except Exception as e:
            logger.error(f"Failed to test capability {capability_id}: {e}")
            return CapabilityTestResult(
                capability_id=capability_id,
                success=False,
                response_time_ms=0,
                error_message=str(e)
            )
    
    def list_server_capabilities(self, server_id: str, current_user: Any) -> List[Dict[str, Any]]:
        """List all capabilities for a server."""
        capabilities = self.db.query(McpCapability).filter(
            McpCapability.mcp_server_id == server_id
        ).all()
        
        return [
            {
                "id": str(cap.id),
                "name": cap.name,
                "type": cap.capability_type,
                "description": cap.description,
                "metadata": json.loads(cap.capability_metadata) if cap.capability_metadata else {}
            }
            for cap in capabilities
        ]
    
    def get_capability_details(self, capability_id: str, current_user: Any) -> Dict[str, Any]:
        """Get detailed information about a capability."""
        capability = self.db.query(McpCapability).filter(
            McpCapability.id == capability_id
        ).first()
        
        if not capability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Capability not found"
            )
        
        return {
            "id": str(capability.id),
            "name": capability.name,
            "type": capability.capability_type,
            "description": capability.description,
            "data": json.loads(capability.capability_data) if capability.capability_data else {},
            "metadata": json.loads(capability.capability_metadata) if capability.capability_metadata else {},
            "created_at": capability.created_at,
            "updated_at": capability.updated_at
        }
    
    def update_capability_metadata(self, capability_id: str, metadata: Dict[str, Any], current_user: Any) -> Dict[str, Any]:
        """Update capability metadata."""
        capability = self.db.query(McpCapability).filter(
            McpCapability.id == capability_id
        ).first()
        
        if not capability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Capability not found"
            )
        
        capability.capability_metadata = json.dumps(metadata)
        capability.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return {
            "id": str(capability.id),
            "metadata": metadata,
            "updated_at": capability.updated_at
        }
    
    def get_capability_usage_stats(self, capability_id: str, current_user: Any) -> CapabilityUsageStats:
        """Get usage statistics for a capability."""
        # Mock usage statistics
        return CapabilityUsageStats(
            capability_id=capability_id,
            total_calls=150,
            success_rate=0.95,
            avg_response_time_ms=250,
            last_used=datetime.now(timezone.utc)
        )
    
    def get_capability_usage_timeline(self, capability_id: str, days: int = 30, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get usage timeline for a capability."""
        # Mock timeline data
        timeline = []
        for i in range(days):
            timeline.append({
                "date": (datetime.now(timezone.utc) - timedelta(days=i)).date(),
                "calls": 10 + (i % 5),
                "success_rate": 0.9 + (i % 10) * 0.01,
                "avg_response_time": 200 + (i % 3) * 50
            })
        
        return timeline
    
    def get_capability_error_logs(self, capability_id: str, limit: int = 100, current_user: Any = None) -> List[Dict[str, Any]]:
        """Get error logs for a capability."""
        # Mock error logs
        return [
            {
                "timestamp": datetime.now(timezone.utc),
                "error_type": "TimeoutError",
                "error_message": "Request timeout after 30 seconds",
                "request_id": f"req-{i}"
            }
            for i in range(min(limit, 5))
        ]
