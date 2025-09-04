import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { vi } from 'vitest';
import { lightTheme } from '../../../styles/theme';
import DiscoveryPage from '../../../pages/discovery/DiscoveryPage';
import { mcpService } from '../../../services/mcpService';
import { McpServer, McpCapabilityDiscovery } from '../../../types/mcp';

// Mock the mcpService
vi.mock('../../../services/mcpService');
const mockedMcpService = mcpService as any;

// Mock the auth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      name: 'Test User',
      email: 'test@example.com',
      org_id: 'org-1',
      org_name: 'Test Org',
      picture: null
    }
  })
}));

// Create a wrapper with all necessary providers
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={lightTheme}>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

// Mock data
const mockServers: McpServer[] = [
  {
    id: 'server-1',
    name: 'Test Server 1',
    description: 'A test MCP server',
    base_url: 'https://test1.example.com',
    environment: 'development',
    status: 'active',
    health_status: 'healthy',
    tags: ['test', 'development'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    org_id: 'org-1',
    owner_user_id: 'user-1'
  },
  {
    id: 'server-2',
    name: 'Production Server',
    description: 'Production MCP server',
    base_url: 'https://prod.example.com',
    environment: 'production',
    status: 'active',
    health_status: 'unhealthy',
    tags: ['production', 'critical'],
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    org_id: 'org-1',
    owner_user_id: 'user-1'
  }
];

const mockDiscoveryResult: McpCapabilityDiscovery = {
  server_id: 'server-1',
  capabilities: {
    tools: {
      'test-tool': {
        name: 'test-tool',
        description: 'A test tool',
        inputSchema: {
          type: 'object',
          properties: {
            message: { type: 'string' }
          }
        }
      }
    },
    resources: {
      'test-resource': {
        name: 'test-resource',
        description: 'A test resource',
        uriTemplate: 'https://example.com/resource/{id}'
      }
    }
  },
  resources: [],
  tools: [],
  discovered_at: '2024-01-01T00:00:00Z',
  errors: [],
  warnings: []
};

describe('DiscoveryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    mockedMcpService.listServers.mockResolvedValue({
      servers: mockServers,
      total: 2,
      limit: 100,
      offset: 0
    });
    
    mockedMcpService.discoverCapabilities.mockResolvedValue(mockDiscoveryResult);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should render the discovery page', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    expect(screen.getByText('MCP Server Discovery')).toBeInTheDocument();
    expect(screen.getByText('Discover and test capabilities of your MCP servers')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
  });

  it('should display server list', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
  });

  it('should display server health status', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getAllByText('healthy')).toHaveLength(1);
      expect(screen.getAllByText('unhealthy')).toHaveLength(1);
    });
  });

  it('should display server environment tags', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getAllByText('development')).toHaveLength(1); // One in environment chip
      expect(screen.getAllByText('production')).toHaveLength(1); // One in environment chip
    });
  });

  it('should display server tags in server info', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('test')).toBeInTheDocument();
      expect(screen.getAllByText('development')).toHaveLength(3); // One in list environment, one in list tags, one in info
    });
  });

  it('should allow server selection', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
  });

  it('should show server info when server is selected', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Server Info')).toBeInTheDocument();
      expect(screen.getByText('A test MCP server')).toBeInTheDocument();
      expect(screen.getAllByText('https://test1.example.com')).toHaveLength(2); // One in list, one in info
    });
  });

  it('should trigger capability discovery when button is clicked', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Discover Capabilities'));
    
    await waitFor(() => {
      expect(mockedMcpService.discoverCapabilities).toHaveBeenCalledWith('server-1');
    });
  });

  it('should show loading state during discovery', async () => {
    // Mock a delayed response
    mockedMcpService.discoverCapabilities.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockDiscoveryResult), 100))
    );
    
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Discover Capabilities'));
    
    await waitFor(() => {
      expect(screen.getByText('Discovering...')).toBeInTheDocument();
    });
  });

  it('should display discovered capabilities', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Discover Capabilities'));
    
    await waitFor(() => {
      expect(screen.getByText('Available Tools (1)')).toBeInTheDocument();
      expect(screen.getByText('test-tool')).toBeInTheDocument();
      expect(screen.getByText('A test tool')).toBeInTheDocument();
    });
  });

  it('should display discovered resources', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Discover Capabilities'));
    
    // Switch to resources tab
    await waitFor(() => {
      expect(screen.getByText('Resources')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Resources'));
    
    await waitFor(() => {
      expect(screen.getByText('Available Resources (1)')).toBeInTheDocument();
      expect(screen.getByText('test-resource')).toBeInTheDocument();
      expect(screen.getByText('A test resource')).toBeInTheDocument();
      expect(screen.getByText('https://example.com/resource/{id}')).toBeInTheDocument();
    });
  });

  it('should handle discovery errors', async () => {
    const errorResult = {
      ...mockDiscoveryResult,
      errors: ['Connection timeout', 'Invalid response format']
    };
    
    mockedMcpService.discoverCapabilities.mockResolvedValue(errorResult);
    
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Discover Capabilities'));
    
    await waitFor(() => {
      expect(screen.getByText('Discovery completed with warnings: Connection timeout, Invalid response format')).toBeInTheDocument();
    });
  });

  it('should handle empty discovery results', async () => {
    const emptyResult = {
      ...mockDiscoveryResult,
      capabilities: {
        tools: {},
        resources: {}
      }
    };
    
    mockedMcpService.discoverCapabilities.mockResolvedValue(emptyResult);
    
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Discover Capabilities')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Discover Capabilities'));
    
    await waitFor(() => {
      expect(screen.getByText('No tools discovered for this server.')).toBeInTheDocument();
    });
  });

  it('should filter servers by search term', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('Search servers by name, description, or tags...');
    fireEvent.change(searchInput, { target: { value: 'production' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Test Server 1')).not.toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
  });

  it('should show empty state when no servers match search', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('Search servers by name, description, or tags...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    
    await waitFor(() => {
      expect(screen.queryByText('Test Server 1')).not.toBeInTheDocument();
      expect(screen.queryByText('Production Server')).not.toBeInTheDocument();
    });
  });

  it('should handle server loading error', async () => {
    mockedMcpService.listServers.mockRejectedValue(new Error('Failed to fetch servers'));
    
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load servers: Failed to fetch servers')).toBeInTheDocument();
    });
  });

  it('should show loading state while fetching servers', async () => {
    mockedMcpService.listServers.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ servers: mockServers, total: 2, limit: 100, offset: 0 }), 100))
    );
    
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should show select server message when no server is selected', async () => {
    render(<DiscoveryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select a Server')).toBeInTheDocument();
      expect(screen.getByText('Choose a server from the list to discover its capabilities')).toBeInTheDocument();
    });
  });
});
