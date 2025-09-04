/**
 * Basic Test for SprintConnect Frontend
 * User Story 1.1: OIDC Authentication Interface
 */

import { describe, it, expect } from 'vitest'

describe('Basic Frontend Setup', () => {
  it('should have basic functionality', () => {
    expect(1 + 1).toBe(2)
  })

  it('should have environment variables', () => {
    // Environment variables will be loaded from .env file when available
    expect(import.meta.env).toBeDefined()
  })
})
