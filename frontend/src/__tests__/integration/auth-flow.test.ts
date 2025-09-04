/**
 * Authentication Flow Integration Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect } from 'vitest'

describe('OIDC Authentication Flow Integration', () => {
  it('should initiate login flow with redirect', async () => {
    const response = await fetch('http://localhost:8000/v1/auth/oidc/login', {
      method: 'GET',
      redirect: 'manual' // Don't follow redirects automatically
    })
    
    // Should return a redirect response
    expect(response.status).toBe(302)
    expect(response.headers.get('location')).toContain('logto.app')
  })

  it('should handle logout flow', async () => {
    const response = await fetch('http://localhost:8000/v1/auth/oidc/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        post_logout_redirect_uri: 'http://localhost:3000'
      })
    })
    
    expect(response.ok).toBe(true)
    
    const data = await response.json()
    expect(data).toHaveProperty('logout_url')
    expect(data.logout_url).toContain('logto.app')
  })

  it('should validate callback parameters', async () => {
    // Test callback with invalid parameters (should fail gracefully)
    const response = await fetch('http://localhost:8000/v1/auth/oidc/callback?code=invalid-code&state=invalid-state', {
      method: 'GET'
    })
    
    // Should return an error (not 404)
    expect(response.status).not.toBe(404)
    expect(response.status).toBeGreaterThanOrEqual(400)
  })

  it('should have proper CORS headers for frontend', async () => {
    const response = await fetch('http://localhost:8000/health', {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    })
    
    // CORS preflight should be handled
    expect(response.status).toBeLessThan(500)
  })
})
