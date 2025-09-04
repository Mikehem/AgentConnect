/**
 * Callback Page Component Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { CallbackPage } from '../../../pages/auth/CallbackPage'
import { useAuth } from '../../../hooks/useAuth'
import { authService } from '../../../services/authService'

// Mock the auth service
vi.mock('../../../services/authService', () => ({
  authService: {
    handleCallback: vi.fn(),
  },
}))

// Mock the auth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [
      new URLSearchParams('code=test-code&state=test-state'),
    ],
  }
})

const mockUseAuth = vi.mocked(useAuth)
const mockAuthService = vi.mocked(authService)

describe('CallbackPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })
  })

  it('should render processing state initially', () => {
    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Completing Sign In')).toBeInTheDocument()
    expect(screen.getByText('Please wait while we complete your authentication...')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('should handle successful callback', async () => {
    const mockUser = {
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

    const mockTokens = {
      access_token: 'access-token',
      id_token: 'id-token',
      expires_in: 3600,
      token_type: 'Bearer',
      scope: 'openid profile email',
    }

    mockAuthService.handleCallback.mockResolvedValue({
      user: mockUser,
      tokens: mockTokens,
    })

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Sign In Successful')).toBeInTheDocument()
      expect(screen.getByText('Redirecting to your dashboard...')).toBeInTheDocument()
    })

    expect(mockAuthService.handleCallback).toHaveBeenCalledWith('test-code', 'test-state')
  })

  it('should handle callback with OIDC error', async () => {
    // Mock URLSearchParams to return error
    vi.doMock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom')
      return {
        ...actual,
        useSearchParams: () => [
          new URLSearchParams('error=access_denied&error_description=User%20denied%20access'),
        ],
      }
    })

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Sign In Failed')).toBeInTheDocument()
      expect(screen.getByText('There was an error completing your authentication.')).toBeInTheDocument()
    })
  })

  it('should handle missing code parameter', async () => {
    // Mock URLSearchParams to return no code
    vi.doMock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom')
      return {
        ...actual,
        useSearchParams: () => [
          new URLSearchParams('state=test-state'),
        ],
      }
    })

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Sign In Failed')).toBeInTheDocument()
      expect(screen.getByText('Missing required authentication parameters')).toBeInTheDocument()
    })
  })

  it('should handle missing state parameter', async () => {
    // Mock URLSearchParams to return no state
    vi.doMock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom')
      return {
        ...actual,
        useSearchParams: () => [
          new URLSearchParams('code=test-code'),
        ],
      }
    })

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Sign In Failed')).toBeInTheDocument()
      expect(screen.getByText('Missing required authentication parameters')).toBeInTheDocument()
    })
  })

  it('should handle callback service errors', async () => {
    const errorMessage = 'Invalid state parameter'
    mockAuthService.handleCallback.mockRejectedValue(new Error(errorMessage))

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Sign In Failed')).toBeInTheDocument()
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should redirect to dashboard when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        email_verified: true,
        org_id: 'org-123',
        org_name: 'Test Org',
        roles: ['engineer'],
        permissions: ['mcp:servers:read'],
        created_at: '2024-01-01T00:00:00Z',
      },
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    // Should redirect to dashboard (Navigate component behavior)
    expect(screen.queryByText('Completing Sign In')).not.toBeInTheDocument()
  })

  it('should display error from auth context', () => {
    const errorMessage = 'Authentication context error'
    
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: errorMessage,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('should show appropriate icons for different states', async () => {
    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    // Initially should show loading spinner
    expect(screen.getByRole('progressbar')).toBeInTheDocument()

    // After error, should show error icon
    mockAuthService.handleCallback.mockRejectedValue(new Error('Test error'))

    await waitFor(() => {
      expect(screen.getByTestId('ErrorIcon')).toBeInTheDocument()
    })
  })

  it('should display footer message', () => {
    render(
      <BrowserRouter>
        <CallbackPage />
      </BrowserRouter>
    )

    expect(screen.getByText('If you continue to experience issues, please contact your administrator')).toBeInTheDocument()
  })
})
