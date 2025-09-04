/**
 * Authentication Types for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

export interface User {
  id: string
  email: string
  name: string
  given_name?: string
  family_name?: string
  picture?: string
  email_verified: boolean
  org_id: string
  org_name: string
  roles: string[]
  permissions: string[]
  created_at: string
  last_login_at?: string
}

export interface AuthTokens {
  access_token: string
  id_token: string
  refresh_token?: string
  expires_in: number
  token_type: string
  scope: string
}

export interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  tokens: AuthTokens | null
  error: string | null
}

export interface LoginRequest {
  redirect_uri: string
  state?: string
  nonce?: string
}

export interface LoginResponse {
  auth_url: string
  state: string
  nonce: string
}

export interface CallbackRequest {
  code: string
  state: string
  redirect_uri: string
}

export interface CallbackResponse {
  user: User
  tokens: AuthTokens
}

export interface LogoutRequest {
  post_logout_redirect_uri?: string
}

export interface LogoutResponse {
  logout_url: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  tokens: AuthTokens
}

export interface AuthError {
  error: string
  error_description?: string
  error_uri?: string
  state?: string
}

// OIDC Configuration
export interface OIDCConfig {
  authority: string
  client_id: string
  redirect_uri: string
  post_logout_redirect_uri: string
  response_type: string
  scope: string
  automaticSilentRenew: boolean
  includeIdTokenInSilentRenew: boolean
  loadUserInfo: boolean
  filterProtocolClaims: boolean
  clockSkew: number
}

// Permission types
export type Permission = 
  | 'mcp:servers:read'
  | 'mcp:servers:create'
  | 'mcp:servers:update'
  | 'mcp:servers:delete'
  | 'mcp:servers:test'
  | 'mcp:capabilities:discover'
  | 'mcp:chat:create'
  | 'mcp:chat:read'
  | 'mcp:chat:delete'
  | 'mcp:analytics:read'
  | 'mcp:analytics:export'
  | 'admin:users:read'
  | 'admin:users:create'
  | 'admin:users:update'
  | 'admin:users:delete'
  | 'admin:organizations:read'
  | 'admin:organizations:update'
  | 'admin:audit:read'
  | 'admin:webhooks:read'
  | 'admin:webhooks:create'
  | 'admin:webhooks:update'
  | 'admin:webhooks:delete'

export type Role = 
  | 'viewer'
  | 'engineer'
  | 'admin'
  | 'owner'

// Auth context type
export interface AuthContextType {
  // State
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  error: string | null
  
  // Actions
  login: (redirectUri?: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  clearError: () => void
  
  // Utilities
  hasPermission: (permission: Permission) => boolean
  hasRole: (role: Role) => boolean
  hasAnyPermission: (permissions: Permission[]) => boolean
  hasAnyRole: (roles: Role[]) => boolean
}
