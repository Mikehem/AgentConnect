/**
 * MCP Server API service for SprintConnect frontend
 */

import axios, { AxiosResponse } from 'axios';
import {
  McpServer,
  McpServerCreate,
  McpServerUpdate,
  McpServerListResponse,
  McpServerListParams,
  McpServerHealth,
  McpServerHealthMetrics,
  McpCapabilityDiscovery,
  McpCapabilityTest,
  McpCapabilityTestResult,
  ApiError
} from '../types/mcp';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('id_token');
      localStorage.removeItem('user_info');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

export class McpService {
  /**
   * List MCP servers with optional filtering and pagination
   */
  async listServers(params: McpServerListParams = {}): Promise<McpServerListResponse> {
    try {
      const response: AxiosResponse<McpServerListResponse> = await apiClient.get('/v1/mcp/servers', {
        params: {
          limit: 50,
          offset: 0,
          ...params
        }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get a specific MCP server by ID
   */
  async getServer(serverId: string): Promise<McpServer> {
    try {
      const response: AxiosResponse<McpServer> = await apiClient.get(`/v1/mcp/servers/${serverId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create a new MCP server
   */
  async createServer(serverData: McpServerCreate): Promise<McpServer> {
    try {
      const response: AxiosResponse<McpServer> = await apiClient.post('/v1/mcp/servers', serverData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Register a new MCP server using MCP protocol
   */
  async registerServer(serverData: McpServerCreate): Promise<McpServer> {
    try {
      const response: AxiosResponse<McpServer> = await apiClient.post('/v1/mcp/servers/register', serverData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Update an existing MCP server
   */
  async updateServer(serverId: string, serverData: McpServerUpdate): Promise<McpServer> {
    try {
      const response: AxiosResponse<McpServer> = await apiClient.put(`/v1/mcp/servers/${serverId}`, serverData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Delete an MCP server
   */
  async deleteServer(serverId: string): Promise<{ message: string; deleted_at: string; cleanup_job_id: string | null }> {
    try {
      const response = await apiClient.delete(`/v1/mcp/servers/${serverId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get health status of an MCP server
   */
  async getServerHealth(serverId: string): Promise<McpServerHealth> {
    try {
      const response: AxiosResponse<McpServerHealth> = await apiClient.get(`/v1/mcp/servers/${serverId}/health`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get health metrics for an MCP server
   */
  async getServerHealthMetrics(
    serverId: string,
    params: {
      start_time?: string;
      end_time?: string;
      granularity?: '1m' | '5m' | '1h' | '1d';
    } = {}
  ): Promise<McpServerHealthMetrics> {
    try {
      const response: AxiosResponse<McpServerHealthMetrics> = await apiClient.get(
        `/v1/mcp/servers/${serverId}/health/metrics`,
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Discover capabilities of an MCP server
   */
  async discoverCapabilities(serverId: string): Promise<McpCapabilityDiscovery> {
    try {
      const response: AxiosResponse<McpCapabilityDiscovery> = await apiClient.post(
        `/v1/mcp/servers/${serverId}/capabilities/discover`
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Test a capability method on an MCP server
   */
  async testCapability(serverId: string, testData: McpCapabilityTest): Promise<McpCapabilityTestResult> {
    try {
      const response: AxiosResponse<McpCapabilityTestResult> = await apiClient.post(
        `/v1/mcp/servers/${serverId}/capabilities/test`,
        testData
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get health configuration for an MCP server
   */
  async getHealthConfig(serverId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/mcp/servers/${serverId}/health/config`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Update health configuration for an MCP server
   */
  async updateHealthConfig(serverId: string, config: any): Promise<any> {
    try {
      const response = await apiClient.put(`/v1/mcp/servers/${serverId}/health/config`, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get health alerts for an MCP server
   */
  async getHealthAlerts(serverId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/mcp/servers/${serverId}/health/alerts`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create a health alert for an MCP server
   */
  async createHealthAlert(serverId: string, alertData: any): Promise<any> {
    try {
      const response = await apiClient.post(`/v1/mcp/servers/${serverId}/health/alerts`, alertData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get notification channels for an MCP server
   */
  async getNotificationChannels(serverId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/mcp/servers/${serverId}/health/notifications`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create a notification channel for an MCP server
   */
  async createNotificationChannel(serverId: string, channelData: any): Promise<any> {
    try {
      const response = await apiClient.post(`/v1/mcp/servers/${serverId}/health/notifications`, channelData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Handle API errors consistently
   */
  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const apiError: ApiError = error.response.data;
      const message = typeof apiError.detail === 'string' 
        ? apiError.detail 
        : apiError.detail?.[0]?.msg || apiError.title || 'An error occurred';
      
      const customError = new Error(message);
      (customError as any).status = apiError.status;
      (customError as any).type = apiError.type;
      (customError as any).request_id = apiError.request_id;
      return customError;
    } else if (error.request) {
      // Network error
      return new Error('Network error: Unable to connect to the server');
    } else {
      // Other error
      return new Error(error.message || 'An unexpected error occurred');
    }
  }
}

// Export singleton instance
export const mcpService = new McpService();
