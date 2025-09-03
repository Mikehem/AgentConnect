# SprintConnect Data Model

## Overview

This document defines the complete database schema for SprintConnect, including all tables, relationships, indexes, and constraints. The data model is designed for PostgreSQL 14+ and supports multi-tenancy, audit logging, and enterprise-scale operations.

## Database Design Principles

### Multi-Tenancy
- Organization-level isolation for all user data
- Shared infrastructure tables (system configurations, policies)
- Row-level security (RLS) for data protection
- Foreign key constraints to ensure data consistency

### Audit and Compliance
- Immutable audit logs with cryptographic integrity
- Comprehensive tracking of all data changes
- PII identification and protection
- Data retention and deletion policies

### Performance and Scalability
- Strategic indexing for common query patterns
- Partitioning for large tables (audit logs, usage events)
- Optimized JSON storage for flexible metadata
- Connection pooling and query optimization

### Security
- Encrypted sensitive data at column level
- Vault integration for credential storage
- Role-based access control (RBAC)
- Data classification and handling

## Core Entities

### Organizations and Users

#### organizations
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB NOT NULL DEFAULT '{}',
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT organizations_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT organizations_slug_check 
        CHECK (slug ~ '^[a-z0-9\-]+$'),
    CONSTRAINT organizations_status_check 
        CHECK (status IN ('active', 'suspended', 'deleted'))
);

-- Indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_created_at ON organizations(created_at);

-- Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
```

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    oidc_subject VARCHAR(255),
    roles TEXT[] NOT NULL DEFAULT '{}',
    settings JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT users_email_check 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT users_status_check 
        CHECK (status IN ('active', 'suspended', 'deleted')),
    CONSTRAINT users_roles_check 
        CHECK (array_length(roles, 1) >= 1),
    
    UNIQUE(org_id, email)
);

-- Indexes
CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oidc_subject ON users(oidc_subject);
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_last_login ON users(last_login_at);
CREATE INDEX idx_users_roles ON users USING GIN(roles);

-- Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

#### api_keys
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    key_hash VARCHAR(128) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT api_keys_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT api_keys_key_hash_check 
        CHECK (char_length(key_hash) >= 64),
    CONSTRAINT api_keys_rate_limit_check 
        CHECK (rate_limit_per_minute > 0),
    CONSTRAINT api_keys_status_check 
        CHECK (status IN ('active', 'revoked', 'expired'))
);

-- Indexes
CREATE INDEX idx_api_keys_org_id ON api_keys(org_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_status ON api_keys(status);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_api_keys_scopes ON api_keys USING GIN(scopes);

-- Row Level Security
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
```

### MCP Server Management

#### mcp_servers
```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    environment VARCHAR(50) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    ws_url VARCHAR(500),
    tags TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    policy_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_discovery',
    health_status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    last_health_check_at TIMESTAMPTZ,
    last_discovery_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT mcp_servers_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT mcp_servers_environment_check 
        CHECK (environment IN ('development', 'staging', 'production')),
    CONSTRAINT mcp_servers_base_url_check 
        CHECK (base_url ~* '^https?://'),
    CONSTRAINT mcp_servers_ws_url_check 
        CHECK (ws_url IS NULL OR ws_url ~* '^wss?://'),
    CONSTRAINT mcp_servers_status_check 
        CHECK (status IN ('pending_discovery', 'active', 'inactive', 'error', 'deleted')),
    CONSTRAINT mcp_servers_health_status_check 
        CHECK (health_status IN ('healthy', 'unhealthy', 'degraded', 'unknown')),
    
    UNIQUE(org_id, name, environment)
);

-- Indexes
CREATE INDEX idx_mcp_servers_org_id ON mcp_servers(org_id);
CREATE INDEX idx_mcp_servers_environment ON mcp_servers(environment);
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_mcp_servers_health_status ON mcp_servers(health_status);
CREATE INDEX idx_mcp_servers_owner_user_id ON mcp_servers(owner_user_id);
CREATE INDEX idx_mcp_servers_tags ON mcp_servers USING GIN(tags);
CREATE INDEX idx_mcp_servers_metadata ON mcp_servers USING GIN(metadata);
CREATE INDEX idx_mcp_servers_created_at ON mcp_servers(created_at);
CREATE INDEX idx_mcp_servers_updated_at ON mcp_servers(updated_at);

-- Full-text search index
CREATE INDEX idx_mcp_servers_search ON mcp_servers USING GIN(
    to_tsvector('english', name || ' ' || COALESCE(description, ''))
);

-- Row Level Security
ALTER TABLE mcp_servers ENABLE ROW LEVEL SECURITY;
```

