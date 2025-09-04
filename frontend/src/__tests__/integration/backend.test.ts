/**
 * Backend Integration Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect } from 'vitest'

describe('Backend Integration', () => {
  it('should connect to backend health endpoint', async () => {
    const response = await fetch('http://localhost:8000/health')
    expect(response.ok).toBe(true)
    
    const data = await response.json()
    expect(data).toHaveProperty('status')
    expect(data).toHaveProperty('version')
    expect(data).toHaveProperty('timestamp')
    expect(data.status).toBe('healthy')
  })

  it('should have correct API base URL configured', () => {
    expect(import.meta.env.VITE_API_BASE_URL).toBe('http://localhost:8000')
  })

  it('should be able to access OIDC endpoints', async () => {
    // Test that OIDC endpoints are accessible (they should return 405 for GET without proper params)
    const loginResponse = await fetch('http://localhost:8000/api/v1/auth/oidc/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        redirect_uri: 'http://localhost:3000/auth/callback'
      })
    })
    
    // Should not be 404 (endpoint exists) but might be 422 (validation error) or 500 (server error)
    expect(loginResponse.status).not.toBe(404)
  })
})
