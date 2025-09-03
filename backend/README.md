# SprintConnect Backend

## Overview

The SprintConnect backend is a FastAPI-based service that provides the core functionality for MCP server discovery, management, and testing. It implements enterprise-grade security, multi-tenancy, and observability features while maintaining high performance and scalability.

## Key Responsibilities

- **MCP Registry Management**: CRUD operations for MCP servers, capabilities, and metadata
- **Discovery Service**: API endpoints for LangGraph Agents to find servers by capability and policy
- **Chat Orchestration**: LangGraph-based agent coordination for multi-server testing
- **Utilization Tracking**: Real-time metrics collection and aggregation
- **Security & Compliance**: Authentication, authorization, audit logging, and data protection
- **Background Processing**: Async tasks for health checks, discovery jobs, and maintenance

## Technology Stack

### Core Framework
- **Python 3.11+** with type hints and async/await patterns
- **FastAPI** for REST API and WebSocket endpoints
- **Pydantic v2** for data validation and serialization
- **Poetry** for dependency management and virtual environments

### Database & Storage
- **PostgreSQL 14+** as primary relational database
- **SQLAlchemy 2.x** or **SQLModel** for ORM and query building
- **Alembic** for database migrations and schema versioning
- **Redis 6+** for caching, session storage, and message queues
- **S3-compatible storage** for artifacts and exports

### Background Processing
- **Celery** or **RQ** for distributed task queues
- **Redis** as message broker and result backend
- **Optional Kafka/NATS** for event streaming and pub/sub

### Security & Secrets
- **HashiCorp Vault** or cloud KMS for secret management
- **OIDC/OAuth2** for authentication with PKCE flow
- **API Keys** with scoped permissions and expiration
- **bcrypt** for password hashing (if local auth is needed)

### Observability
- **OpenTelemetry (OTEL)** for distributed tracing
- **Prometheus** metrics with custom collectors
- **Structured logging** with correlation IDs
- **Health check endpoints** for load balancer integration

## Service Architecture

### API Service
- **REST endpoints** for CRUD operations and queries
- **WebSocket endpoints** for real-time chat streaming
- **Authentication middleware** for token validation and RBAC
- **Rate limiting** and quota enforcement per organization/user
- **Request/response validation** with comprehensive error handling

### Worker Service
- **Discovery jobs** for MCP server capability introspection
- **Health check tasks** with configurable intervals and retry logic
- **Chat tool execution** for async LLM and MCP server calls
- **Maintenance tasks** for cleanup, rotation, and archival
- **Event processing** for webhooks and external integrations

### Scheduler Service
- **Cron-like job scheduling** for periodic tasks
- **Health check orchestration** across all registered servers
- **Credential rotation** on configurable schedules
- **Data retention** and cleanup policies
- **Backup and archival** job coordination

## Configuration

### Environment Variables
```bash
# Application
APP_ENV=development|staging|production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:port/db
REDIS_POOL_SIZE=10

# Authentication
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_DISCOVERY_URL=https://your-provider/.well-known/openid_configuration
JWT_SECRET_KEY=your-jwt-secret
API_KEY_ENCRYPTION_KEY=your-api-key-encryption-key

# Secrets Management
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=your-vault-token
VAULT_NAMESPACE=your-namespace
# OR for cloud KMS
AWS_KMS_KEY_ID=your-kms-key-id
GCP_KMS_KEY_NAME=your-kms-key-name

# LLM & Chat
LLM_PROVIDER=openai|anthropic|azure
LLM_MODEL=gpt-4|claude-3|custom
LLM_API_KEY=your-llm-api-key
LANGGRAPH_CONFIG_PATH=/path/to/langgraph/config

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=100
QUOTA_REQUESTS_PER_DAY=10000

# Security
ALLOWED_EGRESS_HOSTS=api.openai.com,api.anthropic.com,your-mcp-servers.com
CORS_ORIGINS=https://your-frontend.com
CSRF_SECRET_KEY=your-csrf-secret

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces
PROMETHEUS_METRICS_PORT=9090
LOG_FORMAT=json
```

### Secrets in Vault/KMS
Never store secrets in environment variables or configuration files. All sensitive data should be retrieved from:
- **Vault paths**: `secret/sprintconnect/mcp-servers/{server-id}/credentials`
- **KMS encrypted values**: Decrypt on startup or per-request basis
- **Runtime injection**: Via init containers or secret management operators

## API Surface

### Authentication & Authorization
- `POST /auth/token` - Exchange OIDC code for JWT tokens
- `POST /auth/refresh` - Refresh access token using refresh token
- `GET /auth/me` - Get current user profile and permissions
- `POST /auth/api-keys` - Create API key with scoped permissions
- `DELETE /auth/api-keys/{key_id}` - Revoke API key

### MCP Server Registry
- `POST /v1/mcp/servers` - Register new MCP server
- `GET /v1/mcp/servers` - List servers with filtering and pagination
- `GET /v1/mcp/servers/{id}` - Get server details and current status
- `PATCH /v1/mcp/servers/{id}` - Update server metadata and configuration
- `DELETE /v1/mcp/servers/{id}` - Deregister server (soft delete)
- `POST /v1/mcp/servers/{id}/discover` - Trigger capability discovery job
- `GET /v1/mcp/servers/{id}/capabilities` - List discovered capabilities
- `PATCH /v1/mcp/capabilities/{id}` - Update capability configuration
- `GET /v1/mcp/servers/{id}/health` - Get current health status

### Discovery Service (for LangGraph Agents)
- `GET /v1/discovery/servers` - Search servers by capability, tags, environment
- `GET /v1/discovery/capabilities` - Search capabilities by name and schema
- `GET /v1/discovery/policies` - Get applicable policies for server access

