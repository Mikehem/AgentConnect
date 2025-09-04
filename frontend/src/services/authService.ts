/**
 * Authentication Service for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import axios, { AxiosInstance } from 'axios'
import {
  LoginRequest,
  LoginResponse,
  CallbackRequest,
  CallbackResponse,
  LogoutRequest,
  LogoutResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  AuthError,
  AuthTokens,
  User,
} from '../types/auth'

export class AuthService {
  private api: AxiosInstance
  private tokenStorageKey = 'sprintconnect_tokens'
  private userStorageKey = 'sprintconnect_user'

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      (config) => {
        const tokens = this.getStoredTokens()
        if (tokens?.access_token) {
          config.headers.Authorization = `Bearer ${tokens.access_token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Add response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            await this.refreshToken()
            const tokens = this.getStoredTokens()
            if (tokens?.access_token) {
              originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`
            }
            return this.api(originalRequest)
          } catch (refreshError) {
            this.clearStoredAuth()
            window.location.href = '/auth/login'
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  /**
   * Initiate OIDC login flow
   */
  async login(redirectUri?: string): Promise<LoginResponse> {
    try {
      const request: LoginRequest = {
        redirect_uri: redirectUri || `${window.location.origin}/auth/callback`,
      }

      const response = await this.api.post<LoginResponse>('/api/v1/auth/oidc/login', request)
      
      // Store state and nonce for validation
      if (response.data.state) {
        sessionStorage.setItem('oidc_state', response.data.state)
      }
      if (response.data.nonce) {
        sessionStorage.setItem('oidc_nonce', response.data.nonce)
      }

      return response.data
    } catch (error) {
      throw this.handleAuthError(error)
    }
  }

  /**
   * Handle OIDC callback
   */
  async handleCallback(code: string, state: string, redirectUri?: string): Promise<CallbackResponse> {
    try {
      // Validate state parameter
      const storedState = sessionStorage.getItem('oidc_state')
      if (!storedState || storedState !== state) {
        throw new Error('Invalid state parameter')
      }

      const request: CallbackRequest = {
        code,
        state,
        redirect_uri: redirectUri || `${window.location.origin}/auth/callback`,
      }

      const response = await this.api.post<CallbackResponse>('/api/v1/auth/oidc/callback', request)
      
      // Store tokens and user info
      this.storeTokens(response.data.tokens)
      this.storeUser(response.data.user)

      // Clean up session storage
      sessionStorage.removeItem('oidc_state')
      sessionStorage.removeItem('oidc_nonce')

      return response.data
    } catch (error) {
      throw this.handleAuthError(error)
    }
  }

  /**
   * Initiate logout flow
   */
  async logout(postLogoutRedirectUri?: string): Promise<LogoutResponse> {
    try {
      const request: LogoutRequest = {
        post_logout_redirect_uri: postLogoutRedirectUri || window.location.origin,
      }

      const response = await this.api.post<LogoutResponse>('/api/v1/auth/oidc/logout', request)
      
      // Clear stored auth data
      this.clearStoredAuth()

      return response.data
    } catch (error) {
      // Even if logout fails on server, clear local data
      this.clearStoredAuth()
      throw this.handleAuthError(error)
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<RefreshTokenResponse> {
    try {
      const tokens = this.getStoredTokens()
      if (!tokens?.refresh_token) {
        throw new Error('No refresh token available')
      }

      const request: RefreshTokenRequest = {
        refresh_token: tokens.refresh_token,
      }

      const response = await this.api.post<RefreshTokenResponse>('/api/v1/auth/refresh', request)
      
      // Update stored tokens
      this.storeTokens(response.data.tokens)

      return response.data
    } catch (error) {
      this.clearStoredAuth()
      throw this.handleAuthError(error)
    }
  }

  /**
   * Get current user from storage
   */
  getCurrentUser(): User | null {
    try {
      const userStr = localStorage.getItem(this.userStorageKey)
      return userStr ? JSON.parse(userStr) : null
    } catch {
      return null
    }
  }

  /**
   * Get stored tokens
   */
  getStoredTokens(): AuthTokens | null {
    try {
      const tokensStr = localStorage.getItem(this.tokenStorageKey)
      return tokensStr ? JSON.parse(tokensStr) : null
    } catch {
      return null
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const tokens = this.getStoredTokens()
    const user = this.getCurrentUser()
    
    if (!tokens || !user) {
      return false
    }

    // Check if token is expired (with 5 minute buffer)
    const now = Math.floor(Date.now() / 1000)
    const expiresAt = tokens.expires_in + (user.last_login_at ? Math.floor(new Date(user.last_login_at).getTime() / 1000) : now)
    
    return expiresAt > now + 300 // 5 minute buffer
  }

  /**
   * Store authentication tokens
   */
  private storeTokens(tokens: AuthTokens): void {
    localStorage.setItem(this.tokenStorageKey, JSON.stringify(tokens))
  }

  /**
   * Store user information
   */
  private storeUser(user: User): void {
    localStorage.setItem(this.userStorageKey, JSON.stringify(user))
  }

  /**
   * Clear stored authentication data
   */
  public clearStoredAuth(): void {
    localStorage.removeItem(this.tokenStorageKey)
    localStorage.removeItem(this.userStorageKey)
    sessionStorage.removeItem('oidc_state')
    sessionStorage.removeItem('oidc_nonce')
  }

  /**
   * Handle authentication errors
   */
  private handleAuthError(error: any): AuthError {
    if (error.response?.data) {
      return {
        error: error.response.data.error || 'authentication_error',
        error_description: error.response.data.error_description || error.response.data.detail,
        error_uri: error.response.data.error_uri,
        state: error.response.data.state,
      }
    }

    if (error.message) {
      return {
        error: 'network_error',
        error_description: error.message,
      }
    }

    return {
      error: 'unknown_error',
      error_description: 'An unknown error occurred during authentication',
    }
  }
}

// Export singleton instance
export const authService = new AuthService()
