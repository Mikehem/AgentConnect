/**
 * Login Page Component for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Container,
  Stack,
} from '@mui/material'
import { Login as LoginIcon, Security as SecurityIcon } from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'

export function LoginPage() {
  const { isAuthenticated, isLoading, error, login, clearError } = useAuth()

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleLogin = async () => {
    try {
      clearError()
      await login()
    } catch (error) {
      // Error is handled by the auth context
      console.error('Login failed:', error)
    }
  }

  // Clear error when component unmounts
  useEffect(() => {
    return () => {
      clearError()
    }
  }, [clearError])

  return (
    <Container maxWidth="sm">
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        py={4}
      >
        <Card sx={{ width: '100%', maxWidth: 400 }}>
          <CardContent sx={{ p: 4 }}>
            <Stack spacing={3} alignItems="center">
              {/* Logo and Title */}
              <Box textAlign="center">
                <SecurityIcon 
                  sx={{ 
                    fontSize: 48, 
                    color: 'primary.main',
                    mb: 2 
                  }} 
                />
                <Typography variant="h4" component="h1" gutterBottom>
                  SprintConnect
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Enterprise MCP Server Management Platform
                </Typography>
              </Box>

              {/* Error Alert */}
              {error && (
                <Alert 
                  severity="error" 
                  sx={{ width: '100%' }}
                  onClose={clearError}
                >
                  {error}
                </Alert>
              )}

              {/* Login Button */}
              <Button
                variant="contained"
                size="large"
                fullWidth
                startIcon={isLoading ? <CircularProgress size={20} /> : <LoginIcon />}
                onClick={handleLogin}
                disabled={isLoading}
                sx={{
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                }}
              >
                {isLoading ? 'Signing In...' : 'Sign In with OIDC'}
              </Button>

              {/* Additional Info */}
              <Box textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Secure authentication powered by OIDC
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                  You will be redirected to your organization's identity provider
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Footer */}
        <Box mt={4} textAlign="center">
          <Typography variant="caption" color="text.secondary">
            © 2024 SprintConnect. All rights reserved.
          </Typography>
        </Box>
      </Box>
    </Container>
  )
}