#### mcp_credentials
```sql
CREATE TABLE mcp_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mcp_server_id UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    credential_type VARCHAR(50) NOT NULL,
    vault_path VARCHAR(500) NOT NULL,
    scope TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    
    CONSTRAINT mcp_credentials_type_check 
        CHECK (credential_type IN ('bearer_token', 'oauth2', 'api_key', 'mtls', 'basic_auth')),
    CONSTRAINT mcp_credentials_vault_path_check 
        CHECK (char_length(vault_path) >= 1),
    
    UNIQUE(mcp_server_id, credential_type)
);

-- Indexes
CREATE INDEX idx_mcp_credentials_server_id ON mcp_credentials(mcp_server_id);
CREATE INDEX idx_mcp_credentials_type ON mcp_credentials(credential_type);
CREATE INDEX idx_mcp_credentials_expires_at ON mcp_credentials(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_mcp_credentials_rotated_at ON mcp_credentials(rotated_at);

-- Row Level Security
ALTER TABLE mcp_credentials ENABLE ROW LEVEL SECURITY;
```

#### mcp_capabilities
```sql
CREATE TABLE mcp_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mcp_server_id UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    schema_json JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    enabled BOOLEAN NOT NULL DEFAULT true,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT mcp_capabilities_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT mcp_capabilities_schema_check 
        CHECK (jsonb_typeof(schema_json) = 'object'),
    
    UNIQUE(mcp_server_id, name)
);

-- Indexes
CREATE INDEX idx_mcp_capabilities_server_id ON mcp_capabilities(mcp_server_id);
CREATE INDEX idx_mcp_capabilities_name ON mcp_capabilities(name);
CREATE INDEX idx_mcp_capabilities_enabled ON mcp_capabilities(enabled);
CREATE INDEX idx_mcp_capabilities_discovered_at ON mcp_capabilities(discovered_at);
CREATE INDEX idx_mcp_capabilities_schema ON mcp_capabilities USING GIN(schema_json);
CREATE INDEX idx_mcp_capabilities_metadata ON mcp_capabilities USING GIN(metadata);

-- Full-text search for capability discovery
CREATE INDEX idx_mcp_capabilities_search ON mcp_capabilities USING GIN(
    to_tsvector('english', name || ' ' || COALESCE(description, ''))
);

-- Row Level Security
ALTER TABLE mcp_capabilities ENABLE ROW LEVEL SECURITY;
```

#### mcp_health_checks
```sql
CREATE TABLE mcp_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mcp_server_id UUID NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    check_details JSONB NOT NULL DEFAULT '{}',
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT mcp_health_checks_status_check 
        CHECK (status IN ('healthy', 'unhealthy', 'timeout', 'error')),
    CONSTRAINT mcp_health_checks_response_time_check 
        CHECK (response_time_ms >= 0)
);

-- Indexes
CREATE INDEX idx_mcp_health_checks_server_id ON mcp_health_checks(mcp_server_id);
CREATE INDEX idx_mcp_health_checks_status ON mcp_health_checks(status);
CREATE INDEX idx_mcp_health_checks_checked_at ON mcp_health_checks(checked_at);

-- Partitioning by month for performance
CREATE TABLE mcp_health_checks_y2024m01 PARTITION OF mcp_health_checks
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Row Level Security
ALTER TABLE mcp_health_checks ENABLE ROW LEVEL SECURITY;
```

### Chat and Session Management

#### chat_sessions
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    selected_servers UUID[] NOT NULL,
    llm_model VARCHAR(100) NOT NULL,
    llm_config JSONB NOT NULL DEFAULT '{}',
    session_config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    total_tokens_in INTEGER NOT NULL DEFAULT 0,
    total_tokens_out INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    
    CONSTRAINT chat_sessions_title_check 
        CHECK (char_length(title) >= 1),
    CONSTRAINT chat_sessions_selected_servers_check 
        CHECK (array_length(selected_servers, 1) >= 1),
    CONSTRAINT chat_sessions_llm_model_check 
        CHECK (char_length(llm_model) >= 1),
    CONSTRAINT chat_sessions_status_check 
        CHECK (status IN ('active', 'closed', 'error', 'archived')),
    CONSTRAINT chat_sessions_tokens_check 
        CHECK (total_tokens_in >= 0 AND total_tokens_out >= 0),
    CONSTRAINT chat_sessions_cost_check 
        CHECK (estimated_cost_usd >= 0)
);

