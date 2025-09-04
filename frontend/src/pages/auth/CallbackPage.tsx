/**
 * OIDC Callback Page Component for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import { useEffect, useState } from 'react'
import { useSearchParams, Navigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Stack,
} from '@mui/material'
import { CheckCircle as CheckCircleIcon, Error as ErrorIcon } from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'
import { authService } from '../../hooks/useAuth'

export function CallbackPage() {
  const [searchParams] = useSearchParams()
  const { isAuthenticated, error } = useAuth()
  const [callbackStatus, setCallbackStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [callbackError, setCallbackError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        // Handle OIDC error response
        if (error) {
          setCallbackStatus('error')
          setCallbackError(errorDescription || error)
          return
        }

        // Validate required parameters
        if (!code || !state) {
          setCallbackStatus('error')
          setCallbackError('Missing required authentication parameters')
          return
        }

        // Process the callback
        await authService.handleCallback(code, state)
        setCallbackStatus('success')
      } catch (error) {
        console.error('Callback processing error:', error)
        setCallbackStatus('error')
        setCallbackError(error instanceof Error ? error.message : 'Authentication failed')
      }
    }

    handleCallback()
  }, [searchParams])

  // Redirect if already authenticated and callback was successful
  if (isAuthenticated && callbackStatus === 'success') {
    return <Navigate to="/dashboard" replace />
  }

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
              {/* Status Icon */}
              <Box>
                {callbackStatus === 'processing' && (
                  <CircularProgress size={48} color="primary" />
                )}
                {callbackStatus === 'success' && (
                  <CheckCircleIcon 
                    sx={{ 
                      fontSize: 48, 
                      color: 'success.main' 
                    }} 
                  />
                )}
                {callbackStatus === 'error' && (
                  <ErrorIcon 
                    sx={{ 
                      fontSize: 48, 
                      color: 'error.main' 
                    }} 
                  />
                )}
              </Box>

              {/* Status Message */}
              <Box textAlign="center">
                {callbackStatus === 'processing' && (
                  <>
                    <Typography variant="h5" gutterBottom>
                      Completing Sign In
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Please wait while we complete your authentication...
                    </Typography>
                  </>
                )}
                
                {callbackStatus === 'success' && (
                  <>
                    <Typography variant="h5" gutterBottom color="success.main">
                      Sign In Successful
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Redirecting to your dashboard...
                    </Typography>
                  </>
                )}
                
                {callbackStatus === 'error' && (
                  <>
                    <Typography variant="h5" gutterBottom color="error.main">
                      Sign In Failed
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      There was an error completing your authentication.
                    </Typography>
                  </>
                )}
              </Box>

              {/* Error Details */}
              {(callbackError || error) && (
                <Alert 
                  severity="error" 
                  sx={{ width: '100%' }}
                >
                  {callbackError || error}
                </Alert>
              )}

              {/* Loading Indicator */}
              {callbackStatus === 'processing' && (
                <Box textAlign="center">
                  <Typography variant="caption" color="text.secondary">
                    This may take a few moments
                  </Typography>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>

        {/* Footer */}
        <Box mt={4} textAlign="center">
          <Typography variant="caption" color="text.secondary">
            If you continue to experience issues, please contact your administrator
          </Typography>
        </Box>
      </Box>
    </Container>
  )
}
