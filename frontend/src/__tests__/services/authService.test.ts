/**
 * Authentication Service Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import axios from 'axios'
import { AuthService } from '../../services/authService'
import { AuthTokens, User } from '../../types/auth'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    }))
  }
}))
const mockedAxios = vi.mocked(axios)

describe('AuthService', () => {
  let authService: AuthService
  let mockAxiosInstance: any

  beforeEach(() => {
    // Clear all mocks
    vi.clearAllMocks()
    
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    }
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
    })

    // Mock sessionStorage
    const sessionStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    }
    Object.defineProperty(window, 'sessionStorage', {
      value: sessionStorageMock,
    })

    // Mock axios instance
    mockAxiosInstance = {
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { 
          use: vi.fn((_onFulfilled, _onRejected) => {
            // Mock interceptor registration
            return 0 // Mock interceptor ID
          })
        },
        response: { 
          use: vi.fn((_onFulfilled, _onRejected) => {
            // Mock interceptor registration
            return 0 // Mock interceptor ID
          })
        },
      },
    }
    mockedAxios.create = vi.fn().mockReturnValue(mockAxiosInstance)

    authService = new AuthService()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('login', () => {
    it('should initiate OIDC login flow successfully', async () => {
      const mockResponse = {
        data: {
          auth_url: 'https://auth.example.com/authorize?client_id=test&redirect_uri=test',
          state: 'test-state',
          nonce: 'test-nonce',
        },
      }

      mockAxiosInstance.post.mockResolvedValue(mockResponse)
      const sessionStorageSetItem = vi.spyOn(sessionStorage, 'setItem')

      const result = await authService.login('https://example.com/callback')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/auth/oidc/login', {
        redirect_uri: 'https://example.com/callback',
      })
      expect(sessionStorageSetItem).toHaveBeenCalledWith('oidc_state', 'test-state')
      expect(sessionStorageSetItem).toHaveBeenCalledWith('oidc_nonce', 'test-nonce')
      expect(result).toEqual(mockResponse.data)
    })

    it('should use default redirect URI if not provided', async () => {
      const mockResponse = {
        data: {
          auth_url: 'https://auth.example.com/authorize',
          state: 'test-state',
          nonce: 'test-nonce',
        },
      }

      mockAxiosInstance.post.mockResolvedValue(mockResponse)

      await authService.login()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/auth/oidc/login', {
        redirect_uri: `${window.location.origin}/auth/callback`,
      })
    })

    it('should handle login errors', async () => {
      const mockError = {
        response: {
          data: {
            error: 'invalid_request',
            error_description: 'Invalid request parameters',
          },
        },
      }

      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(authService.login()).rejects.toMatchObject({
        error: 'invalid_request',
        error_description: 'Invalid request parameters',
      })
    })
  })

  describe('handleCallback', () => {
    it('should handle OIDC callback successfully', async () => {
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
        access_token: 'access-token-123',
        id_token: 'id-token-123',
        refresh_token: 'refresh-token-123',
        expires_in: 3600,
        token_type: 'Bearer',
        scope: 'openid profile email',
      }

      const mockResponse = {
        data: {
          user: mockUser,
          tokens: mockTokens,
        },
      }

      // Mock sessionStorage to return valid state
      vi.spyOn(sessionStorage, 'getItem').mockImplementation((key) => {
        if (key === 'oidc_state') return 'test-state'
        return null
      })

      mockAxiosInstance.post.mockResolvedValue(mockResponse)
      const localStorageSetItem = vi.spyOn(localStorage, 'setItem')
      const sessionStorageRemoveItem = vi.spyOn(sessionStorage, 'removeItem')

      const result = await authService.handleCallback('test-code', 'test-state')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/auth/oidc/callback', {
        code: 'test-code',
        state: 'test-state',
        redirect_uri: `${window.location.origin}/auth/callback`,
      })
      expect(localStorageSetItem).toHaveBeenCalledWith('sprintconnect_tokens', JSON.stringify(mockTokens))
      expect(localStorageSetItem).toHaveBeenCalledWith('sprintconnect_user', JSON.stringify(mockUser))
      expect(sessionStorageRemoveItem).toHaveBeenCalledWith('oidc_state')
      expect(sessionStorageRemoveItem).toHaveBeenCalledWith('oidc_nonce')
      expect(result).toEqual(mockResponse.data)
    })

    it('should reject callback with invalid state', async () => {
      vi.spyOn(sessionStorage, 'getItem').mockImplementation((key) => {
        if (key === 'oidc_state') return 'different-state'
        return null
      })

      // Ensure axios is not called when state validation fails
      mockAxiosInstance.post.mockClear()

      await expect(authService.handleCallback('test-code', 'test-state')).rejects.toThrow('Invalid state parameter')
      
      // Verify axios was not called
      expect(mockAxiosInstance.post).not.toHaveBeenCalled()
    })

    it('should reject callback with missing state', async () => {
      vi.spyOn(sessionStorage, 'getItem').mockReturnValue(null)

      // Ensure axios is not called when state validation fails
      mockAxiosInstance.post.mockClear()

      await expect(authService.handleCallback('test-code', 'test-state')).rejects.toThrow('Invalid state parameter')
      
      // Verify axios was not called
      expect(mockAxiosInstance.post).not.toHaveBeenCalled()
    })
  })

  describe('logout', () => {
    it('should initiate logout flow successfully', async () => {
      const mockResponse = {
        data: {
          logout_url: 'https://auth.example.com/logout?post_logout_redirect_uri=test',
        },
      }

      mockAxiosInstance.post.mockResolvedValue(mockResponse)
      const localStorageRemoveItem = vi.spyOn(localStorage, 'removeItem')
      const sessionStorageRemoveItem = vi.spyOn(sessionStorage, 'removeItem')

      const result = await authService.logout('https://example.com')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/auth/oidc/logout', {
        post_logout_redirect_uri: 'https://example.com',
      })
      expect(localStorageRemoveItem).toHaveBeenCalledWith('sprintconnect_tokens')
      expect(localStorageRemoveItem).toHaveBeenCalledWith('sprintconnect_user')
      expect(sessionStorageRemoveItem).toHaveBeenCalledWith('oidc_state')
      expect(sessionStorageRemoveItem).toHaveBeenCalledWith('oidc_nonce')
      expect(result).toEqual(mockResponse.data)
    })

    it('should clear local data even if logout fails', async () => {
      mockAxiosInstance.post.mockRejectedValue(new Error('Network error'))
      const localStorageRemoveItem = vi.spyOn(localStorage, 'removeItem')

      await expect(authService.logout()).rejects.toThrow()

      expect(localStorageRemoveItem).toHaveBeenCalledWith('sprintconnect_tokens')
      expect(localStorageRemoveItem).toHaveBeenCalledWith('sprintconnect_user')
    })
  })

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      const mockTokens: AuthTokens = {
        access_token: 'new-access-token',
        id_token: 'new-id-token',
        refresh_token: 'new-refresh-token',
        expires_in: 3600,
        token_type: 'Bearer',
        scope: 'openid profile email',
      }

      const mockResponse = {
        data: {
          tokens: mockTokens,
        },
      }

      // Mock localStorage to return existing tokens
      vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
        if (key === 'sprintconnect_tokens') {
          return JSON.stringify({
            refresh_token: 'old-refresh-token',
          })
        }
        return null
      })

      mockAxiosInstance.post.mockResolvedValue(mockResponse)
      const localStorageSetItem = vi.spyOn(localStorage, 'setItem')

      const result = await authService.refreshToken()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        refresh_token: 'old-refresh-token',
      })
      expect(localStorageSetItem).toHaveBeenCalledWith('sprintconnect_tokens', JSON.stringify(mockTokens))
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle refresh token failure', async () => {
      vi.spyOn(localStorage, 'getItem').mockReturnValue(null)

      await expect(authService.refreshToken()).rejects.toThrow('No refresh token available')
    })
  })

  describe('isAuthenticated', () => {
    it('should return true for valid authentication', () => {
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
        last_login_at: new Date().toISOString(),
      }

      const mockTokens: AuthTokens = {
        access_token: 'access-token',
        id_token: 'id-token',
        expires_in: 3600,
        token_type: 'Bearer',
        scope: 'openid profile email',
      }

      vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
        if (key === 'sprintconnect_user') return JSON.stringify(mockUser)
        if (key === 'sprintconnect_tokens') return JSON.stringify(mockTokens)
        return null
      })

      expect(authService.isAuthenticated()).toBe(true)
    })

    it('should return false for missing user', () => {
      vi.spyOn(localStorage, 'getItem').mockReturnValue(null)

      expect(authService.isAuthenticated()).toBe(false)
    })

    it('should return false for missing tokens', () => {
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

      vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
        if (key === 'sprintconnect_user') return JSON.stringify(mockUser)
        return null
      })

      expect(authService.isAuthenticated()).toBe(false)
    })

    it('should return false for expired token', () => {
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
        last_login_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      }

      const mockTokens: AuthTokens = {
        access_token: 'access-token',
        id_token: 'id-token',
        expires_in: 3600, // 1 hour
        token_type: 'Bearer',
        scope: 'openid profile email',
      }

      vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
        if (key === 'sprintconnect_user') return JSON.stringify(mockUser)
        if (key === 'sprintconnect_tokens') return JSON.stringify(mockTokens)
        return null
      })

      expect(authService.isAuthenticated()).toBe(false)
    })
  })

  describe('getCurrentUser', () => {
    it('should return user from localStorage', () => {
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

      vi.spyOn(localStorage, 'getItem').mockReturnValue(JSON.stringify(mockUser))

      expect(authService.getCurrentUser()).toEqual(mockUser)
    })

    it('should return null for invalid JSON', () => {
      vi.spyOn(localStorage, 'getItem').mockReturnValue('invalid-json')

      expect(authService.getCurrentUser()).toBeNull()
    })

    it('should return null for missing user', () => {
      vi.spyOn(localStorage, 'getItem').mockReturnValue(null)

      expect(authService.getCurrentUser()).toBeNull()
    })
  })
})
