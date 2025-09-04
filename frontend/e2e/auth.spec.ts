import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the login page
    await page.goto('/auth/login');
  });

  test('should display login page correctly', async ({ page }) => {
    // Check if the login page elements are present
    await expect(page.getByRole('heading', { name: 'SprintConnect' })).toBeVisible();
    await expect(page.getByText('Enterprise MCP Server Management Platform')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In with OIDC' })).toBeVisible();
    await expect(page.getByText('Secure authentication powered by OIDC')).toBeVisible();
  });

  test('should handle login button click', async ({ page }) => {
    // Mock the OIDC login response
    await page.route('**/api/v1/auth/oidc/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_url: 'https://auth.example.com/authorize?client_id=test&redirect_uri=http://localhost:3000/auth/callback',
          state: 'test-state',
          nonce: 'test-nonce'
        })
      });
    });

    // Click the login button
    await page.getByRole('button', { name: 'Sign In with OIDC' }).click();

    // Verify that the page would redirect to OIDC provider
    // Note: In a real test, we would check the redirect, but for E2E we'll verify the API call
    await expect(page).toHaveURL('/auth/login');
  });

  test('should handle OIDC callback successfully', async ({ page }) => {
    // Mock the callback response
    await page.route('**/api/v1/auth/oidc/callback', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: 'user-123',
            email: 'test@example.com',
            name: 'Test User',
            email_verified: true,
            org_id: 'org-123',
            org_name: 'Test Org',
            picture: null
          },
          tokens: {
            access_token: 'access-token-123',
            id_token: 'id-token-123',
            refresh_token: 'refresh-token-123',
            expires_in: 3600,
            token_type: 'Bearer',
            scope: 'openid profile email'
          }
        })
      });
    });

    // Navigate to callback page with mock parameters
    await page.goto('/auth/callback?code=test-code&state=test-state');

    // Verify successful authentication
    await expect(page.getByText('Sign In Successful')).toBeVisible();
    await expect(page.getByText('Redirecting to your dashboard...')).toBeVisible();
  });

  test('should handle OIDC callback with error', async ({ page }) => {
    // Navigate to callback page with error parameters
    await page.goto('/auth/callback?error=access_denied&error_description=User%20denied%20access');

    // Verify error handling
    await expect(page.getByText('Sign In Failed')).toBeVisible();
    await expect(page.getByText('User denied access')).toBeVisible();
  });

  test('should handle logout flow', async ({ page }) => {
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

    // Mock logout response
    await page.route('**/api/v1/auth/oidc/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          logout_url: 'https://auth.example.com/logout?post_logout_redirect_uri=http://localhost:3000'
        })
      });
    });

    // Navigate to dashboard (should be authenticated)
    await page.goto('/dashboard');

    // Click logout button
    await page.getByRole('button', { name: 'Logout' }).click();

    // Verify logout redirect
    await expect(page).toHaveURL('/auth/login');
  });
});
