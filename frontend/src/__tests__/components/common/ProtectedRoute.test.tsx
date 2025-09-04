/**
 * Protected Route Component Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { ProtectedRoute } from '../../../components/common/ProtectedRoute'
import { useAuth } from '../../../hooks/useAuth'

// Mock the auth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

const mockUseAuth = vi.mocked(useAuth)

// Test component
function TestComponent() {
  return <div data-testid="protected-content">Protected Content</div>
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should show loading spinner while checking authentication', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
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

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Authenticating...')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should redirect to login when not authenticated', () => {
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

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </MemoryRouter>
    )

    // Should redirect to login (Navigate component behavior)
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should render children when authenticated', () => {
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

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
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
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should show access denied for missing permissions', () => {
    const mockUser = {
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

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn((permission) => permission === 'mcp:servers:read'),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPermissions={['mcp:servers:delete']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('You don\'t have the required permissions to access this page.')).toBeInTheDocument()
    expect(screen.getByText('Required permissions: mcp:servers:delete')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should show access denied for missing roles', () => {
    const mockUser = {
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

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn(),
      hasRole: vi.fn((role) => role === 'viewer'),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRoles={['admin']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('You don\'t have the required role to access this page.')).toBeInTheDocument()
    expect(screen.getByText('Required roles: admin')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should allow access when user has required permissions', () => {
    const mockUser = {
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

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn((permission) => 
        ['mcp:servers:read', 'mcp:servers:create'].includes(permission)
      ),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPermissions={['mcp:servers:read', 'mcp:servers:create']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should allow access when user has required roles', () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      email_verified: true,
      org_id: 'org-123',
      org_name: 'Test Org',
      roles: ['engineer', 'admin'],
      permissions: ['mcp:servers:read'],
      created_at: '2024-01-01T00:00:00Z',
    }

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn(),
      hasRole: vi.fn((role) => ['engineer', 'admin'].includes(role)),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRoles={['admin']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should use custom fallback path', () => {
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

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute fallbackPath="/custom-login">
          <TestComponent />
        </ProtectedRoute>
      </MemoryRouter>
    )

    // Should redirect to custom login path (Navigate component behavior)
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should handle multiple required permissions', () => {
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

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn((permission) => permission === 'mcp:servers:read'),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPermissions={['mcp:servers:read', 'mcp:servers:create']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('Required permissions: mcp:servers:read, mcp:servers:create')).toBeInTheDocument()
  })

  it('should handle multiple required roles', () => {
    const mockUser = {
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

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: mockUser,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: vi.fn(),
      hasPermission: vi.fn(),
      hasRole: vi.fn((role) => role === 'viewer'),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRoles={['engineer', 'admin']}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('Required roles: engineer, admin')).toBeInTheDocument()
  })
})