-- Indexes
CREATE INDEX idx_chat_sessions_org_id ON chat_sessions(org_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at);
CREATE INDEX idx_chat_sessions_selected_servers ON chat_sessions USING GIN(selected_servers);
CREATE INDEX idx_chat_sessions_llm_model ON chat_sessions(llm_model);

-- Full-text search
CREATE INDEX idx_chat_sessions_search ON chat_sessions USING GIN(
    to_tsvector('english', title)
);

-- Row Level Security
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
```

#### chat_messages
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    tool_calls JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chat_messages_role_check 
        CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    CONSTRAINT chat_messages_content_check 
        CHECK (char_length(content) >= 1),
    CONSTRAINT chat_messages_tool_calls_check 
        CHECK (jsonb_typeof(tool_calls) = 'array'),
    CONSTRAINT chat_messages_tokens_check 
        CHECK (tokens_in >= 0 AND tokens_out >= 0),
    CONSTRAINT chat_messages_processing_time_check 
        CHECK (processing_time_ms >= 0)
);

-- Indexes
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX idx_chat_messages_tool_calls ON chat_messages USING GIN(tool_calls);

-- Full-text search on message content
CREATE INDEX idx_chat_messages_search ON chat_messages USING GIN(
    to_tsvector('english', content)
);

-- Row Level Security
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
```

### Usage Tracking and Analytics

#### usage_events
```sql
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    mcp_server_id UUID REFERENCES mcp_servers(id) ON DELETE SET NULL,
    capability_id UUID REFERENCES mcp_capabilities(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    duration_ms INTEGER,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    status VARCHAR(20) NOT NULL,
    error_code VARCHAR(50),
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT usage_events_event_type_check 
        CHECK (event_type IN ('chat_message', 'tool_call', 'capability_discovery', 'health_check', 'api_request')),
    CONSTRAINT usage_events_duration_check 
        CHECK (duration_ms >= 0),
    CONSTRAINT usage_events_tokens_check 
        CHECK (tokens_in >= 0 AND tokens_out >= 0),
    CONSTRAINT usage_events_cost_check 
        CHECK (estimated_cost_usd >= 0),
    CONSTRAINT usage_events_status_check 
        CHECK (status IN ('success', 'error', 'timeout', 'cancelled'))
);

-- Indexes for analytics queries
CREATE INDEX idx_usage_events_org_id_created_at ON usage_events(org_id, created_at);
CREATE INDEX idx_usage_events_user_id_created_at ON usage_events(user_id, created_at);
CREATE INDEX idx_usage_events_server_id_created_at ON usage_events(mcp_server_id, created_at);
CREATE INDEX idx_usage_events_capability_id_created_at ON usage_events(capability_id, created_at);
CREATE INDEX idx_usage_events_event_type ON usage_events(event_type);
CREATE INDEX idx_usage_events_status ON usage_events(status);
CREATE INDEX idx_usage_events_created_at ON usage_events(created_at);

-- Partitioning by month for large-scale analytics
CREATE TABLE usage_events_y2024m01 PARTITION OF usage_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Row Level Security
ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY;
```

### Security and Audit

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    actor_type VARCHAR(50) NOT NULL,
    actor_id UUID,
    target_type VARCHAR(50),
    target_id UUID,
    action VARCHAR(100) NOT NULL,
    result VARCHAR(20) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    context JSONB NOT NULL DEFAULT '{}',
    record_hash VARCHAR(128) NOT NULL,
    previous_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT audit_logs_actor_type_check 
        CHECK (actor_type IN ('user', 'api_key', 'system', 'automated_process')),
    CONSTRAINT audit_logs_result_check 
        CHECK (result IN ('success', 'failure', 'error', 'partial')),
    CONSTRAINT audit_logs_record_hash_check 
        CHECK (char_length(record_hash) = 64)
);

-- Indexes for audit queries
CREATE INDEX idx_audit_logs_org_id_created_at ON audit_logs(org_id, created_at);
CREATE INDEX idx_audit_logs_actor_id_created_at ON audit_logs(actor_id, created_at);
CREATE INDEX idx_audit_logs_target_id_created_at ON audit_logs(target_id, created_at);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_result ON audit_logs(result);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_record_hash ON audit_logs(record_hash);

