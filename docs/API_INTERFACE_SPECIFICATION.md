# SprintConnect API Interface Specification

## Overview

This document provides a comprehensive specification of all API endpoints available in the SprintConnect backend. The API follows RESTful principles and uses JSON for data exchange.

**Base URL**: `http://localhost:8000` (development)  
**API Version**: v1  
**Content Type**: `application/json`  
**Authentication**: Bearer Token (JWT) or API Key

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [MCP Server Management](#mcp-server-management)
3. [Health Monitoring](#health-monitoring)
4. [Capabilities Discovery](#capabilities-discovery)
5. [Organizations](#organizations)
6. [Error Handling](#error-handling)
7. [Data Models](#data-models)

---

## Authentication & Authorization

### OIDC Authentication Flow

#### 1. Initiate Login
**GET** `/v1/auth/oidc/login`

Redirects to Logto Cloud for OIDC authentication.

**Response**: `302 Redirect` to Logto Cloud  
**Location Header**: Logto Cloud authorization URL

**Example**:
```bash
curl -X GET http://localhost:8000/v1/auth/oidc/login
# Returns: 302 Redirect to https://7atvme.logto.app/oidc/auth?...
```

#### 2. OIDC Callback
**GET** `/v1/auth/oidc/callback`

Handles the OIDC callback from Logto Cloud.

**Query Parameters**:
- `code` (string): Authorization code from OIDC provider
- `state` (string): State parameter for CSRF protection
- `error` (string, optional): Error code if authentication failed
- `error_description` (string, optional): Human-readable error description

**Response**: `302 Redirect` to frontend or error page

**Example**:
```bash
curl -X GET "http://localhost:8000/v1/auth/oidc/callback?code=abc123&state=xyz789"
```

#### 3. Logout
**POST** `/v1/auth/oidc/logout`

Initiates logout flow with Logto Cloud.

**Request Body**:
```json
{
  "post_logout_redirect_uri": "http://localhost:3000"
}
```

**Response**:
```json
{
  "logout_url": "https://7atvme.logto.app/oidc/logout?post_logout_redirect_uri=..."
}
```

### Traditional Authentication

#### 4. Login with Credentials
**POST** `/v1/auth/login`

Authenticate with email and password.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "session_id": "session-123",
  "user": {
    "user_id": "user-123",
    "org_id": "org-123",
    "email": "user@example.com",
    "roles": ["admin"]
  }
}
```

#### 5. Validate Session
**POST** `/v1/auth/validate`

Validate an existing session.

**Request Body**:
```json
{
  "session_id": "session-123"
}
```

**Response**:
```json
{
  "valid": true,
  "user": {
    "user_id": "user-123",
    "org_id": "org-123",
    "email": "user@example.com",
    "roles": ["admin"]
  }
}
```

#### 6. API Key Validation
**POST** `/v1/auth/api-key/validate`

Validate an API key.

**Request Body**:
```json
{
  "api_key": "api-key-123"
}
```

**Response**:
```json
{
  "valid": true,
  "user": {
    "user_id": "user-123",
    "org_id": "org-123",
    "email": "user@example.com",
    "roles": ["admin"]
  }
}
```

#### 7. Permission Check
**POST** `/v1/auth/permissions/check`

Check if user has specific permissions.

**Request Body**:
```json
{
  "permissions": ["mcp:servers:read", "mcp:servers:create"]
}
```

**Response**:
```json
{
  "has_permissions": true,
  "missing_permissions": []
}
```

---

## MCP Server Management

### Server Registration

#### 1. Register MCP Server (MCP Protocol)
**POST** `/v1/mcp/servers/register`

Register a new MCP server using the MCP protocol specification.

**Request Body**:
```json
{
  "name": "My MCP Server",
  "description": "A sample MCP server",
  "base_url": "https://mcp.example.com",
  "environment": "development",
  "tags": ["filesystem", "utilities"],
  "capabilities": {
    "tools": ["read_file", "write_file"],
    "resources": ["file:///path/to/resource"]
  }
}
```

**Response**:
```json
{
  "id": "server-123",
  "name": "My MCP Server",
  "description": "A sample MCP server",
  "base_url": "https://mcp.example.com",
  "environment": "development",
  "status": "active",
  "health_status": "healthy",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "org_id": "org-123",
  "owner_user_id": "user-123",
  "tags": ["filesystem", "utilities"],
  "capabilities": {
    "tools": ["read_file", "write_file"],
    "resources": ["file:///path/to/resource"]
  }
}
```

#### 2. Register MCP Server (Legacy)
**POST** `/v1/mcp/servers`

Register a new MCP server using the legacy format.

**Request Body**:
```json
{
  "name": "My MCP Server",
  "description": "A sample MCP server",
  "base_url": "https://mcp.example.com",
  "environment": "development",
  "tags": ["filesystem", "utilities"]
}
```

**Response**: Same as MCP Protocol registration

### Server Management

#### 3. List MCP Servers
**GET** `/v1/mcp/servers`

List all MCP servers for the authenticated user's organization.

**Query Parameters**:
- `environment` (string, optional): Filter by environment (development, staging, production)
- `status` (string, optional): Filter by status (active, inactive, archived)
- `health_status` (string, optional): Filter by health status (healthy, unhealthy, degraded, unknown)
- `limit` (integer, optional): Number of results per page (default: 50)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Response**:
```json
{
  "servers": [
    {
      "id": "server-123",
      "name": "My MCP Server",
      "description": "A sample MCP server",
      "base_url": "https://mcp.example.com",
      "environment": "development",
      "status": "active",
      "health_status": "healthy",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "org_id": "org-123",
      "owner_user_id": "user-123",
      "tags": ["filesystem", "utilities"]
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### 4. Get MCP Server
**GET** `/v1/mcp/servers/{server_id}`

Get details of a specific MCP server.

**Path Parameters**:
- `server_id` (string): UUID of the MCP server

**Response**:
```json
{
  "id": "server-123",
  "name": "My MCP Server",
  "description": "A sample MCP server",
  "base_url": "https://mcp.example.com",
  "environment": "development",
  "status": "active",
  "health_status": "healthy",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "org_id": "org-123",
  "owner_user_id": "user-123",
  "tags": ["filesystem", "utilities"],
  "capabilities": {
    "tools": ["read_file", "write_file"],
    "resources": ["file:///path/to/resource"]
  },
  "server_metadata": {
    "version": "1.0.0",
    "protocol_version": "2024-11-05"
  }
}
```

#### 5. Update MCP Server
**PUT** `/v1/mcp/servers/{server_id}`

Update an existing MCP server.

**Path Parameters**:
- `server_id` (string): UUID of the MCP server

**Request Body**:
```json
{
  "name": "Updated MCP Server",
  "description": "Updated description",
  "tags": ["filesystem", "utilities", "updated"]
}
```

**Response**: Same as Get MCP Server

#### 6. Delete MCP Server
**DELETE** `/v1/mcp/servers/{server_id}`

Delete an MCP server.

**Path Parameters**:
- `server_id` (string): UUID of the MCP server

**Response**:
```json
{
  "message": "MCP server deleted successfully",
  "deleted_at": "2024-01-01T00:00:00Z",
  "cleanup_job_id": null
}
```

---

## Health Monitoring

### Health Checks

#### 1. System Health
**GET** `/health`

Get overall system health status.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": 1704067200.0
}
```

#### 2. Server Health Status
**GET** `/v1/mcp/servers/{server_id}/health`

Get health status of a specific MCP server.

**Path Parameters**:
- `server_id` (string): UUID of the MCP server

**Response**:
```json
{
  "server_id": "server-123",
  "health_status": "healthy",
  "last_check_at": "2024-01-01T00:00:00Z",
  "uptime_percentage": 99.9,
  "response_time_ms": 150,
  "error_message": null,
  "checks": {
    "connectivity": "healthy",
    "handshake": "healthy",
    "capabilities": "healthy"
  }
}
```

#### 3. Health Configuration
**GET** `/v1/mcp/servers/{server_id}/health/config`

Get health monitoring configuration for a server.

**Response**:
```json
{
  "server_id": "server-123",
  "enabled": true,
  "check_interval_seconds": 300,
  "timeout_seconds": 30,
  "retry_count": 3,
  "alert_thresholds": {
    "response_time_ms": 5000,
    "uptime_percentage": 95.0
  }
}
```

**PUT** `/v1/mcp/servers/{server_id}/health/config`

Update health monitoring configuration.

**Request Body**:
```json
{
  "enabled": true,
  "check_interval_seconds": 300,
  "timeout_seconds": 30,
  "retry_count": 3,
  "alert_thresholds": {
    "response_time_ms": 5000,
    "uptime_percentage": 95.0
  }
}
```

#### 4. Health Metrics
**GET** `/v1/mcp/servers/{server_id}/health/metrics`

Get health metrics for a server.

**Query Parameters**:
- `start_time` (string, optional): Start time for metrics (ISO 8601)
- `end_time` (string, optional): End time for metrics (ISO 8601)
- `granularity` (string, optional): Metrics granularity (1m, 5m, 1h, 1d)

**Response**:
```json
{
  "server_id": "server-123",
  "period": {
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-01T23:59:59Z"
  },
  "summary": {
    "total_checks": 1440,
    "successful_checks": 1439,
    "failed_checks": 1,
    "uptime_percentage": 99.93,
    "avg_response_time_ms": 145.5,
    "max_response_time_ms": 2500
  },
  "metrics": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "status": "healthy",
      "response_time_ms": 150,
      "uptime": true
    }
  ]
}
```

#### 5. Health Alerts
**GET** `/v1/mcp/servers/{server_id}/health/alerts`

Get health alerts for a server.

**Response**:
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "server_id": "server-123",
      "type": "high_response_time",
      "severity": "warning",
      "message": "Response time exceeded threshold",
      "created_at": "2024-01-01T00:00:00Z",
      "resolved_at": "2024-01-01T00:05:00Z",
      "metadata": {
        "threshold": 5000,
        "actual_value": 5500
      }
    }
  ]
}
```

**POST** `/v1/mcp/servers/{server_id}/health/alerts`

Create a new health alert.

**Request Body**:
```json
{
  "type": "custom_alert",
  "severity": "critical",
  "message": "Custom alert message",
  "metadata": {
    "custom_field": "value"
  }
}
```

#### 6. Notification Channels
**GET** `/v1/mcp/servers/{server_id}/health/notifications`

Get notification channels for health alerts.

**Response**:
```json
{
  "channels": [
    {
      "id": "channel-123",
      "name": "Email Notifications",
      "type": "email",
      "enabled": true,
      "config": {
        "recipients": ["admin@example.com"],
        "template": "health_alert"
      }
    }
  ]
}
```

**POST** `/v1/mcp/servers/{server_id}/health/notifications`

Create a new notification channel.

**Request Body**:
```json
{
  "name": "Slack Notifications",
  "type": "slack",
  "enabled": true,
  "config": {
    "webhook_url": "https://hooks.slack.com/services/...",
    "channel": "#alerts"
  }
}
```

---

## Capabilities Discovery

### Capability Discovery

#### 1. Discover Server Capabilities
**POST** `/v1/mcp/servers/{server_id}/capabilities/discover`

Discover capabilities of an MCP server.

**Path Parameters**:
- `server_id` (string): UUID of the MCP server

**Response**:
```json
{
  "server_id": "server-123",
  "discovered_at": "2024-01-01T00:00:00Z",
  "capabilities": {
    "tools": {
      "read_file": {
        "name": "read_file",
        "description": "Read contents of a file",
        "inputSchema": {
          "type": "object",
          "properties": {
            "path": {
              "type": "string",
              "description": "Path to the file"
            }
          },
          "required": ["path"]
        }
      }
    },
    "resources": {
      "file:///": {
        "name": "file:///",
        "description": "File system resource",
        "uriTemplate": "file:///{path}"
      }
    }
  },
  "resources": [],
  "tools": [],
  "errors": [],
  "warnings": []
}
```

#### 2. Test Capability Method
**POST** `/v1/mcp/servers/{server_id}/capabilities/test`

Test a specific capability method.

**Path Parameters**:
- `server_id` (string): UUID of the MCP server

**Request Body**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/tmp/test.txt"
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "result": {
    "content": "Hello, World!",
    "isError": false
  },
  "execution_time_ms": 150
}
```

---

## Organizations

### Organization Management

#### 1. List Organizations
**GET** `/v1/organizations`

List organizations accessible to the authenticated user.

**Response**:
```json
{
  "organizations": [
    {
      "id": "org-123",
      "name": "Acme Corp",
      "description": "Acme Corporation",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "settings": {
        "max_servers": 100,
        "allowed_environments": ["development", "staging", "production"]
      }
    }
  ]
}
```

#### 2. Get Organization
**GET** `/v1/organizations/{org_id}`

Get details of a specific organization.

**Path Parameters**:
- `org_id` (string): UUID of the organization

**Response**:
```json
{
  "id": "org-123",
  "name": "Acme Corp",
  "description": "Acme Corporation",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "settings": {
    "max_servers": 100,
    "allowed_environments": ["development", "staging", "production"]
  },
  "users": [
    {
      "id": "user-123",
      "email": "user@example.com",
      "name": "John Doe",
      "roles": ["admin"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "type": "about:blank",
  "title": "Error Title",
  "status": 400,
  "detail": "Detailed error message",
  "request_id": "req-123-456-789"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate name)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Examples

#### Authentication Error
```json
{
  "type": "about:blank",
  "title": "Authentication required",
  "status": 401,
  "detail": "Missing Bearer token",
  "request_id": "req-123-456-789"
}
```

#### Validation Error
```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 422,
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "request_id": "req-123-456-789"
}
```

#### Resource Not Found
```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "MCP server not found",
  "request_id": "req-123-456-789"
}
```

---

## Data Models

### User Model
```json
{
  "id": "user-123",
  "email": "user@example.com",
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "picture": "https://example.com/avatar.jpg",
  "email_verified": true,
  "org_id": "org-123",
  "org_name": "Acme Corp",
  "roles": ["admin", "engineer"],
  "permissions": [
    "mcp:servers:read",
    "mcp:servers:create",
    "mcp:servers:update",
    "mcp:servers:delete"
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T12:00:00Z"
}
```

### MCP Server Model
```json
{
  "id": "server-123",
  "name": "My MCP Server",
  "description": "A sample MCP server",
  "base_url": "https://mcp.example.com",
  "environment": "development",
  "status": "active",
  "health_status": "healthy",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deleted_at": null,
  "org_id": "org-123",
  "owner_user_id": "user-123",
  "tags": ["filesystem", "utilities"],
  "capabilities": {
    "tools": ["read_file", "write_file"],
    "resources": ["file:///path/to/resource"]
  },
  "server_metadata": {
    "version": "1.0.0",
    "protocol_version": "2024-11-05",
    "health_config": {
      "enabled": true,
      "check_interval_seconds": 300,
      "timeout_seconds": 30,
      "retry_count": 3
    }
  }
}
```

### Organization Model
```json
{
  "id": "org-123",
  "name": "Acme Corp",
  "description": "Acme Corporation",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "settings": {
    "max_servers": 100,
    "allowed_environments": ["development", "staging", "production"],
    "features": {
      "analytics": true,
      "webhooks": true,
      "audit_logs": true
    }
  }
}
```

---

## Authentication Headers

### Bearer Token
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key
```http
X-API-Key: api-key-123-456-789
```

### Session ID
```http
X-Session-ID: session-123-456-789
```

### Request ID (Optional)
```http
X-Request-ID: req-123-456-789
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute per IP
- **MCP server endpoints**: 100 requests per minute per user
- **Health monitoring**: 1000 requests per minute per user
- **Discovery endpoints**: 50 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067260
```

---

## WebSocket Endpoints

### Real-time Health Updates
**WebSocket** `/ws/health/{server_id}`

Subscribe to real-time health updates for a specific server.

**Connection**: `ws://localhost:8000/ws/health/server-123`

**Message Format**:
```json
{
  "type": "health_update",
  "server_id": "server-123",
  "health_status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "response_time_ms": 150
}
```

---

## SDK Examples

### JavaScript/TypeScript
```typescript
import { SprintConnectClient } from '@sprintconnect/client'

const client = new SprintConnectClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
})

// List servers
const servers = await client.mcpServers.list()

// Create server
const server = await client.mcpServers.create({
  name: 'My Server',
  base_url: 'https://example.com',
  environment: 'development'
})
```

### Python
```python
from sprintconnect import SprintConnectClient

client = SprintConnectClient(
    base_url='http://localhost:8000',
    api_key='your-api-key'
)

# List servers
servers = client.mcp_servers.list()

# Create server
server = client.mcp_servers.create(
    name='My Server',
    base_url='https://example.com',
    environment='development'
)
```

---

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial API specification
- OIDC authentication support
- MCP server management
- Health monitoring
- Capabilities discovery
- Organization management

---

*This document is automatically generated from the backend API implementation. Last updated: 2024-01-01*
