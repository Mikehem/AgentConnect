
import { Typography, Box, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="50vh"
      textAlign="center"
    >
      <Typography variant="h1" color="primary" gutterBottom>
        404
      </Typography>
      <Typography variant="h4" gutterBottom>
        Page Not Found
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        The page you're looking for doesn't exist.
      </Typography>
      <Button
        variant="contained"
        onClick={() => navigate('/dashboard')}
        sx={{ mt: 2 }}
      >
        Go to Dashboard
      </Button>
    </Box>
  )
}