-- Full-text search on audit details
CREATE INDEX idx_audit_logs_search ON audit_logs USING GIN(
    to_tsvector('english', action || ' ' || COALESCE(details->>'description', ''))
);

-- Partitioning by month for performance and compliance
CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- No RLS - audit logs need to be immutable and globally accessible to auditors
```

### Policy and Access Control

#### policies
```sql
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    policy_type VARCHAR(50) NOT NULL,
    rules JSONB NOT NULL,
    targets JSONB NOT NULL DEFAULT '[]',
    enabled BOOLEAN NOT NULL DEFAULT true,
    version INTEGER NOT NULL DEFAULT 1,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT policies_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT policies_policy_type_check 
        CHECK (policy_type IN ('access_control', 'data_retention', 'usage_quota', 'security')),
    CONSTRAINT policies_rules_check 
        CHECK (jsonb_typeof(rules) = 'object'),
    CONSTRAINT policies_targets_check 
        CHECK (jsonb_typeof(targets) = 'array'),
    CONSTRAINT policies_version_check 
        CHECK (version > 0),
    
    UNIQUE(org_id, name)
);

-- Indexes
CREATE INDEX idx_policies_org_id ON policies(org_id);
CREATE INDEX idx_policies_policy_type ON policies(policy_type);
CREATE INDEX idx_policies_enabled ON policies(enabled);
CREATE INDEX idx_policies_created_at ON policies(created_at);
CREATE INDEX idx_policies_rules ON policies USING GIN(rules);
CREATE INDEX idx_policies_targets ON policies USING GIN(targets);

-- Row Level Security
ALTER TABLE policies ENABLE ROW LEVEL SECURITY;
```

### Integration and Notifications

#### webhooks
```sql
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255),
    event_types TEXT[] NOT NULL,
    filters JSONB NOT NULL DEFAULT '{}',
    retry_config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_triggered_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    failure_count INTEGER NOT NULL DEFAULT 0,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT webhooks_name_check 
        CHECK (char_length(name) >= 1),
    CONSTRAINT webhooks_url_check 
        CHECK (url ~* '^https://'),
    CONSTRAINT webhooks_event_types_check 
        CHECK (array_length(event_types, 1) >= 1),
    CONSTRAINT webhooks_status_check 
        CHECK (status IN ('active', 'inactive', 'failed')),
    CONSTRAINT webhooks_failure_count_check 
        CHECK (failure_count >= 0),
    
    UNIQUE(org_id, name)
);

-- Indexes
CREATE INDEX idx_webhooks_org_id ON webhooks(org_id);
CREATE INDEX idx_webhooks_status ON webhooks(status);
CREATE INDEX idx_webhooks_event_types ON webhooks USING GIN(event_types);
CREATE INDEX idx_webhooks_last_triggered_at ON webhooks(last_triggered_at);

-- Row Level Security
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
```

#### webhook_deliveries
```sql
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    response_time_ms INTEGER,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT webhook_deliveries_attempt_number_check 
        CHECK (attempt_number > 0),
    CONSTRAINT webhook_deliveries_response_status_check 
        CHECK (response_status BETWEEN 100 AND 599),
    CONSTRAINT webhook_deliveries_response_time_check 
        CHECK (response_time_ms >= 0),
    CONSTRAINT webhook_deliveries_status_check 
        CHECK (status IN ('pending', 'delivered', 'failed', 'cancelled'))
);

