import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { vi } from 'vitest';
import { lightTheme } from '../../../styles/theme';
import ChatPage from '../../../pages/chat/ChatPage';
import { mcpService } from '../../../services/mcpService';
import { McpServer, McpCapabilityDiscovery } from '../../../types/mcp';

// Mock the mcpService
vi.mock('../../../services/mcpService');
const mockedMcpService = mcpService as any;

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

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
      },
      'another-tool': {
        name: 'another-tool',
        description: 'Another test tool',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string' }
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

describe('ChatPage', () => {
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

  it('should render the chat page', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    expect(screen.getByText('MCP Chat Testing Console')).toBeInTheDocument();
    expect(screen.getByText('Select Server')).toBeInTheDocument();
  });

  it('should show server selection prompt when no server is selected', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select a Server to Start Testing')).toBeInTheDocument();
      expect(screen.getByText('Choose an MCP server from the list above to begin interactive testing of its capabilities')).toBeInTheDocument();
    });
  });

  it('should display server list when select server button is clicked', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Select MCP Server')).toBeInTheDocument();
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
    });
  });

  it('should allow server selection and create chat session', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument(); // In header
      expect(screen.getByText('healthy')).toBeInTheDocument();
      expect(screen.getByText('Connected to Test Server 1. You can now test MCP capabilities through natural language.')).toBeInTheDocument();
    });
  });

  it('should display server information in sidebar', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Server Information')).toBeInTheDocument();
      expect(screen.getByText('A test MCP server')).toBeInTheDocument();
      expect(screen.getByText('Health: healthy')).toBeInTheDocument();
      expect(screen.getByText('Environment: development')).toBeInTheDocument();
    });
  });

  it('should display available capabilities in sidebar', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    await waitFor(() => {
      expect(screen.getByText('Available Capabilities')).toBeInTheDocument();
      expect(screen.getByText('Tools (2)')).toBeInTheDocument();
      expect(screen.getByText('test-tool')).toBeInTheDocument();
      expect(screen.getByText('another-tool')).toBeInTheDocument();
      expect(screen.getByText('Resources (1)')).toBeInTheDocument();
      expect(screen.getByText('test-resource')).toBeInTheDocument();
    });
  });

  it('should allow sending messages', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Wait for chat interface to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Type your message to test MCP capabilities...')).toBeInTheDocument();
    });
    
    // Type a message
    const messageInput = screen.getByPlaceholderText('Type your message to test MCP capabilities...');
    fireEvent.change(messageInput, { target: { value: 'Hello, test this tool' } });
    
    // Send the message
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    // Check that the message appears
    await waitFor(() => {
      expect(screen.getByText('Hello, test this tool')).toBeInTheDocument();
    });
  });

  it('should handle Enter key to send messages', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Wait for chat interface to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Type your message to test MCP capabilities...')).toBeInTheDocument();
    });
    
    // Type a message and press Enter
    const messageInput = screen.getByPlaceholderText('Type your message to test MCP capabilities...');
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.keyPress(messageInput, { key: 'Enter', code: 'Enter' });
    
    // Check that the message appears
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
  });

  it('should show typing indicator when processing message', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Wait for chat interface to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Type your message to test MCP capabilities...')).toBeInTheDocument();
    });
    
    // Type and send a message
    const messageInput = screen.getByPlaceholderText('Type your message to test MCP capabilities...');
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    // Check for typing indicator
    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });

  it('should clear session when clear button is clicked', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Wait for chat interface to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Type your message to test MCP capabilities...')).toBeInTheDocument();
    });
    
    // Send a message first
    const messageInput = screen.getByPlaceholderText('Type your message to test MCP capabilities...');
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
    
    // Clear the session
    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);
    
    // Check that session is cleared
    await waitFor(() => {
      expect(screen.getByText('Session cleared. You can continue testing Test Server 1 capabilities.')).toBeInTheDocument();
    });
  });

  it('should disable send button when message input is empty', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Wait for chat interface to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Type your message to test MCP capabilities...')).toBeInTheDocument();
    });
    
    // Check that send button is disabled when input is empty
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
    
    // Type a message
    const messageInput = screen.getByPlaceholderText('Type your message to test MCP capabilities...');
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    
    // Check that send button is now enabled
    expect(sendButton).not.toBeDisabled();
  });

  it('should show change server button when server is selected', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Check that button text changes
    await waitFor(() => {
      expect(screen.getByText('Change Server')).toBeInTheDocument();
      expect(screen.getByText('Sessions')).toBeInTheDocument();
      expect(screen.getByText('Clear')).toBeInTheDocument();
    });
  });

  it('should handle server loading error', async () => {
    mockedMcpService.listServers.mockRejectedValue(new Error('Failed to fetch servers'));
    
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load servers: Failed to fetch servers')).toBeInTheDocument();
    });
  });

  it('should show loading state while fetching servers', async () => {
    mockedMcpService.listServers.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ servers: mockServers, total: 2, limit: 100, offset: 0 }), 100))
    );
    
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should display server health status in header', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    // Select server first
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Test Server 1'));
    
    // Check that server info appears in header
    await waitFor(() => {
      expect(screen.getAllByText('Test Server 1')).toHaveLength(2); // One in header, one in sidebar
      expect(screen.getAllByText('healthy')).toHaveLength(2); // One in header, one in sidebar
    });
  });

  it('should display multiple server options in selection list', async () => {
    render(<ChatPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Select Server')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Select Server'));
    
    await waitFor(() => {
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Production Server')).toBeInTheDocument();
      expect(screen.getByText('https://test1.example.com')).toBeInTheDocument();
      expect(screen.getByText('https://prod.example.com')).toBeInTheDocument();
    });
  });
});
