
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { lightTheme } from './styles/theme'
import { AuthProvider } from './hooks/useAuth'
import { Layout } from './components/layout/Layout'
import { ProtectedRoute } from './components/common/ProtectedRoute'

// Pages
import { LoginPage } from './pages/auth/LoginPage'
import { CallbackPage } from './pages/auth/CallbackPage'
import { DashboardPage } from './pages/DashboardPage'
import RegistryPage from './pages/registry/RegistryPage'
import DiscoveryPage from './pages/discovery/DiscoveryPage'
import ChatPage from './pages/chat/ChatPage'
import { AnalyticsPage } from './pages/analytics/AnalyticsPage'
import { AdminPage } from './pages/admin/AdminPage'
import { SettingsPage } from './pages/SettingsPage'
import { NotFoundPage } from './pages/NotFoundPage'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={lightTheme}>
        <CssBaseline />
        <Router>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/auth/login" element={<LoginPage />} />
              <Route path="/auth/callback" element={<CallbackPage />} />
              
              {/* Protected routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="registry" element={<RegistryPage />} />
                <Route path="discovery" element={<DiscoveryPage />} />
                <Route path="chat" element={<ChatPage />} />
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="admin" element={<AdminPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
              
              {/* 404 route */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AuthProvider>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
