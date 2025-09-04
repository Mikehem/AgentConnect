import { test, expect } from '@playwright/test';

test.describe('MCP Server Discovery', () => {
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
            },
            {
              id: 'server-2',
              name: 'Test Server 2',
              description: 'Another test MCP server with GitHub integration',
              base_url: 'https://test2.example.com',
              health_status: 'healthy',
              environment: 'production',
              created_at: '2024-01-02T00:00:00Z',
              updated_at: '2024-01-02T00:00:00Z'
            }
          ],
          total: 2,
          page: 1,
          limit: 10
        })
      });
    });

    // Mock capability discovery API
    await page.route('**/api/v1/mcp/servers/*/discover', async (route) => {
      const url = new URL(route.request().url());
      const serverId = url.pathname.split('/')[4];
      
      if (serverId === 'server-1') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            server_id: serverId,
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
      } else if (serverId === 'server-2') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            server_id: serverId,
            discovered_at: new Date().toISOString(),
            capabilities: {
              tools: {
                'get_repository': {
                  name: 'get_repository',
                  description: 'Get repository information',
                  input_schema: {
                    type: 'object',
                    properties: {
                      owner: { type: 'string', description: 'Repository owner' },
                      repo: { type: 'string', description: 'Repository name' }
                    },
                    required: ['owner', 'repo']
                  }
                },
                'list_issues': {
                  name: 'list_issues',
                  description: 'List repository issues',
                  input_schema: {
                    type: 'object',
                    properties: {
                      owner: { type: 'string', description: 'Repository owner' },
                      repo: { type: 'string', description: 'Repository name' }
                    },
                    required: ['owner', 'repo']
                  }
                }
              },
              resources: {
                'github': {
                  name: 'github',
                  description: 'GitHub repository access',
                  uri_template: 'github://{owner}/{repo}'
                }
              }
            },
            resources: [],
            tools: [],
            errors: [],
            warnings: []
          })
        });
      }
    });

    await page.goto('/discovery');
  });

  test('should display discovery page', async ({ page }) => {
    // Check if the discovery page elements are present
    await expect(page.getByRole('heading', { name: 'MCP Server Discovery' })).toBeVisible();
    await expect(page.getByText('Select a server to discover its capabilities')).toBeVisible();
  });

  test('should display list of available servers', async ({ page }) => {
    // Wait for servers to load
    await expect(page.getByText('Test Server 1')).toBeVisible();
    await expect(page.getByText('Test Server 2')).toBeVisible();
    
    // Check server details
    await expect(page.getByText('A test MCP server with filesystem capabilities')).toBeVisible();
    await expect(page.getByText('Another test MCP server with GitHub integration')).toBeVisible();
  });

  test('should select server and discover capabilities', async ({ page }) => {
    // Click on the first server
    await page.getByText('Test Server 1').click();
    
    // Wait for discovery to complete
    await expect(page.getByText('Capabilities Discovered')).toBeVisible();
    
    // Check that tools are displayed
    await expect(page.getByText('Tools (2)')).toBeVisible();
    await expect(page.getByText('read_file')).toBeVisible();
    await expect(page.getByText('write_file')).toBeVisible();
    
    // Check that resources are displayed
    await expect(page.getByText('Resources (1)')).toBeVisible();
    await expect(page.getByText('filesystem')).toBeVisible();
  });

  test('should display tool details', async ({ page }) => {
    // Select server and discover capabilities
    await page.getByText('Test Server 1').click();
    await expect(page.getByText('Capabilities Discovered')).toBeVisible();
    
    // Click on a tool to see details
    await page.getByText('read_file').click();
    
    // Check tool details
    await expect(page.getByText('Read contents of a file')).toBeVisible();
    await expect(page.getByText('File path to read')).toBeVisible();
  });

  test('should display resource details', async ({ page }) => {
    // Select server and discover capabilities
    await page.getByText('Test Server 1').click();
    await expect(page.getByText('Capabilities Discovered')).toBeVisible();
    
    // Click on a resource to see details
    await page.getByText('filesystem').click();
    
    // Check resource details
    await expect(page.getByText('File system access')).toBeVisible();
    await expect(page.getByText('file://{path}')).toBeVisible();
  });

  test('should switch between servers', async ({ page }) => {
    // Select first server
    await page.getByText('Test Server 1').click();
    await expect(page.getByText('Capabilities Discovered')).toBeVisible();
    await expect(page.getByText('read_file')).toBeVisible();
    
    // Select second server
    await page.getByText('Test Server 2').click();
    await expect(page.getByText('Capabilities Discovered')).toBeVisible();
    await expect(page.getByText('get_repository')).toBeVisible();
    await expect(page.getByText('list_issues')).toBeVisible();
  });

  test('should handle discovery errors', async ({ page }) => {
    // Mock discovery error
    await page.route('**/api/v1/mcp/servers/server-1/discover', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'discovery_failed',
          message: 'Failed to connect to server'
        })
      });
    });

    // Click on server
    await page.getByText('Test Server 1').click();
    
    // Check error message
    await expect(page.getByText('Discovery failed')).toBeVisible();
    await expect(page.getByText('Failed to connect to server')).toBeVisible();
  });

  test('should filter servers by environment', async ({ page }) => {
    // Filter by development environment
    await page.getByRole('button', { name: 'Environment' }).click();
    await page.getByRole('option', { name: 'Development' }).click();
    
    // Wait for filtered results
    await expect(page.getByText('Test Server 1')).toBeVisible();
    await expect(page.getByText('Test Server 2')).not.toBeVisible();
  });

  test('should filter servers by health status', async ({ page }) => {
    // Filter by healthy servers
    await page.getByRole('button', { name: 'Health Status' }).click();
    await page.getByRole('option', { name: 'Healthy' }).click();
    
    // Wait for filtered results
    await expect(page.getByText('Test Server 1')).toBeVisible();
    await expect(page.getByText('Test Server 2')).toBeVisible();
  });
});
