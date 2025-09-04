/**
 * TypeScript types for MCP (Model Context Protocol) server management
 */

export interface McpServer {
  id: string;
  name: string;
  description: string;
  base_url: string;
  environment: 'development' | 'staging' | 'production';
  status: 'active' | 'inactive' | 'archived';
  health_status: 'healthy' | 'unhealthy' | 'degraded' | 'unknown';
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  org_id: string;
  owner_user_id: string;
  tags: string[];
  capabilities?: McpCapabilities;
  server_metadata?: McpServerMetadata;
}

export interface McpCapabilities {
  tools?: string[];
  resources?: string[];
  [key: string]: any;
}

export interface McpServerMetadata {
  version?: string;
  protocol_version?: string;
  health_config?: HealthConfig;
  [key: string]: any;
}

export interface HealthConfig {
  enabled: boolean;
  check_interval_seconds: number;
  timeout_seconds: number;
  retry_count: number;
  alert_thresholds?: {
    response_time_ms?: number;
    uptime_percentage?: number;
  };
}

export interface McpServerCreate {
  name: string;
  description: string;
  base_url: string;
  environment: 'development' | 'staging' | 'production';
  tags: string[];
  capabilities?: McpCapabilities;
}

export interface McpServerUpdate {
  name?: string;
  description?: string;
  tags?: string[];
  capabilities?: McpCapabilities;
}

export interface McpServerListResponse {
  servers: McpServer[];
  total: number;
  limit: number;
  offset: number;
}

export interface McpServerListParams {
  environment?: 'development' | 'staging' | 'production';
  status?: 'active' | 'inactive' | 'archived';
  health_status?: 'healthy' | 'unhealthy' | 'degraded' | 'unknown';
  limit?: number;
  offset?: number;
  search?: string;
}

export interface McpServerHealth {
  server_id: string;
  health_status: 'healthy' | 'unhealthy' | 'degraded' | 'unknown';
  last_check_at: string;
  uptime_percentage: number;
  response_time_ms?: number;
  error_message?: string;
  checks?: {
    connectivity?: 'healthy' | 'unhealthy';
    handshake?: 'healthy' | 'unhealthy';
    capabilities?: 'healthy' | 'unhealthy';
  };
}

export interface McpServerHealthMetrics {
  server_id: string;
  period: {
    start_time: string;
    end_time: string;
  };
  summary: {
    total_checks: number;
    successful_checks: number;
    failed_checks: number;
    uptime_percentage: number;
    avg_response_time_ms: number;
    max_response_time_ms: number;
  };
  metrics: Array<{
    timestamp: string;
    status: 'healthy' | 'unhealthy' | 'degraded';
    response_time_ms: number;
    uptime: boolean;
  }>;
}

export interface McpCapabilityDiscovery {
  server_id: string;
  discovered_at: string;
  capabilities: {
    tools?: Record<string, McpToolCapability>;
    resources?: Record<string, McpResourceCapability>;
  };
  resources: any[];
  tools: any[];
  errors: string[];
  warnings: string[];
}

export interface McpToolCapability {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, any>;
    required?: string[];
  };
}

export interface McpResourceCapability {
  name: string;
  description: string;
  uriTemplate: string;
}

export interface McpCapabilityTest {
  method: string;
  params: {
    name: string;
    arguments: Record<string, any>;
  };
}

export interface McpCapabilityTestResult {
  success: boolean;
  result?: any;
  error?: string;
  execution_time_ms: number;
}

// Form validation schemas
export interface McpServerFormData {
  name: string;
  description: string;
  base_url: string;
  environment: 'development' | 'staging' | 'production';
  tags: string[];
}

export interface McpServerFormErrors {
  name?: string;
  description?: string;
  base_url?: string;
  environment?: string;
  tags?: string;
  general?: string;
}

// Filter and search types
export interface McpServerFilters {
  environment?: string[];
  status?: string[];
  health_status?: string[];
  tags?: string[];
  date_range?: {
    start: string;
    end: string;
  };
}

export interface McpServerSort {
  field: 'name' | 'created_at' | 'updated_at' | 'health_status';
  direction: 'asc' | 'desc';
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  request_id?: string;
}

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string | Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
  request_id: string;
}

// WebSocket message types
export interface McpServerWebSocketMessage {
  type: 'health_update' | 'status_change' | 'capability_update';
  server_id: string;
  data: any;
  timestamp: string;
}
