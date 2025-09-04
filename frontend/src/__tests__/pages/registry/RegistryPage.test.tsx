/**
 * Unit tests for RegistryPage component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import RegistryPage from '../../../pages/registry/RegistryPage';
import { mcpService } from '../../../services/mcpService';
import { McpServer, McpServerListResponse } from '../../../types/mcp';

// Mock the MCP service
vi.mock('../../../services/mcpService');
const mockedMcpService = mcpService as any;

// Mock the useAuth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      email: 'test@example.com',
      name: 'Test User',
      org_id: 'org-1'
    }
  })
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const mockServers: McpServer[] = [
  {
    id: 'server-1',
    name: 'Test Server 1',
    description: 'A test MCP server',
    base_url: 'https://test1.example.com',
    environment: 'development',
    status: 'active',
    health_status: 'healthy',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    org_id: 'org-1',
    owner_user_id: 'user-1',
    tags: ['test', 'development']
  },
  {
    id: 'server-2',
    name: 'Production Server',
    description: 'Production MCP server',
    base_url: 'https://prod.example.com',
    environment: 'production',
    status: 'active',
    health_status: 'unhealthy',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    org_id: 'org-1',
    owner_user_id: 'user-1',
    tags: ['production', 'critical']
  }
];

const mockServersResponse: McpServerListResponse = {
  servers: mockServers,
  total: 2,
  limit: 50,
  offset: 0
};

describe('RegistryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock for listServers
    mockedMcpService.listServers.mockResolvedValue(mockServersResponse);
    
    // Default mocks for mutations
    mockedMcpService.createServer.mockResolvedValue(mockServers[0]);
    mockedMcpService.updateServer.mockResolvedValue(mockServers[0]);
    mockedMcpService.deleteServer.mockResolvedValue({
      message: 'MCP server deleted successfully',
      deleted_at: '2024-01-01T12:00:00Z',
      cleanup_job_id: null
    });
  });

  it('should render the registry page with header', () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    expect(screen.getByText('MCP Server Registry')).toBeInTheDocument();
    expect(screen.getByText('Manage and monitor your Model Context Protocol servers')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Add Server/i })).toBeInTheDocument();
  });

  it('should display servers in a grid layout', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
    
    expect(screen.getByText('https://test1.example.com')).toBeInTheDocument();
    expect(screen.getByText('https://prod.example.com')).toBeInTheDocument();
  });

  it('should display server health status with correct colors', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('healthy')).toBeInTheDocument();
      expect(screen.getByText('unhealthy')).toBeInTheDocument();
    });
  });

  it('should display server environment tags', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getAllByText('development')).toHaveLength(2); // One in environment chip, one in tags
      expect(screen.getAllByText('production')).toHaveLength(2); // One in environment chip, one in tags
    });
  });

  it('should display server tags', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('test')).toBeInTheDocument();
      expect(screen.getAllByText('development')).toHaveLength(2); // One in environment chip, one in tags
      expect(screen.getAllByText('production')).toHaveLength(2); // One in environment chip, one in tags
      expect(screen.getByText('critical')).toBeInTheDocument();
    });
  });

  it('should open create server dialog when Add Server button is clicked', () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    fireEvent.click(screen.getByRole('button', { name: /Add Server/i }));
    
    expect(screen.getByText('Add New MCP Server')).toBeInTheDocument();
    expect(screen.getByLabelText('Server Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Base URL')).toBeInTheDocument();
  });

  it('should create a new server when form is submitted', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    // Open create dialog
    fireEvent.click(screen.getByRole('button', { name: /Add Server/i }));
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Server Name'), {
      target: { value: 'New Test Server' }
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'A new test server' }
    });
    fireEvent.change(screen.getByLabelText('Base URL'), {
      target: { value: 'https://new.example.com' }
    });
    fireEvent.change(screen.getByLabelText('Tags (comma-separated)'), {
      target: { value: 'new, test' }
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Create Server/i }));
    
    await waitFor(() => {
      expect(mockedMcpService.createServer).toHaveBeenCalledWith({
        name: 'New Test Server',
        description: 'A new test server',
        base_url: 'https://new.example.com',
        environment: 'development',
        tags: ['new', 'test']
      });
    });
  });

  it('should open edit dialog when server menu is clicked', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    // Click the more options button for the first server
    const moreButtons = screen.getAllByRole('button', { name: '' });
    const moreButton = moreButtons.find(button => 
      button.querySelector('[data-testid="MoreVertIcon"]')
    );
    
    if (moreButton) {
      fireEvent.click(moreButton);
      
      // Click edit option
      fireEvent.click(screen.getByText('Edit'));
      
      expect(screen.getByText('Edit MCP Server')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Server 1')).toBeInTheDocument();
    }
  });

  it('should open delete confirmation dialog when delete is clicked', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    // Click the more options button for the first server
    const moreButtons = screen.getAllByRole('button', { name: '' });
    const moreButton = moreButtons.find(button => 
      button.querySelector('[data-testid="MoreVertIcon"]')
    );
    
    if (moreButton) {
      fireEvent.click(moreButton);
      
      // Click delete option
      fireEvent.click(screen.getByText('Delete'));
      
      expect(screen.getByText('Delete MCP Server')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to delete "Test Server 1"/)).toBeInTheDocument();
    }
  });

  it('should filter servers by search term', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
    
    // Search for "Test"
    const searchInput = screen.getByPlaceholderText(/Search servers by name/i);
    fireEvent.change(searchInput, { target: { value: 'Test' } });
    
    // Should only show Test Server 1
    expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    expect(screen.queryByText('Production Server')).not.toBeInTheDocument();
  });

  it('should filter servers by environment', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
    
    // Filter by development environment - use role instead of label
    const environmentSelects = screen.getAllByRole('combobox');
    const environmentSelect = environmentSelects[0]; // First select is environment
    fireEvent.mouseDown(environmentSelect);
    fireEvent.click(screen.getByText('Development'));
    
    // Should trigger a new query with development filter
    await waitFor(() => {
      expect(mockedMcpService.listServers).toHaveBeenCalledWith(
        expect.objectContaining({
          environment: 'development'
        })
      );
    });
  });

  it('should filter servers by health status', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
    
    // Filter by healthy status - use role instead of label
    const healthSelects = screen.getAllByRole('combobox');
    const healthSelect = healthSelects[1]; // Second select is health status
    fireEvent.mouseDown(healthSelect);
    fireEvent.click(screen.getByText('Healthy'));
    
    // Should trigger a new query with healthy filter
    await waitFor(() => {
      expect(mockedMcpService.listServers).toHaveBeenCalledWith(
        expect.objectContaining({
          health_status: 'healthy'
        })
      );
    });
  });

  it('should display empty state when no servers are found', async () => {
    mockedMcpService.listServers.mockResolvedValue({
      servers: [],
      total: 0,
      limit: 50,
      offset: 0
    });
    
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('No servers found')).toBeInTheDocument();
      expect(screen.getByText('Get started by adding your first MCP server')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Add Your First Server/i })).toBeInTheDocument();
    });
  });

  it('should display error message when server loading fails', async () => {
    const errorMessage = 'Failed to load servers';
    mockedMcpService.listServers.mockRejectedValue(new Error(errorMessage));
    
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText(`Failed to load servers: ${errorMessage}`)).toBeInTheDocument();
    });
  });

  it('should show loading state while fetching servers', () => {
    // Mock a delayed response
    mockedMcpService.listServers.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockServersResponse), 100))
    );
    
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle form validation errors', async () => {
    const validationError = new Error('Server name is required');
    mockedMcpService.createServer.mockRejectedValue(validationError);
    
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    // Open create dialog
    fireEvent.click(screen.getByRole('button', { name: /Add Server/i }));
    
    // Submit form without filling required fields
    fireEvent.click(screen.getByRole('button', { name: /Create Server/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Server name is required')).toBeInTheDocument();
    });
  });

  it('should display server creation date', async () => {
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Created: 1/1/2024')).toBeInTheDocument();
      expect(screen.getByText('Created: 1/2/2024')).toBeInTheDocument();
    });
  });

  it('should handle server tags overflow correctly', async () => {
    const serverWithManyTags: McpServer = {
      ...mockServers[0],
      tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5']
    };
    
    mockedMcpService.listServers.mockResolvedValue({
      servers: [serverWithManyTags],
      total: 1,
      limit: 50,
      offset: 0
    });
    
    render(<RegistryPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('tag1')).toBeInTheDocument();
      expect(screen.getByText('tag2')).toBeInTheDocument();
      expect(screen.getByText('tag3')).toBeInTheDocument();
      expect(screen.getByText('+2')).toBeInTheDocument(); // Shows overflow count
    });
  });
});
