/**
 * Protected Route Component for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Box, CircularProgress, Typography } from '@mui/material'
import { useAuth } from '../../hooks/useAuth'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermissions?: string[]
  requiredRoles?: string[]
  fallbackPath?: string
}

export function ProtectedRoute({
  children,
  requiredPermissions = [],
  requiredRoles = [],
  fallbackPath = '/auth/login',
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, hasPermission, hasRole } = useAuth()
  const location = useLocation()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Authenticating...
        </Typography>
      </Box>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return (
      <Navigate
        to={fallbackPath}
        state={{ from: location }}
        replace
      />
    )
  }

  // Check required permissions
  if (requiredPermissions.length > 0) {
    const hasRequiredPermissions = requiredPermissions.every(permission =>
      hasPermission(permission as any)
    )
    
    if (!hasRequiredPermissions) {
      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="100vh"
          gap={2}
          p={4}
        >
          <Typography variant="h5" color="error" textAlign="center">
            Access Denied
          </Typography>
          <Typography variant="body1" color="text.secondary" textAlign="center">
            You don't have the required permissions to access this page.
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Required permissions: {requiredPermissions.join(', ')}
          </Typography>
        </Box>
      )
    }
  }

  // Check required roles
  if (requiredRoles.length > 0) {
    const hasRequiredRoles = requiredRoles.some(role =>
      hasRole(role as any)
    )
    
    if (!hasRequiredRoles) {
      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="100vh"
          gap={2}
          p={4}
        >
          <Typography variant="h5" color="error" textAlign="center">
            Access Denied
          </Typography>
          <Typography variant="body1" color="text.secondary" textAlign="center">
            You don't have the required role to access this page.
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Required roles: {requiredRoles.join(', ')}
          </Typography>
        </Box>
      )
    }
  }

  // User is authenticated and has required permissions/roles
  return <>{children}</>
}