-- Indexes
CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_event_id ON webhook_deliveries(event_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_created_at ON webhook_deliveries(created_at);

-- Partitioning by month
CREATE TABLE webhook_deliveries_y2024m01 PARTITION OF webhook_deliveries
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Row Level Security
ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;
```

## Views and Materialized Views

### Server Discovery View
```sql
CREATE VIEW server_discovery_view AS
SELECT 
    s.id,
    s.org_id,
    s.name,
    s.description,
    s.environment,
    s.base_url,
    s.ws_url,
    s.tags,
    s.metadata,
    s.status,
    s.health_status,
    s.created_at,
    s.updated_at,
    ARRAY_AGG(
        DISTINCT jsonb_build_object(
            'id', c.id,
            'name', c.name,
            'description', c.description,
            'version', c.version,
            'enabled', c.enabled
        )
    ) FILTER (WHERE c.id IS NOT NULL) AS capabilities,
    COUNT(c.id) FILTER (WHERE c.enabled = true) AS enabled_capability_count
FROM mcp_servers s
LEFT JOIN mcp_capabilities c ON s.id = c.mcp_server_id
WHERE s.deleted_at IS NULL
GROUP BY s.id, s.org_id, s.name, s.description, s.environment, 
         s.base_url, s.ws_url, s.tags, s.metadata, s.status, 
         s.health_status, s.created_at, s.updated_at;
```

### Usage Analytics Materialized View
```sql
CREATE MATERIALIZED VIEW daily_usage_analytics AS
SELECT 
    org_id,
    user_id,
    mcp_server_id,
    DATE(created_at) AS usage_date,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE event_type = 'chat_message') AS chat_messages,
    COUNT(*) FILTER (WHERE event_type = 'tool_call') AS tool_calls,
    SUM(tokens_in) AS total_tokens_in,
    SUM(tokens_out) AS total_tokens_out,
    SUM(estimated_cost_usd) AS total_cost_usd,
    AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) AS avg_duration_ms,
    COUNT(*) FILTER (WHERE status = 'error') AS error_count
FROM usage_events
GROUP BY org_id, user_id, mcp_server_id, DATE(created_at);

-- Index for fast queries
CREATE INDEX idx_daily_usage_analytics_org_date ON daily_usage_analytics(org_id, usage_date);
CREATE INDEX idx_daily_usage_analytics_server_date ON daily_usage_analytics(mcp_server_id, usage_date);

-- Refresh policy
CREATE OR REPLACE FUNCTION refresh_daily_usage_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_usage_analytics;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh every hour
SELECT cron.schedule('refresh-usage-analytics', '0 * * * *', 'SELECT refresh_daily_usage_analytics();');
```

## Functions and Triggers

### Audit Logging Trigger
```sql
CREATE OR REPLACE FUNCTION audit_log_changes()
RETURNS TRIGGER AS $$
DECLARE
    audit_record RECORD;
    current_user_id UUID;
    hash_input TEXT;
    record_hash TEXT;
