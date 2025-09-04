import { test, expect } from '@playwright/test';
import { Buffer } from 'buffer';

test.describe('Chat Testing Console', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('sprintconnect_user', JSON.stringify({
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        picture: null
      }));
      localStorage.setItem('sprintconnect_tokens', JSON.stringify({
        access_token: 'access-token-123',
        id_token: 'id-token-123',
        refresh_token: 'refresh-token-123',
        expires_in: 3600,
        token_type: 'Bearer',
        scope: 'openid profile email'
      }));
    });

    // Mock MCP servers API
    await page.route('**/api/v1/mcp/servers**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          servers: [
            {
              id: 'server-1',
              name: 'Test Server 1',
              description: 'A test MCP server with filesystem capabilities',
              base_url: 'https://test1.example.com',
              health_status: 'healthy',
              environment: 'development',
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z'
            }
          ],
          total: 1,
          page: 1,
          limit: 10
        })
      });
    });

    // Mock capability discovery API
    await page.route('**/api/v1/mcp/servers/*/discover', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          server_id: 'server-1',
          discovered_at: new Date().toISOString(),
          capabilities: {
            tools: {
              'read_file': {
                name: 'read_file',
                description: 'Read contents of a file',
                input_schema: {
                  type: 'object',
                  properties: {
                    path: { type: 'string', description: 'File path to read' }
                  },
                  required: ['path']
                }
              },
              'write_file': {
                name: 'write_file',
                description: 'Write contents to a file',
                input_schema: {
                  type: 'object',
                  properties: {
                    path: { type: 'string', description: 'File path to write' },
                    content: { type: 'string', description: 'Content to write' }
                  },
                  required: ['path', 'content']
                }
              }
            },
            resources: {
              'filesystem': {
                name: 'filesystem',
                description: 'File system access',
                uri_template: 'file://{path}'
              }
            }
          },
          resources: [],
          tools: [],
          errors: [],
          warnings: []
        })
      });
    });

    await page.goto('/chat');
  });

  test('should display chat console page', async ({ page }) => {
    // Check if the chat console page elements are present
    await expect(page.getByRole('heading', { name: 'MCP Chat Testing Console' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Select Server' })).toBeVisible();
  });

  test('should show server selection prompt when no server is selected', async ({ page }) => {
    // Check for server selection prompt
    await expect(page.getByText('Select a Server to Start Testing')).toBeVisible();
    await expect(page.getByText('Choose an MCP server from the list above to begin interactive testing of its capabilities')).toBeVisible();
  });

  test('should display server list when select server button is clicked', async ({ page }) => {
    // Click select server button
    await page.getByRole('button', { name: 'Select Server' }).click();
    
    // Check that server list is displayed
    await expect(page.getByText('Select MCP Server')).toBeVisible();
    await expect(page.getByText('Test Server 1')).toBeVisible();
  });

  test('should select server and create chat session', async ({ page }) => {
    // Click select server button
    await page.getByRole('button', { name: 'Select Server' }).click();
    
    // Select a server
    await page.getByText('Test Server 1').click();
    
    // Check that chat session is created
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    await expect(page.getByText('You can now test MCP capabilities through natural language')).toBeVisible();
    
    // Check that server info is displayed in sidebar
    await expect(page.getByText('Server Information')).toBeVisible();
    await expect(page.getByText('Test Server 1')).toBeVisible();
    await expect(page.getByText('A test MCP server with filesystem capabilities')).toBeVisible();
  });

  test('should display available capabilities in sidebar', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for capabilities to load
    await expect(page.getByText('Available Capabilities')).toBeVisible();
    await expect(page.getByText('Tools (2)')).toBeVisible();
    await expect(page.getByText('read_file')).toBeVisible();
    await expect(page.getByText('write_file')).toBeVisible();
    await expect(page.getByText('Resources (1)')).toBeVisible();
    await expect(page.getByText('filesystem')).toBeVisible();
  });

  test('should send messages in chat', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Type a message
    await page.getByPlaceholder('Type your message to test MCP capabilities...').fill('Hello, can you help me read a file?');
    
    // Send the message
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Check that message appears in chat
    await expect(page.getByText('Hello, can you help me read a file?')).toBeVisible();
    
    // Check that typing indicator appears
    await expect(page.getByText('Processing...')).toBeVisible();
  });

  test('should handle Enter key to send messages', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Type a message and press Enter
    await page.getByPlaceholder('Type your message to test MCP capabilities...').fill('Test message');
    await page.getByPlaceholder('Type your message to test MCP capabilities...').press('Enter');
    
    // Check that message appears in chat
    await expect(page.getByText('Test message')).toBeVisible();
  });

  test('should upload files', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Create a test file
    const testFile = {
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test content')
    };
    
    // Upload the file
    await page.setInputFiles('input[type="file"]', testFile);
    
    // Check that file appears in attached files section
    await expect(page.getByText('Attached Files (1)')).toBeVisible();
    await expect(page.getByText('test.txt')).toBeVisible();
  });

  test('should remove uploaded files', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Create and upload a test file
    const testFile = {
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test content')
    };
    await page.setInputFiles('input[type="file"]', testFile);
    
    // Check that file appears
    await expect(page.getByText('test.txt')).toBeVisible();
    
    // Remove the file
    await page.getByRole('button', { name: 'Remove file' }).click();
    
    // Check that file is removed
    await expect(page.getByText('test.txt')).not.toBeVisible();
  });

  test('should send message with attached files', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Create and upload a test file
    const testFile = {
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('test content')
    };
    await page.setInputFiles('input[type="file"]', testFile);
    
    // Send message with file
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Check that message with file appears
    await expect(page.getByText('Uploaded 1 file(s)')).toBeVisible();
    await expect(page.getByText('test.txt')).toBeVisible();
  });

  test('should clear chat session', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Send a message
    await page.getByPlaceholder('Type your message to test MCP capabilities...').fill('Test message');
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Check that message appears
    await expect(page.getByText('Test message')).toBeVisible();
    
    // Clear the session
    await page.getByRole('button', { name: 'Clear' }).click();
    
    // Check that session is cleared
    await expect(page.getByText('Session cleared')).toBeVisible();
    await expect(page.getByText('Test message')).not.toBeVisible();
  });

  test('should change server', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Change server
    await page.getByRole('button', { name: 'Change Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Check that new session is created
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
  });

  test('should validate file upload types', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Try to upload an unsupported file type
    const unsupportedFile = {
      name: 'test.xyz',
      mimeType: 'application/xyz',
      buffer: Buffer.from('test content')
    };
    await page.setInputFiles('input[type="file"]', unsupportedFile);
    
    // Check that file is not uploaded (validation should prevent it)
    await expect(page.getByText('test.xyz')).not.toBeVisible();
  });

  test('should validate file upload size', async ({ page }) => {
    // Select a server
    await page.getByRole('button', { name: 'Select Server' }).click();
    await page.getByText('Test Server 1').click();
    
    // Wait for chat session to be ready
    await expect(page.getByText('Connected to Test Server 1')).toBeVisible();
    
    // Create a large file (over 10MB)
    const largeContent = 'x'.repeat(11 * 1024 * 1024); // 11MB
    const largeFile = {
      name: 'large.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from(largeContent)
    };
    
    // Try to upload the large file
    await page.setInputFiles('input[type="file"]', largeFile);
    
    // Check that file is not uploaded (size validation should prevent it)
    await expect(page.getByText('large.txt')).not.toBeVisible();
  });
});
