import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Stack,
  Paper,
  Tabs,
  Tab,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { mcpService } from '../../services/mcpService';
import { McpServer, McpCapabilityDiscovery } from '../../types/mcp';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`discovery-tabpanel-${index}`}
      aria-labelledby={`discovery-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const DiscoveryPage: React.FC = () => {
  const [selectedServer, setSelectedServer] = useState<McpServer | null>(null);
  const [discoveryResult, setDiscoveryResult] = useState<McpCapabilityDiscovery | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  // Queries
  const {
    data: serversData,
    isLoading: serversLoading,
    error: serversError
  } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => mcpService.listServers({ limit: 100 }),
    staleTime: 30000,
  });

  // Mutations
  const discoverCapabilitiesMutation = useMutation({
    mutationFn: (serverId: string) => mcpService.discoverCapabilities(serverId),
    onSuccess: (result) => {
      setDiscoveryResult(result);
      setTabValue(1); // Switch to capabilities tab
    },
    onError: (error) => {
      console.error('Discovery failed:', error);
    }
  });

  // Helper functions
  const handleServerSelect = (server: McpServer) => {
    setSelectedServer(server);
    setDiscoveryResult(null);
    setTabValue(0);
  };

  const handleDiscoverCapabilities = () => {
    if (selectedServer) {
      discoverCapabilitiesMutation.mutate(selectedServer.id);
    }
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'unhealthy': return 'error';
      case 'degraded': return 'warning';
      default: return 'default';
    }
  };

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon />;
      case 'unhealthy': return <ErrorIcon />;
      case 'degraded': return <WarningIcon />;
      default: return <InfoIcon />;
    }
  };

  const getEnvironmentColor = (env: string) => {
    switch (env) {
      case 'production': return 'error';
      case 'staging': return 'warning';
      case 'development': return 'info';
      default: return 'default';
    }
  };

  // Filter servers based on search term
  const filteredServers = serversData?.servers?.filter(server =>
    server.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    server.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    server.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            MCP Server Discovery
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Discover and test capabilities of your MCP servers
          </Typography>
        </Box>
        {selectedServer && (
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={handleDiscoverCapabilities}
            disabled={discoverCapabilitiesMutation.isPending}
            sx={{ minWidth: 200 }}
          >
            {discoverCapabilitiesMutation.isPending ? 'Discovering...' : 'Discover Capabilities'}
          </Button>
        )}
      </Box>

      {/* Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search servers by name, description, or tags..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
        />
      </Paper>

      {/* Error Display */}
      {serversError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load servers: {(serversError as Error).message}
        </Alert>
      )}

      {/* Loading State */}
      {serversLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Main Content */}
      {!serversLoading && (
        <Grid container spacing={3}>
          {/* Server Selection */}
          <Grid sx={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Select Server
                </Typography>
                <List>
                  {filteredServers.map((server) => (
                    <ListItem
                      key={server.id}
                      onClick={() => handleServerSelect(server)}
                      sx={{ 
                        mb: 1, 
                        borderRadius: 1, 
                        cursor: 'pointer',
                        backgroundColor: selectedServer?.id === server.id ? 'action.selected' : 'transparent'
                      }}
                    >
                      <ListItemIcon>
                        {getHealthStatusIcon(server.health_status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={server.name}
                        secondary={server.base_url}
                      />
                      <Box sx={{ mt: 0.5 }}>
                        <Stack direction="row" spacing={1}>
                          <Chip
                            label={server.health_status}
                            color={getHealthStatusColor(server.health_status) as any}
                            size="small"
                          />
                          <Chip
                            label={server.environment}
                            color={getEnvironmentColor(server.environment) as any}
                            size="small"
                            variant="outlined"
                          />
                        </Stack>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Discovery Results */}
          <Grid sx={{ xs: 12, md: 8 }}>
            {selectedServer ? (
              <Card>
                <CardContent>
                  <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                      <Tab label="Server Info" />
                      <Tab 
                        label={
                          <Badge badgeContent={discoveryResult ? Object.keys(discoveryResult.capabilities.tools || {}).length : 0} color="primary">
                            Capabilities
                          </Badge>
                        } 
                      />
                      <Tab 
                        label={
                          <Badge badgeContent={discoveryResult ? Object.keys(discoveryResult.capabilities.resources || {}).length : 0} color="secondary">
                            Resources
                          </Badge>
                        } 
                      />
                    </Tabs>
                  </Box>

                  <TabPanel value={tabValue} index={0}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        {selectedServer.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {selectedServer.description}
                      </Typography>
                      
                      <Grid container spacing={2}>
                        <Grid sx={{ xs: 6 }}>
                          <Typography variant="subtitle2">Base URL</Typography>
                          <Typography variant="body2">{selectedServer.base_url}</Typography>
                        </Grid>
                        <Grid sx={{ xs: 6 }}>
                          <Typography variant="subtitle2">Environment</Typography>
                          <Chip
                            label={selectedServer.environment}
                            color={getEnvironmentColor(selectedServer.environment) as any}
                            size="small"
                          />
                        </Grid>
                        <Grid sx={{ xs: 6 }}>
                          <Typography variant="subtitle2">Health Status</Typography>
                          <Chip
                            icon={getHealthStatusIcon(selectedServer.health_status)}
                            label={selectedServer.health_status}
                            color={getHealthStatusColor(selectedServer.health_status) as any}
                            size="small"
                          />
                        </Grid>
                        <Grid sx={{ xs: 6 }}>
                          <Typography variant="subtitle2">Created</Typography>
                          <Typography variant="body2">
                            {new Date(selectedServer.created_at).toLocaleDateString()}
                          </Typography>
                        </Grid>
                      </Grid>

                      {selectedServer.tags.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Tags</Typography>
                          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                            {selectedServer.tags.map((tag) => (
                              <Chip key={tag} label={tag} size="small" variant="outlined" />
                            ))}
                          </Stack>
                        </Box>
                      )}
                    </Box>
                  </TabPanel>

                  <TabPanel value={tabValue} index={1}>
                    {discoverCapabilitiesMutation.isPending ? (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <CircularProgress />
                        <Typography variant="body2" sx={{ mt: 2 }}>
                          Discovering capabilities...
                        </Typography>
                      </Box>
                    ) : discoveryResult ? (
                      <Box>
                        {discoveryResult.errors.length > 0 && (
                          <Alert severity="warning" sx={{ mb: 2 }}>
                            Discovery completed with warnings: {discoveryResult.errors.join(', ')}
                          </Alert>
                        )}
                        
                        {Object.keys(discoveryResult.capabilities.tools || {}).length > 0 ? (
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              Available Tools ({Object.keys(discoveryResult.capabilities.tools || {}).length})
                            </Typography>
                            {Object.entries(discoveryResult.capabilities.tools || {}).map(([name, tool]) => (
                              <Card key={name} sx={{ mb: 2 }}>
                                <CardContent>
                                  <Typography variant="subtitle1" gutterBottom>
                                    {name}
                                  </Typography>
                                  <Typography variant="body2" paragraph>
                                    {tool.description}
                                  </Typography>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Input Schema:
                                  </Typography>
                                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                                    <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                                      {JSON.stringify(tool.inputSchema, null, 2)}
                                    </pre>
                                  </Paper>
                                </CardContent>
                              </Card>
                            ))}
                          </Box>
                        ) : (
                          <Alert severity="info">
                            No tools discovered for this server.
                          </Alert>
                        )}
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          Ready to Discover
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Click "Discover Capabilities" to explore this server's tools
                        </Typography>
                      </Box>
                    )}
                  </TabPanel>

                  <TabPanel value={tabValue} index={2}>
                    {discoverCapabilitiesMutation.isPending ? (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <CircularProgress />
                        <Typography variant="body2" sx={{ mt: 2 }}>
                          Discovering resources...
                        </Typography>
                      </Box>
                    ) : discoveryResult ? (
                      <Box>
                        {Object.keys(discoveryResult.capabilities.resources || {}).length > 0 ? (
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              Available Resources ({Object.keys(discoveryResult.capabilities.resources || {}).length})
                            </Typography>
                            {Object.entries(discoveryResult.capabilities.resources || {}).map(([name, resource]) => (
                              <Card key={name} sx={{ mb: 2 }}>
                                <CardContent>
                                  <Typography variant="subtitle1" gutterBottom>
                                    {name}
                                  </Typography>
                                  <Typography variant="body2" paragraph>
                                    {resource.description}
                                  </Typography>
                                  <Typography variant="subtitle2" gutterBottom>
                                    URI Template:
                                  </Typography>
                                  <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                                    <Typography variant="body2" fontFamily="monospace">
                                      {resource.uriTemplate}
                                    </Typography>
                                  </Paper>
                                </CardContent>
                              </Card>
                            ))}
                          </Box>
                        ) : (
                          <Alert severity="info">
                            No resources discovered for this server.
                          </Alert>
                        )}
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          Ready to Discover
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Click "Discover Capabilities" to explore this server's resources
                        </Typography>
                      </Box>
                    )}
                  </TabPanel>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent>
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      Select a Server
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Choose a server from the list to discover its capabilities
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default DiscoveryPage;