# SprintConnect API Documentation

## Overview

The SprintConnect API provides RESTful endpoints and WebSocket connections for managing MCP servers, testing capabilities, and discovering resources. All endpoints follow OpenAPI 3.0 specifications with comprehensive validation and error handling.

## SprintConnect API Surface (by Component)

- AuthGateway / Auth API: `/auth/*` (OIDC PKCE, PAR/JAR, token exchange, introspection/revocation)
- Registry API: `/mcp/servers`, `/mcp/servers/{id}` (CRUD, signed manifest upload, discovery trigger/status)
- Capabilities API: `/mcp/servers/{id}/capabilities` (list/details), scoped to capability-level permissions
- Health API: `/mcp/servers/{id}/health`, `/metrics/health` (status, history, config)
- Discovery API: `/discovery/*` (search by capability/policy/environment)
- Chat API: `/chat/sessions/*` (create/list/detail/export) and WS stream endpoints
- Admin/Audit API: `/audit/*`, `/metrics/*`, `/webhooks/*`

## Base URLs

```
Development: https://dev-api.sprintconnect.com/v1
Staging:     https://staging-api.sprintconnect.com/v1  
Production:  https://api.sprintconnect.com/v1
```

## Authentication

### OIDC Authentication
```http
# Authorization Code flow with PKCE
GET /auth/authorize?
  client_id=sprintconnect&
  response_type=code&
  scope=openid profile email&
  redirect_uri=https://app.sprintconnect.com/auth/callback&
  code_challenge=<code_challenge>&
  code_challenge_method=S256&
  state=<state>

# Token exchange
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=<authorization_code>&
redirect_uri=https://app.sprintconnect.com/auth/callback&
client_id=sprintconnect&
code_verifier=<code_verifier>
```

### AuthGateway Enforcement
- All non-public endpoints require a Bearer token.
- Public endpoints (no auth): `/health`, `/metrics`, `/docs`, `/redoc`, OpenAPI spec.
- Problem+json errors on auth failures:
```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Token has expired",
  "request_id": "req_abc123"
}
```

### PAR/JAR and Token Exchange (OAuth 2.1 Enhancements)
```http
# Pushed Authorization Request (PAR)
POST /auth/par
Content-Type: application/x-www-form-urlencoded

client_id=sprintconnect&
response_type=code&
scope=openid profile email&
redirect_uri=https://app.sprintconnect.com/auth/callback&
code_challenge=<code_challenge>&
code_challenge_method=S256&
state=<state>

# PAR response
{
  "request_uri": "urn:ietf:params:oauth:request_uri:abc123",
  "expires_in": 90
}

# Token Exchange (RFC 8693)
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange&
subject_token=<access_token>&
subject_token_type=urn:ietf:params:oauth:token-type:access_token&
audience=mcp:server:{server_id}:capability:{capability}&
scope=mcp:server:{server_id}:capability:{capability}:invoke
```

### DPoP / mTLS Token Binding
```http
# DPoP-bound request example
GET /mcp/servers
Authorization: DPoP <access_token>
DPoP: <signed_proof_jwt>
```

### API Key Authentication
```http
Authorization: Bearer <api_key>
```

### JWT Token Format
```json
{
  "iss": "https://auth.sprintconnect.com",
  "sub": "user_12345",
  "aud": "sprintconnect",
  "exp": 1640995200,
  "iat": 1640991600,
  "org_id": "org_67890",
  "roles": ["engineer"],
  "permissions": [
    "mcp:servers:read",
    "mcp:servers:create",
    "chat:sessions:create"
  ]
}
```

## API Endpoints

### Authentication & Authorization

#### Exchange Authorization Code for Tokens
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=<code>&
redirect_uri=<redirect_uri>&
client_id=<client_id>&
code_verifier=<code_verifier>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "rt_1234567890abcdef",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid profile email"
}
```

#### Refresh Access Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "rt_1234567890abcdef"
}
```

