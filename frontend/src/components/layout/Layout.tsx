/**
 * Main Layout Component for SprintConnect
 * User Story 1.1: OIDC Authentication Interface
 */

import React from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,

  Avatar,
  Menu,
  MenuItem,
  IconButton,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CssBaseline,
} from '@mui/material'
import {
  AccountCircle as AccountIcon,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  Storage as RegistryIcon,
  Search as DiscoveryIcon,
  Chat as ChatIcon,
  Analytics as AnalyticsIcon,
  AdminPanelSettings as AdminIcon,
} from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'

const drawerWidth = 240

const navigationItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Server Registry', icon: <RegistryIcon />, path: '/registry' },
  { text: 'Discovery', icon: <DiscoveryIcon />, path: '/discovery' },
  { text: 'Chat Testing', icon: <ChatIcon />, path: '/chat' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Admin', icon: <AdminIcon />, path: '/admin' },
]

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    handleMenuClose()
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const handleSettings = () => {
    handleMenuClose()
    navigate('/settings')
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          width: `calc(100% - ${drawerWidth}px)`, 
          ml: `${drawerWidth}px`,
          zIndex: (theme) => theme.zIndex.drawer + 1 
        }}
      >
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SprintConnect
          </Typography>
          
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" color="inherit">
                {user.name}
              </Typography>
              <Typography variant="caption" color="inherit">
                {user.org_name}
              </Typography>
              
              <IconButton
                size="large"
                onClick={handleMenuOpen}
                color="inherit"
                aria-label="account menu"
              >
                {user.picture ? (
                  <Avatar
                    src={user.picture}
                    alt={user.name}
                    sx={{ width: 32, height: 32 }}
                  />
                ) : (
                  <AccountIcon />
                )}
              </IconButton>
              
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
              >
                <MenuItem onClick={handleSettings}>
                  <SettingsIcon sx={{ mr: 1 }} />
                  Settings
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>
                  <LogoutIcon sx={{ mr: 1 }} />
                  Sign Out
                </MenuItem>
              </Menu>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            Navigation
          </Typography>
        </Toolbar>
        <Divider />
        <List>
          {navigationItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
          width: `calc(100% - ${drawerWidth}px)`,
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  )
}
