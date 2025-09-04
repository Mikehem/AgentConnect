/**
 * Authentication Hook for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'
import { AuthContextType, AuthState, Permission, Role, AuthError } from '../types/auth'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const navigate = useNavigate()
  
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    tokens: null,
    error: null,
  })

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }))

        const isAuth = authService.isAuthenticated()
        const user = authService.getCurrentUser()
        const tokens = authService.getStoredTokens()

        if (isAuth && user && tokens) {
          setState({
            isAuthenticated: true,
            isLoading: false,
            user,
            tokens,
            error: null,
          })
        } else {
          // Clear invalid auth data
          authService.clearStoredAuth()
          setState({
            isAuthenticated: false,
            isLoading: false,
            user: null,
            tokens: null,
            error: null,
          })
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        setState({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          tokens: null,
          error: 'Failed to initialize authentication',
        })
      }
    }

    initializeAuth()
  }, [])

  // Auto-refresh token before expiration
  useEffect(() => {
    if (!state.isAuthenticated || !state.tokens) return

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto token refresh failed:', error)
        // Don't logout immediately, let the interceptor handle it
      }
    }, 5 * 60 * 1000) // Check every 5 minutes

    return () => clearInterval(refreshInterval)
  }, [state.isAuthenticated, state.tokens])

  const login = useCallback(async (redirectUri?: string) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))

      const response = await authService.login(redirectUri)
      
      // Redirect to OIDC provider
      window.location.href = response.auth_url
    } catch (error) {
      const authError = error as AuthError
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: authError.error_description || 'Login failed',
      }))
      throw error
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))

      const response = await authService.logout()
      
      // Redirect to OIDC provider logout
      window.location.href = response.logout_url
    } catch (error) {
      const authError = error as AuthError
      console.error('Logout error:', authError)
      
      // Even if logout fails, clear local state and redirect
      setState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        tokens: null,
        error: null,
      })
      
      navigate('/auth/login')
    }
  }, [navigate])

  const refreshToken = useCallback(async () => {
    try {
      const response = await authService.refreshToken()
      
      setState(prev => ({
        ...prev,
        tokens: response.tokens,
        error: null,
      }))
    } catch (error) {
      const authError = error as AuthError
      console.error('Token refresh error:', authError)
      
      setState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        tokens: null,
        error: authError.error_description || 'Token refresh failed',
      })
      
      navigate('/auth/login')
      throw error
    }
  }, [navigate])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  const hasPermission = useCallback((permission: Permission): boolean => {
    if (!state.user) return false
    return state.user.permissions.includes(permission)
  }, [state.user])

  const hasRole = useCallback((role: Role): boolean => {
    if (!state.user) return false
    return state.user.roles.includes(role)
  }, [state.user])

  const hasAnyPermission = useCallback((permissions: Permission[]): boolean => {
    if (!state.user) return false
    return permissions.some(permission => state.user!.permissions.includes(permission))
  }, [state.user])

  const hasAnyRole = useCallback((roles: Role[]): boolean => {
    if (!state.user) return false
    return roles.some(role => state.user!.roles.includes(role))
  }, [state.user])



  const contextValue: AuthContextType = {
    // State
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    user: state.user,
    error: state.error,
    
    // Actions
    login,
    logout,
    refreshToken,
    clearError,
    
    // Utilities
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAnyRole,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Export the callback handler for use in callback page
export { authService }