BEGIN
    -- Get current user context
    current_user_id := current_setting('app.current_user_id', true)::UUID;
    
    -- Build audit record
    audit_record := (
        COALESCE(NEW.org_id, OLD.org_id),  -- org_id
        TG_TABLE_NAME || '.' || TG_OP,     -- event_type
        'user',                             -- actor_type
        current_user_id,                    -- actor_id
        TG_TABLE_NAME,                      -- target_type
        COALESCE(NEW.id, OLD.id),          -- target_id
        TG_OP,                             -- action
        'success',                          -- result
        CASE 
            WHEN TG_OP = 'INSERT' THEN row_to_json(NEW)
            WHEN TG_OP = 'UPDATE' THEN jsonb_build_object('old', row_to_json(OLD), 'new', row_to_json(NEW))
            WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)
        END,                               -- details
        jsonb_build_object(
            'table_name', TG_TABLE_NAME,
            'schema_name', TG_TABLE_SCHEMA,
            'operation', TG_OP
        ),                                 -- context
        NOW()                              -- created_at
    );
    
    -- Calculate hash for integrity
    hash_input := audit_record::TEXT;
    record_hash := encode(digest(hash_input, 'sha256'), 'hex');
    
    -- Insert audit log
    INSERT INTO audit_logs (
        org_id, event_type, actor_type, actor_id, target_type, target_id,
        action, result, details, context, record_hash, created_at
    ) VALUES (
        audit_record.org_id, audit_record.event_type, audit_record.actor_type,
        audit_record.actor_id, audit_record.target_type, audit_record.target_id,
        audit_record.action, audit_record.result, audit_record.details,
        audit_record.context, record_hash, audit_record.created_at
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply to key tables
CREATE TRIGGER audit_mcp_servers 
    AFTER INSERT OR UPDATE OR DELETE ON mcp_servers
    FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

CREATE TRIGGER audit_users 
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_log_changes();

CREATE TRIGGER audit_api_keys 
    AFTER INSERT OR UPDATE OR DELETE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION audit_log_changes();
```

### Updated Timestamp Trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mcp_servers_updated_at 
    BEFORE UPDATE ON mcp_servers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Row Level Security Policies

### Organizations
```sql
-- Users can only see their own organization
CREATE POLICY organizations_isolation ON organizations
    FOR ALL TO authenticated_user
    USING (id = current_setting('app.current_org_id')::UUID);
```

### Users
```sql
-- Users can see users in their organization
CREATE POLICY users_org_isolation ON users
    FOR ALL TO authenticated_user
    USING (org_id = current_setting('app.current_org_id')::UUID);

-- Users can only modify their own profile (except admins)
CREATE POLICY users_self_modify ON users
    FOR UPDATE TO authenticated_user
    USING (
        id = current_setting('app.current_user_id')::UUID 
        OR 'admin' = ANY(current_setting('app.current_user_roles')::TEXT[])
    );
```

### MCP Servers
```sql
-- Users can only access servers in their organization
CREATE POLICY mcp_servers_org_isolation ON mcp_servers
    FOR ALL TO authenticated_user
    USING (org_id = current_setting('app.current_org_id')::UUID);

-- Only owners and admins can delete servers
CREATE POLICY mcp_servers_delete_permission ON mcp_servers
    FOR DELETE TO authenticated_user
    USING (
        owner_user_id = current_setting('app.current_user_id')::UUID
        OR 'admin' = ANY(current_setting('app.current_user_roles')::TEXT[])
    );
```

## Database Maintenance

### Partitioning Strategy
```sql
-- Function to create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name TEXT,
    start_date DATE
) RETURNS void AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    end_date := start_date + INTERVAL '1 month';
    partition_name := table_name || '_y' || EXTRACT(year FROM start_date) || 'm' || LPAD(EXTRACT(month FROM start_date)::TEXT, 2, '0');
    
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule partition creation
SELECT cron.schedule('create-partitions', '0 0 1 * *', $$
    SELECT create_monthly_partition('usage_events', DATE_TRUNC('month', NOW() + INTERVAL '1 month'));
    SELECT create_monthly_partition('audit_logs', DATE_TRUNC('month', NOW() + INTERVAL '1 month'));
    SELECT create_monthly_partition('webhook_deliveries', DATE_TRUNC('month', NOW() + INTERVAL '1 month'));
    SELECT create_monthly_partition('mcp_health_checks', DATE_TRUNC('month', NOW() + INTERVAL '1 month'));
$$);
```

### Index Maintenance
```sql
-- Function to rebuild indexes
CREATE OR REPLACE FUNCTION rebuild_indexes()
RETURNS void AS $$
DECLARE
    index_record RECORD;
BEGIN
    FOR index_record IN 
        SELECT schemaname, tablename, indexname
        FROM pg_indexes 
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
    LOOP
        EXECUTE 'REINDEX INDEX CONCURRENTLY ' || quote_ident(index_record.indexname);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule weekly index maintenance
SELECT cron.schedule('rebuild-indexes', '0 2 * * 0', 'SELECT rebuild_indexes();');
```

### Data Retention
```sql
-- Function to clean old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Clean old health checks (keep 90 days)
    DELETE FROM mcp_health_checks 
    WHERE checked_at < NOW() - INTERVAL '90 days';
    
    -- Clean old webhook deliveries (keep 30 days)
    DELETE FROM webhook_deliveries 
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    -- Clean old usage events (keep 2 years)
    DELETE FROM usage_events 
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Archive old audit logs (keep 7 years)
    -- This would typically move to archive storage
    
    -- Vacuum tables after cleanup
    VACUUM ANALYZE mcp_health_checks, webhook_deliveries, usage_events;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly cleanup
SELECT cron.schedule('cleanup-old-data', '0 3 1 * *', 'SELECT cleanup_old_data();');
```

## Performance Optimization

### Query Performance
```sql
-- Analyze table statistics
SELECT cron.schedule('analyze-tables', '0 1 * * *', $$
    ANALYZE organizations, users, mcp_servers, mcp_capabilities, 
            chat_sessions, chat_messages, usage_events, audit_logs;
$$);

-- Monitor slow queries
CREATE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE mean_time > 100
ORDER BY mean_time DESC;
```

### Connection Pooling Configuration
```sql
-- Recommended PostgreSQL settings for SprintConnect
-- postgresql.conf
/*
max_connections = 200
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 64MB
min_wal_size = 2GB
max_wal_size = 8GB
*/
```

This comprehensive data model provides the foundation for a scalable, secure, and maintainable SprintConnect implementation. The schema supports all planned features while providing flexibility for future enhancements and compliance requirements.
