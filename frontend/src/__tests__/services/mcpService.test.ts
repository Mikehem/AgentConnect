/**
 * Unit tests for MCP Service
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mcpService } from '../../services/mcpService';

// Mock axios completely
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    }))
  }
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
  },
  writable: true,
});

describe('McpService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('mock-token');
  });

  it('should be defined', () => {
    expect(mcpService).toBeDefined();
  });

  it('should have listServers method', () => {
    expect(typeof mcpService.listServers).toBe('function');
  });

  it('should have createServer method', () => {
    expect(typeof mcpService.createServer).toBe('function');
  });

  it('should have getServer method', () => {
    expect(typeof mcpService.getServer).toBe('function');
  });

  it('should have updateServer method', () => {
    expect(typeof mcpService.updateServer).toBe('function');
  });

  it('should have deleteServer method', () => {
    expect(typeof mcpService.deleteServer).toBe('function');
  });

  it('should have getServerHealth method', () => {
    expect(typeof mcpService.getServerHealth).toBe('function');
  });

  it('should have discoverCapabilities method', () => {
    expect(typeof mcpService.discoverCapabilities).toBe('function');
  });

  it('should have testCapability method', () => {
    expect(typeof mcpService.testCapability).toBe('function');
  });
});