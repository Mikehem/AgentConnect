/**
 * Authentication Hook Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../../hooks/useAuth'
import { authService } from '../../services/authService'
import { User, AuthTokens } from '../../types/auth'

// Mock the auth service
vi.mock('../../services/authService', () => ({
  authService: {
    isAuthenticated: vi.fn(),
    getCurrentUser: vi.fn(),
    getStoredTokens: vi.fn(),
    clearStoredAuth: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    handleCallback: vi.fn(),
  },
}))

const mockAuthService = vi.mocked(authService)

// Test component that uses the auth hook
function TestComponent() {
  const { isAuthenticated, isLoading, user, error, hasPermission, hasRole } = useAuth()
  
  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="is-loading">{isLoading.toString()}</div>
      <div data-testid="user-name">{user?.name || 'null'}</div>
      <div data-testid="error">{error || 'null'}</div>
      <div data-testid="has-permission">{hasPermission('mcp:servers:read').toString()}</div>
      <div data-testid="has-role">{hasRole('engineer').toString()}</div>
    </div>
  )
}

// Wrapper component for testing
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initialization', () => {
    it('should initialize with authenticated user', async () => {
      const mockUser: User = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        roles: ['engineer'],
        permissions: ['mcp:servers:read'],
        created_at: '2024-01-01T00:00:00Z',
      }

      const mockTokens: AuthTokens = {
        access_token: 'access-token',
        id_token: 'id-token',
        expires_in: 3600,
        token_type: 'Bearer',
        scope: 'openid profile email',
      }

      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getCurrentUser.mockReturnValue(mockUser)
      mockAuthService.getStoredTokens.mockReturnValue(mockTokens)

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
        expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
        expect(screen.getByTestId('user-name')).toHaveTextContent('Test User')
        expect(screen.getByTestId('error')).toHaveTextContent('null')
      })
    })

    it('should initialize with unauthenticated state', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false)
      mockAuthService.getCurrentUser.mockReturnValue(null)
      mockAuthService.getStoredTokens.mockReturnValue(null)

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
        expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
        expect(screen.getByTestId('user-name')).toHaveTextContent('null')
        expect(screen.getByTestId('error')).toHaveTextContent('null')
      })
    })

    it('should handle initialization errors', async () => {
      mockAuthService.isAuthenticated.mockImplementation(() => {
        throw new Error('Storage error')
      })

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
        expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
        expect(screen.getByTestId('error')).toHaveTextContent('Failed to initialize authentication')
      })
    })
  })

  describe('permission checking', () => {
    it('should check user permissions correctly', async () => {
      const mockUser: User = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        roles: ['engineer'],
        permissions: ['mcp:servers:read', 'mcp:servers:create'],
        created_at: '2024-01-01T00:00:00Z',
      }

      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getCurrentUser.mockReturnValue(mockUser)
      mockAuthService.getStoredTokens.mockReturnValue({} as AuthTokens)

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('has-permission')).toHaveTextContent('true')
        expect(screen.getByTestId('has-role')).toHaveTextContent('true')
      })
    })

    it('should return false for missing permissions', async () => {
      const mockUser: User = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        roles: ['viewer'],
        permissions: ['mcp:servers:read'],
        created_at: '2024-01-01T00:00:00Z',
      }

      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getCurrentUser.mockReturnValue(mockUser)
      mockAuthService.getStoredTokens.mockReturnValue({} as AuthTokens)

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('has-permission')).toHaveTextContent('true')
        expect(screen.getByTestId('has-role')).toHaveTextContent('false')
      })
    })
  })

  describe('login', () => {
    it('should handle successful login', async () => {
      const mockResponse = {
        auth_url: 'https://auth.example.com/authorize',
        state: 'test-state',
        nonce: 'test-nonce',
      }

      mockAuthService.isAuthenticated.mockReturnValue(false)
      mockAuthService.getCurrentUser.mockReturnValue(null)
      mockAuthService.getStoredTokens.mockReturnValue(null)
      mockAuthService.login.mockResolvedValue(mockResponse)

      // Mock window.location.href
      const mockLocationHref = vi.fn()
      Object.defineProperty(window, 'location', {
        value: { href: mockLocationHref },
        writable: true,
      })

      function LoginTestComponent() {
        const { login, isLoading } = useAuth()
        
        return (
          <div>
            <div data-testid="is-loading">{isLoading.toString()}</div>
            <button
              data-testid="login-button"
              onClick={() => login()}
            >
              Login
            </button>
          </div>
        )
      }

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
      })

      await act(async () => {
        screen.getByTestId('login-button').click()
      })

      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalledWith(undefined)
        expect(mockLocationHref).toHaveBeenCalledWith(mockResponse.auth_url)
      })
    })

    it('should handle login errors', async () => {
      const mockError = {
        error: 'login_failed',
        error_description: 'Login failed',
      }

      mockAuthService.isAuthenticated.mockReturnValue(false)
      mockAuthService.getCurrentUser.mockReturnValue(null)
      mockAuthService.getStoredTokens.mockReturnValue(null)
      mockAuthService.login.mockRejectedValue(mockError)

      function LoginTestComponent() {
        const { login, error } = useAuth()
        
        return (
          <div>
            <button
              data-testid="login-button"
              onClick={() => login()}
            >
              Login
            </button>
            <div data-testid="error">{error || 'null'}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      await act(async () => {
        screen.getByTestId('login-button').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Login failed')
      })
    })
  })

  describe('logout', () => {
    it('should handle successful logout', async () => {
      const mockResponse = {
        logout_url: 'https://auth.example.com/logout',
      }

      const mockUser: User = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        roles: ['engineer'],
        permissions: ['mcp:servers:read'],
        created_at: '2024-01-01T00:00:00Z',
      }

      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getCurrentUser.mockReturnValue(mockUser)
      mockAuthService.getStoredTokens.mockReturnValue({} as AuthTokens)
      mockAuthService.logout.mockResolvedValue(mockResponse)

      // Mock window.location.href
      const mockLocationHref = vi.fn()
      Object.defineProperty(window, 'location', {
        value: { href: mockLocationHref },
        writable: true,
      })

      function LogoutTestComponent() {
        const { logout } = useAuth()
        
        return (
          <button
            data-testid="logout-button"
            onClick={() => logout()}
          >
            Logout
          </button>
        )
      }

      render(
        <TestWrapper>
          <LogoutTestComponent />
        </TestWrapper>
      )

      await act(async () => {
        screen.getByTestId('logout-button').click()
      })

      await waitFor(() => {
        expect(mockAuthService.logout).toHaveBeenCalled()
        expect(mockLocationHref).toHaveBeenCalledWith(mockResponse.logout_url)
      })
    })
  })

  describe('token refresh', () => {
    it('should handle successful token refresh', async () => {
      const mockUser: User = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        roles: ['engineer'],
        permissions: ['mcp:servers:read'],
        created_at: '2024-01-01T00:00:00Z',
      }

      const mockTokens: AuthTokens = {
        access_token: 'new-access-token',
        id_token: 'new-id-token',
        expires_in: 3600,
        token_type: 'Bearer',
        scope: 'openid profile email',
      }

      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getCurrentUser.mockReturnValue(mockUser)
      mockAuthService.getStoredTokens.mockReturnValue(mockTokens)
      mockAuthService.refreshToken.mockResolvedValue({ tokens: mockTokens })

      function RefreshTestComponent() {
        const { refreshToken } = useAuth()
        
        return (
          <button
            data-testid="refresh-button"
            onClick={() => refreshToken()}
          >
            Refresh
          </button>
        )
      }

      render(
        <TestWrapper>
          <RefreshTestComponent />
        </TestWrapper>
      )

      await act(async () => {
        screen.getByTestId('refresh-button').click()
      })

      await waitFor(() => {
        expect(mockAuthService.refreshToken).toHaveBeenCalled()
      })
    })
  })

  describe('error handling', () => {
    it('should clear errors', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false)
      mockAuthService.getCurrentUser.mockReturnValue(null)
      mockAuthService.getStoredTokens.mockReturnValue(null)

      function ErrorTestComponent() {
        const { clearError, error } = useAuth()
        
        return (
          <div>
            <button
              data-testid="clear-error-button"
              onClick={() => clearError()}
            >
              Clear Error
            </button>
            <div data-testid="error">{error || 'null'}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <ErrorTestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('null')
      })
    })
  })
})
