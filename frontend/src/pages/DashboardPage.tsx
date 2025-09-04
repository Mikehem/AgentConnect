/**
 * Dashboard Page Component for SprintConnect
 */


import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
} from '@mui/material'
import { useAuth } from '../hooks/useAuth'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome to SprintConnect
      </Typography>
      
      {user && (
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Hello, {user.name}! You're logged in as {user.email}
        </Typography>
      )}

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid sx={{ xs: 12, md: 6, lg: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                MCP Servers
              </Typography>
              <Typography variant="h4" color="primary">
                0
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Registered servers
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid sx={{ xs: 12, md: 6, lg: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Sessions
              </Typography>
              <Typography variant="h4" color="primary">
                0
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Chat sessions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid sx={{ xs: 12, md: 6, lg: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Capabilities
              </Typography>
              <Typography variant="h4" color="primary">
                0
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Discovered tools
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid sx={{ xs: 12, md: 6, lg: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Health Status
              </Typography>
              <Typography variant="h4" color="success.main">
                Good
              </Typography>
              <Typography variant="body2" color="text.secondary">
                System status
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ mt: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Recent Activity
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No recent activity to display.
        </Typography>
      </Paper>
    </Box>
  )
}