#### Get Current User Profile
```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "user_12345",
  "email": "engineer@example.com",
  "name": "John Engineer",
  "org_id": "org_67890",
  "org_name": "Acme Corporation",
  "roles": ["engineer"],
  "permissions": [
    "mcp:servers:read",
    "mcp:servers:create",
    "mcp:capabilities:read",
    "chat:sessions:create"
  ],
  "last_login": "2024-01-15T10:30:00Z"
}
```

#### Create API Key
```http
POST /auth/api-keys
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "CI/CD Pipeline Key",
  "description": "For automated server registration",
  "scopes": [
    "mcp:servers:read",
    "mcp:servers:create"
  ],
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "api_key_id": "ak_abcdef123456",
  "name": "CI/CD Pipeline Key",
  "api_key": "ak_live_1234567890abcdef",
  "scopes": ["mcp:servers:read", "mcp:servers:create"],
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-12-31T23:59:59Z",
  "last_used_at": null
}
```

### MCP Server Registry

#### List MCP Servers
```http
GET /mcp/servers?environment=production&status=active&limit=20&offset=0
Authorization: Bearer <token>
```

**Query Parameters:**
- `environment`: Filter by environment (dev, staging, production)
- `status`: Filter by status (active, inactive, error)
- `tags`: Comma-separated list of tags
- `search`: Text search in name and description
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "servers": [
    {
      "id": "mcp_srv_123456",
      "name": "weather-api-server",
      "description": "Provides weather information and forecasts",
      "environment": "production",
      "base_url": "https://weather-mcp.example.com",
      "ws_url": "wss://weather-mcp.example.com/ws",
      "status": "active",
      "health_status": "healthy",
      "tags": ["weather", "external-api", "public"],
      "capabilities_count": 5,
      "owner": {
        "user_id": "user_98765",
        "name": "Jane Developer",
        "email": "jane@example.com"
      },
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "last_health_check": "2024-01-15T10:45:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

#### Get MCP Server Details
```http
GET /mcp/servers/{server_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "mcp_srv_123456",
  "name": "weather-api-server",
  "description": "Provides weather information and forecasts",
  "environment": "production",
  "base_url": "https://weather-mcp.example.com",
  "ws_url": "wss://weather-mcp.example.com/ws",
  "status": "active",
  "health_status": "healthy",
  "tags": ["weather", "external-api", "public"],
  "metadata": {
    "version": "1.2.0",
    "region": "us-east-1",
    "cost_center": "eng-platform"
  },
  "auth_config": {
    "type": "bearer_token",
    "vault_path": "secret/mcp-servers/weather-api/credentials"
  },
  "health_check": {
    "enabled": true,
    "interval_seconds": 60,
    "timeout_seconds": 30,
    "failure_threshold": 3
  },
  "policy_id": "policy_789",
  "owner": {
    "user_id": "user_98765",
    "name": "Jane Developer",
    "email": "jane@example.com"
  },
  "capabilities": [
    {
      "id": "cap_weather_current",
      "name": "get_current_weather",
      "description": "Get current weather for a location",
      "version": "1.0",
      "enabled": true,
      "schema": {
        "type": "function",
        "properties": {
          "location": {
            "type": "string",
            "description": "City name or coordinates"
          }
        },
        "required": ["location"]
      }
    }
  ],
  "usage_stats": {
    "total_calls": 1234,
    "calls_last_24h": 56,
    "avg_response_time_ms": 250,
    "error_rate_24h": 0.02
  },
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Register New MCP Server
```http
POST /mcp/servers
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "calendar-integration",
  "description": "Provides calendar management capabilities",
  "environment": "production",
  "base_url": "https://calendar-mcp.example.com",
  "ws_url": "wss://calendar-mcp.example.com/ws",
  "tags": ["calendar", "productivity", "internal"],
  "metadata": {
    "version": "2.1.0",
    "team": "productivity-team",
    "cost_center": "eng-productivity"
  },
  "auth_config": {
    "type": "oauth2",
    "vault_path": "secret/mcp-servers/calendar/oauth2"
  },
  "health_check": {
    "enabled": true,
    "interval_seconds": 120,
    "timeout_seconds": 45,
    "failure_threshold": 2
  },
  "auto_discover": true
}
```

**Response:**
```json
{
  "id": "mcp_srv_789012",
  "name": "calendar-integration",
  "status": "pending_discovery",
  "created_at": "2024-01-15T11:00:00Z",
  "discovery_job_id": "job_discover_789012"
}
```

#### Upload Signed Capability Manifest (JWS)
```http
POST /mcp/servers/{server_id}/manifests
Authorization: Bearer <token>
Content-Type: application/jose

<JWS signed manifest>
```

**Response:**
```json
{
  "version_id": "man_001",
  "issuer": "https://issuer.example.com",
  "kid": "key-2025-01-01",
  "verified": true,
  "policy_hash": "sha256:..."
}
```

#### Update MCP Server
```http
PATCH /mcp/servers/{server_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "description": "Updated description with new features",
  "tags": ["calendar", "productivity", "internal", "v2"],
  "metadata": {
    "version": "2.2.0",
    "changelog": "Added recurring event support"
  }
}
```

#### Delete MCP Server
```http
DELETE /mcp/servers/{server_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Server marked for deletion",
  "deleted_at": "2024-01-15T11:15:00Z",
  "cleanup_job_id": "job_cleanup_789012"
}
```

#### Trigger Capability Discovery
```http
POST /mcp/servers/{server_id}/discover
Authorization: Bearer <token>
Content-Type: application/json

{
  "force_refresh": true,
  "timeout_seconds": 120
}
```

**Response:**
```json
{
  "job_id": "job_discover_789012_v2",
  "status": "queued",
  "estimated_completion": "2024-01-15T11:05:00Z"
}
```

#### Get Discovery Job Status
```http
GET /mcp/discovery/jobs/{job_id}
Authorization: Bearer <token>
```

#### Get Server Capabilities
```http
GET /mcp/servers/{server_id}/capabilities
Authorization: Bearer <token>
```

**Response:**
```json
{
  "capabilities": [
    {
      "id": "cap_cal_create_event",
      "name": "create_calendar_event",
      "description": "Create a new calendar event",
      "version": "2.1",
      "enabled": true,
      "schema": {
        "type": "function",
        "properties": {
          "title": {"type": "string"},
          "start_time": {"type": "string", "format": "date-time"},
          "end_time": {"type": "string", "format": "date-time"},
          "attendees": {
            "type": "array",
            "items": {"type": "string", "format": "email"}
          }
        },
        "required": ["title", "start_time", "end_time"]
      },
      "usage_stats": {
        "total_calls": 89,
        "avg_response_time_ms": 180,
        "success_rate": 0.98
      },
      "discovered_at": "2024-01-15T11:03:00Z"
    }
  ],
  "discovery_metadata": {
    "last_discovery": "2024-01-15T11:03:00Z",
    "discovery_version": "1.2.0",
    "server_version": "2.1.0",
    "total_capabilities": 1
  }
}
```

#### Get Server Health Status
```http
GET /mcp/servers/{server_id}/health
Authorization: Bearer <token>
```

**Response:**
```json
{
  "server_id": "mcp_srv_123456",
  "status": "healthy",
  "last_check": "2024-01-15T11:00:00Z",
  "response_time_ms": 45,
  "checks": [
    {
      "name": "connectivity",
      "status": "pass",
      "response_time_ms": 45,
      "message": "Connection successful"
    },
    {
      "name": "authentication",
      "status": "pass",
      "response_time_ms": 12,
      "message": "Authentication successful"
    },
    {
      "name": "capability_introspection",
      "status": "pass",
      "response_time_ms": 89,
      "message": "5 capabilities discovered"
    }
  ],
  "history": [
    {
      "timestamp": "2024-01-15T10:55:00Z",
      "status": "healthy",
      "response_time_ms": 52
    },
    {
      "timestamp": "2024-01-15T10:50:00Z",
      "status": "healthy",
      "response_time_ms": 38
    }
  ]
}
```

### Discovery Service

#### Search Servers by Capability
```http
GET /discovery/servers?capability=weather&environment=production&tags=public
Authorization: Bearer <token>
```

**Query Parameters:**
- `capability`: Capability name or pattern
- `environment`: Target environment
- `tags`: Comma-separated tags
- `policy`: Policy constraints
- `fuzzy`: Enable fuzzy matching (default: false)
- `limit`: Max results (default: 10, max: 50)

**Response:**
```json
{
  "servers": [
    {
      "server_id": "mcp_srv_123456",
      "name": "weather-api-server",
      "environment": "production",
      "base_url": "https://weather-mcp.example.com",
      "ws_url": "wss://weather-mcp.example.com/ws",
      "matching_capabilities": [
        {
          "name": "get_current_weather",
          "description": "Get current weather for a location",
          "confidence_score": 0.95
        },
        {
          "name": "get_weather_forecast",
          "description": "Get weather forecast for location",
          "confidence_score": 0.88
        }
      ],
      "tags": ["weather", "external-api", "public"],
      "health_status": "healthy",
      "performance_score": 0.92,
      "auth_requirements": {
        "type": "bearer_token",
        "scopes": ["weather:read"]
      }
    }
  ],
  "total_matches": 1,
  "search_metadata": {
    "query": "weather",
    "filters_applied": ["environment=production", "tags=public"],
    "search_time_ms": 23
  }
}
```

#### Search Capabilities
```http
GET /discovery/capabilities?name=calendar&fuzzy=true
Authorization: Bearer <token>
```

**Response:**
```json
{
  "capabilities": [
    {
      "id": "cap_cal_create_event",
      "name": "create_calendar_event",
      "description": "Create a new calendar event",
      "server": {
        "id": "mcp_srv_789012",
        "name": "calendar-integration",
        "environment": "production"
      },
      "schema": {
        "type": "function",
        "properties": {
          "title": {"type": "string"},
          "start_time": {"type": "string", "format": "date-time"}
        }
      },
      "confidence_score": 1.0,
      "usage_stats": {
        "popularity_rank": 5,
        "avg_response_time_ms": 180
      }
    }
  ],
  "suggestions": [
    "schedule_meeting",
    "calendar_availability",
    "event_management"
  ]
}
```

#### Get Access Policies
```http
GET /discovery/policies?server_id=mcp_srv_123456
Authorization: Bearer <token>
```

**Response:**
```json
{
  "policies": [
    {
      "id": "policy_789",
      "name": "External API Access",
      "description": "Controls access to external API servers",
      "rules": [
        {
          "resource": "mcp:servers:mcp_srv_123456",
          "actions": ["read", "execute"],
          "conditions": {
            "environment": "production",
            "user_roles": ["engineer", "admin"],
            "rate_limit": "100/hour"
          }
        }
      ],
      "applies_to": ["mcp_srv_123456"],
      "created_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

### Chat & Testing

#### Create Chat Session
```http
POST /chat/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Multi-server weather and calendar test",
  "selected_servers": [
    "mcp_srv_123456",
    "mcp_srv_789012"
  ],
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "session_config": {
    "auto_save": true,
    "export_format": "json",
    "timeout_minutes": 60
  }
}
```

**Response:**
```json
{
  "session_id": "chat_sess_456789",
  "title": "Multi-server weather and calendar test",
  "status": "active",
  "selected_servers": [
    {
      "server_id": "mcp_srv_123456",
      "name": "weather-api-server",
      "available_capabilities": 5
    },
    {
      "server_id": "mcp_srv_789012", 
      "name": "calendar-integration",
      "available_capabilities": 8
    }
  ],
  "websocket_url": "wss://api.sprintconnect.com/v1/chat/sessions/chat_sess_456789/stream",
  "created_at": "2024-01-15T12:00:00Z"
}
```

#### List Chat Sessions
```http
GET /chat/sessions?limit=10&status=active
Authorization: Bearer <token>
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "chat_sess_456789",
      "title": "Multi-server weather and calendar test",
      "status": "active",
      "message_count": 12,
      "server_count": 2,
      "created_at": "2024-01-15T12:00:00Z",
      "last_activity": "2024-01-15T12:15:00Z",
      "total_tokens": 1456
    }
  ],
  "total": 1,
  "has_more": false
}
```

#### Get Chat Session Details
```http
GET /chat/sessions/{session_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "session_id": "chat_sess_456789",
  "title": "Multi-server weather and calendar test",
  "status": "active",
  "selected_servers": [
    {
      "server_id": "mcp_srv_123456",
      "name": "weather-api-server"
    }
  ],
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "What's the weather like in San Francisco?",
      "timestamp": "2024-01-15T12:01:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "I'll check the weather in San Francisco for you.",
      "timestamp": "2024-01-15T12:01:05Z",
      "tool_calls": [
        {
          "id": "tool_call_001",
          "server_id": "mcp_srv_123456",
          "capability": "get_current_weather",
          "arguments": {"location": "San Francisco, CA"},
          "result": {
            "temperature": 65,
            "condition": "partly cloudy",
            "humidity": 72
          },
          "duration_ms": 245,
          "status": "success"
        }
      ]
    }
  ],
  "usage_summary": {
    "total_tokens": 1456,
    "total_tool_calls": 8,
    "unique_capabilities_used": 3
  },
  "created_at": "2024-01-15T12:00:00Z"
}
```

#### Export Chat Session
```http
GET /chat/sessions/{session_id}/export?format=json
Authorization: Bearer <token>
```

**Response:** Returns downloadable file with session data.

#### Delete Chat Session
```http
DELETE /chat/sessions/{session_id}
Authorization: Bearer <token>
```

### WebSocket Chat Streaming

#### Connect to Chat Stream
```javascript
// WebSocket connection
const ws = new WebSocket(
  'wss://api.sprintconnect.com/v1/chat/sessions/chat_sess_456789/stream',
  ['bearer', access_token]
);

// Send message
ws.send(JSON.stringify({
  type: 'user_message',
  content: 'Schedule a meeting for tomorrow at 2pm',
  message_id: 'msg_003'
}));
```

#### WebSocket Message Types

**User Message:**
```json
{
  "type": "user_message",
  "content": "What's the weather in NYC?",
  "message_id": "msg_003",
  "timestamp": "2024-01-15T12:05:00Z"
}
```

**Assistant Response Stream:**
```json
{
  "type": "assistant_token",
  "content": "I'll",
  "message_id": "msg_004",
  "token_index": 0
}

{
  "type": "assistant_token", 
  "content": " check",
  "message_id": "msg_004",
  "token_index": 1
}
```

**Tool Call Event:**
```json
{
  "type": "tool_call_start",
  "tool_call_id": "tool_call_002",
  "server_id": "mcp_srv_123456",
  "capability": "get_current_weather",
  "arguments": {"location": "New York, NY"}
}

{
  "type": "tool_call_result",
  "tool_call_id": "tool_call_002",
  "result": {
    "temperature": 42,
    "condition": "snow",
    "humidity": 85
  },
  "duration_ms": 312,
  "status": "success"
}
```

**Error Event:**
```json
{
  "type": "error",
  "error_code": "TOOL_CALL_FAILED",
  "message": "Weather service temporarily unavailable",
  "tool_call_id": "tool_call_002",
  "retry_after_seconds": 30
}
```

### Metrics & Analytics

#### Get Usage Metrics
```http
GET /metrics/usage?group_by=server&range=7d&org_id=org_67890
Authorization: Bearer <token>
```

**Query Parameters:**
- `group_by`: server, capability, user, day, hour
- `range`: 1h, 6h, 1d, 7d, 30d
- `org_id`: Filter by organization (admin only)
- `server_id`: Filter by specific server
- `user_id`: Filter by specific user

**Response:**
```json
{
  "metrics": [
    {
      "dimension": "weather-api-server",
      "metrics": {
        "total_calls": 1234,
        "unique_users": 45,
        "avg_response_time_ms": 250,
        "error_rate": 0.02,
        "total_tokens": 45670,
        "estimated_cost_usd": 12.45
      },
      "time_series": [
        {
          "timestamp": "2024-01-14T00:00:00Z",
          "calls": 156,
          "tokens": 5432
        }
      ]
    }
  ],
  "summary": {
    "total_calls": 3456,
    "total_tokens": 123456,
    "total_cost_usd": 34.56,
    "period_start": "2024-01-08T12:00:00Z",
    "period_end": "2024-01-15T12:00:00Z"
  }
}
```

#### Get Top Resources
```http
GET /metrics/top?dimension=capabilities&range=30d&limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "top_capabilities": [
    {
      "rank": 1,
      "capability": "get_current_weather",
      "server": "weather-api-server",
      "usage_count": 5678,
      "unique_users": 89,
      "growth_rate": 0.15
    },
    {
      "rank": 2,
      "capability": "create_calendar_event",
      "server": "calendar-integration", 
      "usage_count": 3456,
      "unique_users": 67,
      "growth_rate": 0.23
    }
  ],
  "metadata": {
    "dimension": "capabilities",
    "period": "30d",
    "total_items": 47
  }
}
```

#### Get Health Metrics
```http
GET /metrics/health?environment=production
Authorization: Bearer <token>
```

**Response:**
```json
{
  "overall_health": {
    "status": "healthy",
    "availability": 0.998,
    "avg_response_time_ms": 180
  },
  "servers": [
    {
      "server_id": "mcp_srv_123456",
      "name": "weather-api-server",
      "status": "healthy",
      "uptime_percentage": 99.9,
      "avg_response_time_ms": 250,
      "last_outage": "2024-01-10T03:15:00Z"
    }
  ],
  "system_metrics": {
    "active_chat_sessions": 23,
    "queue_depth": 5,
    "cache_hit_rate": 0.85
  }
}
```

### Administration

#### Get Audit Logs
```http
GET /audit/logs?actor=user_12345&range=7d&limit=50
Authorization: Bearer <token>
```

**Query Parameters:**
- `actor`: Filter by user ID or API key ID
- `action`: Filter by action type
- `target`: Filter by target resource
- `range`: Time range (1h, 1d, 7d, 30d)
- `limit`: Max results (default: 20, max: 100)

**Response:**
```json
{
  "logs": [
    {
      "id": "audit_log_123456",
      "timestamp": "2024-01-15T12:00:00Z",
      "actor": {
        "type": "user",
        "id": "user_12345",
        "name": "John Engineer"
      },
      "action": "mcp:server:create",
      "target": {
        "type": "mcp_server",
        "id": "mcp_srv_789012",
        "name": "calendar-integration"
      },
      "details": {
        "environment": "production",
        "auto_discover": true
      },
      "source_ip": "203.0.113.45",
      "user_agent": "Mozilla/5.0...",
      "request_id": "req_abcdef123456",
      "result": "success"
    }
  ],
  "total": 1,
  "has_more": false
}
```

#### Create Webhook
```http
POST /webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Slack Notifications",
  "url": "https://hooks.slack.com/services/...",
  "secret": "webhook_secret_123",
  "events": [
    "server.health.unhealthy",
    "server.discovery.completed",
    "chat.session.created"
  ],
  "filters": {
    "environments": ["production"],
    "severity": ["warning", "critical"]
  },
  "retry_config": {
    "max_attempts": 3,
    "backoff_seconds": 60
  }
}
```

**Response:**
```json
{
  "webhook_id": "webhook_789012",
  "name": "Slack Notifications",
  "status": "active",
  "created_at": "2024-01-15T12:30:00Z"
}
```

#### List Webhooks
```http
GET /webhooks
Authorization: Bearer <token>
```

**Response:**
```json
{
  "webhooks": [
    {
      "webhook_id": "webhook_789012",
      "name": "Slack Notifications",
      "url": "https://hooks.slack.com/services/...",
      "status": "active",
      "events": ["server.health.unhealthy"],
      "last_triggered": "2024-01-15T11:45:00Z",
      "success_rate": 0.98,
      "created_at": "2024-01-15T12:30:00Z"
    }
  ]
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "base_url",
        "message": "Must be a valid HTTPS URL"
      }
    ],
    "request_id": "req_abcdef123456",
    "timestamp": "2024-01-15T12:00:00Z"
  }
}
```

### Authentication/Authorization Error Examples (problem+json)
```json
{
  "type": "https://api.sprintconnect.com/errors/permission-denied",
  "title": "Permission denied",
  "status": 403,
  "detail": "Capability invoke scope is required",
  "instance": "/mcp/servers/123/capabilities",
  "request_id": "req_123",
  "required_scopes": ["mcp:server:123:capability:get_current_weather:invoke"]
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content (for deletes)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resources)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Common Error Codes
- `VALIDATION_ERROR` - Request validation failed
- `AUTHENTICATION_REQUIRED` - Missing or invalid authentication
- `PERMISSION_DENIED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `SERVER_UNAVAILABLE` - MCP server unreachable
- `DISCOVERY_FAILED` - Capability discovery failed
- `TOOL_CALL_FAILED` - MCP tool execution failed

## Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Rate Limit Tiers
- **Free Tier**: 100 requests/hour, 10 chat sessions/day
- **Pro Tier**: 1000 requests/hour, 100 chat sessions/day  
- **Enterprise**: Custom limits based on contract

## Pagination

### Cursor-Based Pagination
```http
GET /mcp/servers?limit=20&cursor=eyJpZCI6Im1jcF9zcnZfMTIzNDU2In0%3D
```

**Response:**
```json
{
  "servers": [...],
  "pagination": {
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6Im1jcF9zcnZfNzg5MDEyIn0%3D"
  }
}
```

## Webhook Events

### Event Types
- `server.created` - New MCP server registered
- `server.updated` - Server configuration changed
- `server.deleted` - Server removed
- `server.health.healthy` - Server health check passed
- `server.health.unhealthy` - Server health check failed
- `server.discovery.started` - Capability discovery started
- `server.discovery.completed` - Discovery completed successfully
- `server.discovery.failed` - Discovery failed
- `chat.session.created` - New chat session started
- `chat.session.completed` - Chat session ended
- `usage.threshold.exceeded` - Usage threshold reached

### Webhook Payload
```json
{
  "event_id": "evt_123456789",
  "event_type": "server.health.unhealthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "org_id": "org_67890",
  "data": {
    "server_id": "mcp_srv_123456",
    "server_name": "weather-api-server",
    "environment": "production",
    "health_status": "unhealthy",
    "error_message": "Connection timeout after 30 seconds",
    "consecutive_failures": 3
  },
  "metadata": {
    "delivery_attempt": 1,
    "webhook_id": "webhook_789012"
  }
}
```

## SDK Examples

### Python SDK
```python
from sprintconnect import SprintConnectClient

# Initialize client
client = SprintConnectClient(
    api_key="ak_live_1234567890abcdef",
    base_url="https://api.sprintconnect.com/v1"
)

# Register server
server = client.mcp_servers.create({
    "name": "my-weather-server",
    "base_url": "https://my-weather.example.com",
    "environment": "production",
    "tags": ["weather", "public"]
})

# Start chat session
session = client.chat.create_session({
    "selected_servers": [server.id],
    "title": "Weather Testing"
})

# Send message
response = client.chat.send_message(
    session.id,
    "What's the weather in Paris?"
)
```

### JavaScript SDK
```javascript
import { SprintConnectClient } from '@sprintconnect/js-sdk';

// Initialize client
const client = new SprintConnectClient({
  apiKey: 'ak_live_1234567890abcdef',
  baseUrl: 'https://api.sprintconnect.com/v1'
});

// Register server
const server = await client.mcpServers.create({
  name: 'my-calendar-server',
  baseUrl: 'https://my-calendar.example.com',
  environment: 'production'
});

// WebSocket chat
const chatClient = client.chat.connect(sessionId);
chatClient.on('message', (message) => {
  console.log('Received:', message);
});
chatClient.send('Schedule a meeting for tomorrow');
```
