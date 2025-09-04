/**
 * Frontend-Backend Integration Tests for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect } from 'vitest'

describe('Frontend-Backend Integration', () => {
  it('should have frontend accessible on port 3000', async () => {
    const response = await fetch('http://localhost:3000')
    expect(response.ok).toBe(true)
    expect(response.headers.get('content-type')).toContain('text/html')
  })

  it('should have backend accessible on port 8000', async () => {
    const response = await fetch('http://localhost:8000/health')
    expect(response.ok).toBe(true)
    
    const data = await response.json()
    expect(data.status).toBe('healthy')
  })

  it('should have correct environment configuration', () => {
    expect(import.meta.env.VITE_API_BASE_URL).toBe('http://localhost:8000')
    expect(import.meta.env.VITE_WS_BASE_URL).toBe('ws://localhost:8000')
  })

  it('should be able to access OIDC login endpoint from frontend perspective', async () => {
    // Test the actual OIDC flow that the frontend would use
    const response = await fetch('http://localhost:8000/v1/auth/oidc/login', {
      method: 'GET',
      redirect: 'manual'
    })
    
    // Should redirect to Logto Cloud
    expect(response.status).toBe(302)
    const location = response.headers.get('location')
    expect(location).toContain('logto.app')
    expect(location).toContain('client_id')
  })

  it('should handle CORS properly for frontend requests', async () => {
    const response = await fetch('http://localhost:8000/health', {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type, Authorization'
      }
    })
    
    // CORS preflight should be handled
    expect(response.status).toBeLessThan(500)
    
    // Check for CORS headers
    const corsHeaders = [
      'Access-Control-Allow-Origin',
      'Access-Control-Allow-Methods',
      'Access-Control-Allow-Headers'
    ]
    
    // At least some CORS headers should be present
    const hasCorsHeaders = corsHeaders.some(header => 
      response.headers.get(header) !== null
    )
    expect(hasCorsHeaders).toBe(true)
  })

  it('should be able to access MCP server endpoints (with auth)', async () => {
    // Test that MCP server endpoints exist and require authentication
    const response = await fetch('http://localhost:8000/v1/mcp/servers', {
      method: 'GET'
    })
    
    // Should require authentication (401 or 403)
    expect([401, 403]).toContain(response.status)
  })

  it('should be able to access public MCP registration endpoint', async () => {
    // Test the public MCP registration endpoint
    const response = await fetch('http://localhost:8000/v1/mcp/servers/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'Test Server',
        description: 'Test MCP server',
        base_url: 'https://test.example.com',
        environment: 'development',
        tags: ['test']
      })
    })
    
    // Should not require authentication (not 401/403)
    expect([401, 403]).not.toContain(response.status)
    // Should return some response (could be validation error, but not auth error)
    expect(response.status).toBeLessThan(500)
  })

  it('should have proper API versioning', async () => {
    // Test that API versioning is working
    const v1Response = await fetch('http://localhost:8000/v1/mcp/servers', {
      method: 'GET'
    })
    
    // v1 endpoint should exist and require authentication (401 is expected)
    expect(v1Response.status).toBe(401)
  })

  it('should have WebSocket endpoint available', async () => {
    // Test that WebSocket endpoint is accessible
    // Note: This is a basic connectivity test, not a full WebSocket test
    const response = await fetch('http://localhost:8000/ws/health/test-server', {
      method: 'GET'
    })
    
    // WebSocket endpoint should be available (might return 426 Upgrade Required)
    expect([404, 500]).not.toContain(response.status)
  })

  it('should have proper error handling', async () => {
    // Test error handling for non-existent endpoint
    const response = await fetch('http://localhost:8000/non-existent-endpoint')
    // Middleware protects all endpoints, so 401 is expected instead of 404
    expect(response.status).toBe(401)
    
    const errorData = await response.json()
    expect(errorData).toHaveProperty('detail')
    expect(errorData).toHaveProperty('request_id')
  })

  it('should have proper request ID handling', async () => {
    // Test that request IDs are properly handled
    const response = await fetch('http://localhost:8000/health', {
      headers: {
        'X-Request-ID': 'test-request-123'
      }
    })
    
    expect(response.ok).toBe(true)
    expect(response.headers.get('X-Request-ID')).toBe('test-request-123')
  })
})
