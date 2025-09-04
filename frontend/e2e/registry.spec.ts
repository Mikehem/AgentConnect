import { test, expect } from '@playwright/test';

test.describe('MCP Server Registry', () => {
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
      const url = new URL(route.request().url());
      const method = route.request().method();

      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            servers: [
              {
                id: 'server-1',
                name: 'Test Server 1',
                description: 'A test MCP server',
                base_url: 'https://test1.example.com',
                health_status: 'healthy',
                environment: 'development',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z'
              },
              {
                id: 'server-2',
                name: 'Test Server 2',
                description: 'Another test MCP server',
                base_url: 'https://test2.example.com',
                health_status: 'unhealthy',
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
      } else if (method === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'server-new',
            name: 'New Test Server',
            description: 'A newly created test server',
            base_url: 'https://newtest.example.com',
            health_status: 'unknown',
            environment: 'development',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          })
        });
      }
    });

    await page.goto('/registry');
  });

  test('should display server registry page', async ({ page }) => {
    // Check if the registry page elements are present
    await expect(page.getByRole('heading', { name: 'MCP Server Registry' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add New Server' })).toBeVisible();
    await expect(page.getByPlaceholder('Search servers...')).toBeVisible();
  });

  test('should display list of servers', async ({ page }) => {
    // Wait for servers to load
    await expect(page.getByText('Test Server 1')).toBeVisible();
    await expect(page.getByText('Test Server 2')).toBeVisible();
    
    // Check server details
    await expect(page.getByText('A test MCP server')).toBeVisible();
    await expect(page.getByText('Another test MCP server')).toBeVisible();
    
    // Check health status indicators
    await expect(page.getByText('healthy')).toBeVisible();
    await expect(page.getByText('unhealthy')).toBeVisible();
  });

  test('should filter servers by search', async ({ page }) => {
    // Search for a specific server
    await page.getByPlaceholder('Search servers...').fill('Test Server 1');
    
    // Wait for filtered results
    await expect(page.getByText('Test Server 1')).toBeVisible();
    await expect(page.getByText('Test Server 2')).not.toBeVisible();
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
    await expect(page.getByText('Test Server 2')).not.toBeVisible();
  });

  test('should open add server dialog', async ({ page }) => {
    // Click add server button
    await page.getByRole('button', { name: 'Add New Server' }).click();
    
    // Verify dialog is open
    await expect(page.getByRole('dialog', { name: 'Add New MCP Server' })).toBeVisible();
    await expect(page.getByLabel('Server Name')).toBeVisible();
    await expect(page.getByLabel('Base URL')).toBeVisible();
    await expect(page.getByLabel('Description')).toBeVisible();
  });

  test('should create new server', async ({ page }) => {
    // Open add server dialog
    await page.getByRole('button', { name: 'Add New Server' }).click();
    
    // Fill in server details
    await page.getByLabel('Server Name').fill('New Test Server');
    await page.getByLabel('Base URL').fill('https://newtest.example.com');
    await page.getByLabel('Description').fill('A newly created test server');
    await page.getByLabel('Environment').selectOption('development');
    
    // Submit the form
    await page.getByRole('button', { name: 'Create Server' }).click();
    
    // Verify success message
    await expect(page.getByText('Server created successfully')).toBeVisible();
  });

  test('should handle server creation validation', async ({ page }) => {
    // Open add server dialog
    await page.getByRole('button', { name: 'Add New Server' }).click();
    
    // Try to submit without required fields
    await page.getByRole('button', { name: 'Create Server' }).click();
    
    // Verify validation errors
    await expect(page.getByText('Server name is required')).toBeVisible();
    await expect(page.getByText('Base URL is required')).toBeVisible();
  });

  test('should handle server creation with invalid URL', async ({ page }) => {
    // Open add server dialog
    await page.getByRole('button', { name: 'Add New Server' }).click();
    
    // Fill in server details with invalid URL
    await page.getByLabel('Server Name').fill('Test Server');
    await page.getByLabel('Base URL').fill('invalid-url');
    await page.getByLabel('Description').fill('Test description');
    
    // Submit the form
    await page.getByRole('button', { name: 'Create Server' }).click();
    
    // Verify validation error
    await expect(page.getByText('Please enter a valid URL')).toBeVisible();
  });
});
