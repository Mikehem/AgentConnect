/**
 * Login Page Component Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from '../../../pages/auth/LoginPage'
import { useAuth } from '../../../hooks/useAuth'

// Mock the auth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

const mockUseAuth = vi.mocked(useAuth)

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('LoginPage', () => {
  const mockLogin = vi.fn()
  const mockClearError = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null,
      login: mockLogin,
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: mockClearError,
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })
  })

  it('should render login page correctly', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText('SprintConnect')).toBeInTheDocument()
    expect(screen.getByText('Enterprise MCP Server Management Platform')).toBeInTheDocument()
    expect(screen.getByText('Sign In with OIDC')).toBeInTheDocument()
    expect(screen.getByText('Secure authentication powered by OIDC')).toBeInTheDocument()
  })

  it('should redirect to dashboard if already authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: null,
      error: null,
      login: mockLogin,
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: mockClearError,
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    // Should redirect to dashboard (Navigate component behavior)
    expect(screen.queryByText('Sign In with OIDC')).not.toBeInTheDocument()
  })

  it('should handle login button click', async () => {
    mockLogin.mockResolvedValue(undefined)

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const loginButton = screen.getByText('Sign In with OIDC')
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(undefined)
    })
  })

  it('should show loading state during login', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      error: null,
      login: mockLogin,
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: mockClearError,
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Signing In...')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('should display error message', () => {
    const errorMessage = 'Authentication failed'
    
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: errorMessage,
      login: mockLogin,
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: mockClearError,
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('should clear error when close button is clicked', () => {
    const errorMessage = 'Authentication failed'
    
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: errorMessage,
      login: mockLogin,
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: mockClearError,
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)

    expect(mockClearError).toHaveBeenCalled()
  })

  it('should clear error on component unmount', () => {
    const errorMessage = 'Authentication failed'
    
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: errorMessage,
      login: mockLogin,
      logout: vi.fn(),
      refreshToken: vi.fn(),
      clearError: mockClearError,
      hasPermission: vi.fn(),
      hasRole: vi.fn(),
      hasAnyPermission: vi.fn(),
      hasAnyRole: vi.fn(),
    })

    const { unmount } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    unmount()

    expect(mockClearError).toHaveBeenCalled()
  })

  it('should handle login errors gracefully', async () => {
    const loginError = new Error('Login failed')
    mockLogin.mockRejectedValue(loginError)

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const loginButton = screen.getByText('Sign In with OIDC')
    fireEvent.click(loginButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })

  it('should have proper accessibility attributes', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const loginButton = screen.getByRole('button', { name: /sign in with oidc/i })
    expect(loginButton).toBeInTheDocument()
    expect(loginButton).not.toBeDisabled()

    const alert = screen.queryByRole('alert')
    expect(alert).not.toBeInTheDocument() // No error initially
  })

  it('should display footer information', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText('© 2024 SprintConnect. All rights reserved.')).toBeInTheDocument()
  })

  it('should show security information', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText('You will be redirected to your organization\'s identity provider')).toBeInTheDocument()
  })
})
