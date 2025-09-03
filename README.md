# SprintConnect

SprintConnect is an enterprise-grade discovery and testing platform for MCP (Model Context Protocol) servers. It enables organizations to register, monitor, and test MCP servers while providing a discovery service for LangGraph Agents to find and connect to appropriate MCP capabilities.

## Core Capabilities

SprintConnect allows you to:
- **Register and manage MCP servers** with comprehensive metadata, tagging, and environment segregation
- **Track MCP utilization and health** with real-time monitoring, metrics, and alerting
- **Test one or more MCP servers** with a LangGraph-based chatbot interface that provides intelligent tool routing
- **Expose a Discovery API** for LangGraph Agents to find servers by capability, tags, environment, and policy

## Design Principles

- **Agentic and LLM-driven**: All orchestration and decision-making leverages LLM intelligence; no server-specific hardcoding
- **Security-by-default**: Least privilege access, encryption everywhere, comprehensive auditability
- **Cloud-native**: Horizontally scalable, stateless services, observability-first architecture
- **Enterprise-ready**: Multi-tenancy, RBAC, compliance controls, and data governance
- **Convention-based**: Artifacts stored under `outputs/<timestamp>/` for consistent organization

## High-Level Architecture

### Frontend
- **React + TypeScript** (Vite build system)
- **WebSocket streaming** for real-time chat and events
- **OIDC/API Key authentication** with role-based UI rendering
- **Responsive design** with accessibility compliance

### Backend
- **FastAPI** (Python 3.11+) with Poetry dependency management
- **Postgres** for primary data storage, **Redis** for caching and queues
- **Celery/RQ workers** for background tasks and async processing
- **Optional Kafka/NATS** for event streaming and decoupled architecture

### Discovery & Chat Orchestration
- **LangGraph-based agent** with pluggable LLM providers
- **Dynamic tool selection** based on server capabilities and user intent
- **Multi-server coordination** for complex workflows
- **Streaming responses** with token-level granularity

### Security & Compliance
- **HashiCorp Vault or cloud KMS** for secret management
- **OTEL tracing** and **Prometheus metrics** for observability
- **Immutable audit logs** with tamper-evident hashing
- **SOC2-aligned controls** and GDPR compliance features

## Repository Structure

```
/
├── frontend/           # React TypeScript application
├── backend/           # FastAPI Python application  
├── infra/             # Infrastructure as Code (Terraform, Helm charts)
├── docs/              # Architecture, API, Security, and Operations documentation
├── outputs/           # Run artifacts and exports (timestamped subdirectories)
├── .cursorrules       # Cursor IDE development guidelines
└── README.md          # This file
```

## Key Features

### MCP Server Management
- **Comprehensive registry** with CRUD operations for server metadata
- **Capability discovery** with automatic introspection and versioning
- **Environment segregation** (dev, staging, production) with promotion workflows
- **Health monitoring** with configurable check intervals and alerting thresholds
- **Credential management** with Vault/KMS integration and automatic rotation

### Discovery Service
- **Capability-based search** for LangGraph Agents to find appropriate servers
- **Tag and metadata filtering** with complex query support
- **Policy-based access control** with fine-grained permissions
- **Caching and performance optimization** for high-throughput discovery requests

### Testing and Validation
- **Multi-server chat interface** with intelligent tool routing
- **Session management** with conversation history and export capabilities
- **Real-time streaming** with WebSocket-based token delivery
- **Tool call orchestration** with LangGraph agent coordination
- **Usage tracking** with detailed metrics and cost attribution

### Enterprise Features
- **Multi-tenancy** with org-level isolation and resource quotas
- **RBAC** with customizable roles and permission sets
- **Audit logging** with immutable trails and compliance reporting
- **Webhooks** for external system integration and event notifications
- **Rate limiting** and quota management per organization and user
- **API versioning** with backward compatibility guarantees

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- HashiCorp Vault or cloud KMS access

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd AgentConnect

# Backend setup
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev
```

## Development Status

🚧 **Planning Phase Complete** - All documentation and architecture designs are finalized. Ready for implementation phase.

### Current State
- ✅ Comprehensive planning and architecture documentation
- ✅ Detailed user stories with acceptance criteria
- ✅ Low-level design and data models
- ✅ Security architecture and compliance framework
- ✅ API specifications and integration patterns
- ⏳ Implementation pending approval

### Next Steps
1. Set up development environment and CI/CD pipeline
2. Implement core backend services (auth, registry, discovery)
3. Build React frontend with WebSocket integration
4. Integrate LangGraph agent for chat orchestration
5. Add monitoring, logging, and observability stack
6. Implement security controls and compliance features

## Contributing

Please refer to the development guidelines in `.cursorrules` and the architecture documentation in `docs/ARCHITECTURE.md` before contributing.

## License

[To be determined - typically proprietary for enterprise solutions]

---

**Note**: This project follows an agentic, LLM-driven approach where all decision-making leverages AI intelligence rather than hardcoded logic. The system is designed to be self-learning and adaptive to different MCP server implementations and usage patterns.