### Chat & Testing
- `POST /v1/chat/sessions` - Create new chat session with server selection
- `WS /v1/chat/sessions/{id}/stream` - WebSocket for streaming chat
- `GET /v1/chat/sessions` - List user's chat sessions
- `GET /v1/chat/sessions/{id}` - Get session details and message history
- `GET /v1/chat/sessions/{id}/export` - Export session as JSON/CSV
- `DELETE /v1/chat/sessions/{id}` - Delete chat session and history

### Metrics & Utilization
- `GET /v1/metrics/usage` - Aggregated usage metrics with grouping options
- `GET /v1/metrics/top` - Top servers/capabilities by usage dimension
- `GET /v1/metrics/health` - System health and availability metrics
- `GET /v1/metrics/costs` - Token usage and cost attribution by org/user

### Administration
- `GET /v1/audit/logs` - Query audit logs with filtering and export
- `POST /v1/webhooks` - Create webhook subscription
- `GET /v1/webhooks` - List organization's webhooks
- `PATCH /v1/webhooks/{id}` - Update webhook configuration
- `DELETE /v1/webhooks/{id}` - Delete webhook subscription
- `POST /v1/policies` - Create access policy
- `GET /v1/policies` - List organization's policies

### Health & Monitoring
- `GET /health` - Basic health check for load balancers
- `GET /health/detailed` - Detailed health including dependencies
- `GET /metrics` - Prometheus metrics endpoint
- `GET /ready` - Readiness probe for Kubernetes

## Data Models

### Core Entities
See `../docs/DATA_MODEL.md` for complete schema definitions.

**Key models include:**
- `Organization` - Multi-tenant isolation
- `User` - Identity and role assignment
- `McpServer` - Registered MCP server metadata
- `McpCapability` - Discovered server capabilities
- `McpCredential` - Vault/KMS-backed authentication
- `ChatSession` - Multi-server test sessions
- `UsageEvent` - Detailed utilization tracking
- `AuditLog` - Immutable security audit trail

### Relationships
- Organizations contain users, servers, and policies
- Servers have capabilities and credentials (1:many)
- Chat sessions reference multiple servers and generate usage events
- All actions create audit log entries with full context

## Development Guidelines

### Code Style & Quality
- **Formatting**: Black (line length 88) and isort for import organization
- **Linting**: Ruff for fast Python linting with comprehensive rule set
- **Type checking**: mypy with strict mode for all modules
- **Testing**: pytest with coverage reporting (minimum 90% coverage)
- **Documentation**: Docstrings for all public functions and classes

### Testing Strategy
```bash
# Unit tests - fast, isolated, no external dependencies
pytest tests/unit/ -v

# Integration tests - real Postgres/Redis via Docker
pytest tests/integration/ -v --docker

# API tests - full HTTP client testing
pytest tests/api/ -v

# End-to-end tests - full system with external dependencies
pytest tests/e2e/ -v --slow
```

### Database Migrations
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Add MCP server registry"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Local Development
```bash
# Install dependencies
poetry install --with dev,test

# Start services (Postgres, Redis)
docker-compose up -d

# Run database migrations
poetry run alembic upgrade head

# Start API server with hot reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start worker in separate terminal
poetry run celery -A app.worker worker --loglevel=info

# Start scheduler
poetry run celery -A app.worker beat --loglevel=info
```

### Output Conventions
All run artifacts, exports, and generated files should be stored under:
```
outputs/
├── 2024-01-15T10-30-00/    # Timestamp-based directories
│   ├── chat-exports/
│   ├── discovery-results/
│   ├── health-reports/
│   └── usage-analytics/
└── latest/                 # Symlink to most recent
```

## Security Considerations

### Input Validation
- All API inputs validated with Pydantic models
- SQL injection prevention via parameterized queries
- XSS prevention with output encoding
- CSRF protection for cookie-based sessions

### SSRF Prevention
- Allowlist of permitted egress hosts for MCP server connections
- URL validation and normalization
- Timeout and size limits for external requests
- Network isolation for worker processes

### Rate Limiting & DDoS Protection
- Per-organization and per-user rate limits
- Exponential backoff for failed requests
- Queue depth monitoring and circuit breakers
- IP-based rate limiting for unauthenticated endpoints

### Audit & Compliance
- Immutable audit logs with cryptographic integrity
- PII identification and encryption
- Data retention and deletion policies
- SOC2 and GDPR compliance controls

## Monitoring & Observability

### Application Metrics
- Request/response latency percentiles
- Error rates by endpoint and status code
- Active connections and queue depths
- Background job processing times
- LLM token usage and costs

### Business Metrics
- MCP server registration and discovery rates
- Chat session creation and duration
- Capability usage patterns
- User engagement and retention

### Alerting Thresholds
- P95 latency > 500ms for 5 minutes
- Error rate > 1% for 2 minutes
- Queue depth > 1000 items
- Database connection pool exhaustion
- Failed health checks for critical servers

## Deployment & Scaling

### Container Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --only=main
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Horizontal Scaling
- Stateless API servers behind load balancer
- Separate worker pools for different task types
- Database read replicas for analytics queries
- Redis clustering for high availability

### Performance Tuning
- Connection pooling with appropriate sizing
- Query optimization and indexing strategies
- Caching layers for frequent read operations
- Async processing for expensive operations

## Future Enhancements

### Planned Features
- Multi-region deployment with data sovereignty
- Advanced analytics with ML-driven insights
- GraphQL API for flexible client queries
- Plugin system for custom MCP server types
- Advanced workflow orchestration beyond simple chat

### Technical Debt & Improvements
- Migration to SQLModel when stable
- Evaluation of FastAPI alternatives (e.g., Litestar)
- Consideration of event sourcing for audit trails
- Investigation of serverless deployment options
