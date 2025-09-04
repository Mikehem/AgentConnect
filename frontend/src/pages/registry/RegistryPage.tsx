import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
  Alert,
  CircularProgress,
  Stack,
  Paper,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  CloudOff as CloudOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpService } from '../../services/mcpService';
import { McpServer, McpServerCreate, McpServerListParams } from '../../types/mcp';

const RegistryPage: React.FC = () => {
  const queryClient = useQueryClient();
  
  // State management
  const [filters, setFilters] = useState<McpServerListParams>({
    limit: 50,
    offset: 0
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedServer, setSelectedServer] = useState<McpServer | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [serverToDelete, setServerToDelete] = useState<McpServer | null>(null);

  // Form state
  const [formData, setFormData] = useState<McpServerCreate>({
    name: '',
    description: '',
    base_url: '',
    environment: 'development',
    tags: []
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Queries
  const {
    data: serversData,
    isLoading,
    error
  } = useQuery({
    queryKey: ['mcp-servers', filters],
    queryFn: () => mcpService.listServers(filters),
    staleTime: 30000, // 30 seconds
  });

  // Mutations
  const createServerMutation = useMutation({
    mutationFn: mcpService.createServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setCreateDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      setFormErrors({ general: error.message });
    }
  });

  const updateServerMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => mcpService.updateServer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setEditDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      setFormErrors({ general: error.message });
    }
  });

  const deleteServerMutation = useMutation({
    mutationFn: mcpService.deleteServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setDeleteDialogOpen(false);
      setServerToDelete(null);
    }
  });

  // Helper functions
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      base_url: '',
      environment: 'development',
      tags: []
    });
    setFormErrors({});
  };

  const handleCreateServer = () => {
    setFormErrors({});
    createServerMutation.mutate(formData);
  };

  const handleUpdateServer = () => {
    if (!selectedServer) return;
    setFormErrors({});
    updateServerMutation.mutate({
      id: selectedServer.id,
      data: formData
    });
  };

  const handleDeleteServer = () => {
    if (!serverToDelete) return;
    deleteServerMutation.mutate(serverToDelete.id);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, server: McpServer) => {
    setAnchorEl(event.currentTarget);
    setSelectedServer(server);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedServer(null);
  };

  const handleEditClick = () => {
    if (selectedServer) {
      setFormData({
        name: selectedServer.name,
        description: selectedServer.description,
        base_url: selectedServer.base_url,
        environment: selectedServer.environment,
        tags: selectedServer.tags
      });
      setEditDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleDeleteClick = () => {
    setServerToDelete(selectedServer);
    setDeleteDialogOpen(true);
    handleMenuClose();
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
      default: return <CloudOffIcon />;
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
            MCP Server Registry
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage and monitor your Model Context Protocol servers
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ minWidth: 150 }}
        >
          Add Server
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid sx={{ xs: 12, md: 6 }}>
            <TextField
              fullWidth
              placeholder="Search servers by name, description, or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          <Grid sx={{ xs: 12, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Environment</InputLabel>
              <Select
                value={filters.environment || ''}
                onChange={(e) => setFilters({ ...filters, environment: e.target.value as any })}
                input={<OutlinedInput label="Environment" />}
              >
                <MenuItem value="">All Environments</MenuItem>
                <MenuItem value="development">Development</MenuItem>
                <MenuItem value="staging">Staging</MenuItem>
                <MenuItem value="production">Production</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid sx={{ xs: 12, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Health Status</InputLabel>
              <Select
                value={filters.health_status || ''}
                onChange={(e) => setFilters({ ...filters, health_status: e.target.value as any })}
                input={<OutlinedInput label="Health Status" />}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="healthy">Healthy</MenuItem>
                <MenuItem value="unhealthy">Unhealthy</MenuItem>
                <MenuItem value="degraded">Degraded</MenuItem>
                <MenuItem value="unknown">Unknown</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load servers: {(error as Error).message}
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Servers Grid */}
      {!isLoading && (
        <Grid container spacing={3}>
          {filteredServers.map((server) => (
            <Grid sx={{ xs: 12, sm: 6, lg: 4 }} key={server.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Server Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="h6" component="h3" noWrap>
                        {server.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {server.base_url}
                      </Typography>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, server)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </Box>

                  {/* Description */}
                  <Typography variant="body2" sx={{ mb: 2, minHeight: 40 }}>
                    {server.description || 'No description provided'}
                  </Typography>

                  {/* Status and Environment */}
                  <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    <Chip
                      icon={getHealthStatusIcon(server.health_status)}
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

                  {/* Tags */}
                  {server.tags.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                        {server.tags.slice(0, 3).map((tag) => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            variant="outlined"
                            sx={{ mb: 0.5 }}
                          />
                        ))}
                        {server.tags.length > 3 && (
                          <Chip
                            label={`+${server.tags.length - 3}`}
                            size="small"
                            variant="outlined"
                            sx={{ mb: 0.5 }}
                          />
                        )}
                      </Stack>
                    </Box>
                  )}

                  {/* Metadata */}
                  <Box sx={{ mt: 'auto' }}>
                    <Divider sx={{ mb: 1 }} />
                    <Typography variant="caption" color="text.secondary">
                      Created: {new Date(server.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Empty State */}
      {!isLoading && filteredServers.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <CloudOffIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No servers found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchTerm ? 'Try adjusting your search criteria' : 'Get started by adding your first MCP server'}
          </Typography>
          {!searchTerm && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Add Your First Server
            </Button>
          )}
        </Box>
      )}

      {/* Create Server Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New MCP Server</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Server Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              error={!!formErrors.name}
              helperText={formErrors.name}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={3}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Base URL"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              error={!!formErrors.base_url}
              helperText={formErrors.base_url || 'e.g., https://mcp.example.com'}
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Environment</InputLabel>
              <Select
                value={formData.environment}
                onChange={(e) => setFormData({ ...formData, environment: e.target.value as any })}
                input={<OutlinedInput label="Environment" />}
              >
                <MenuItem value="development">Development</MenuItem>
                <MenuItem value="staging">Staging</MenuItem>
                <MenuItem value="production">Production</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Tags (comma-separated)"
              value={formData.tags.join(', ')}
              onChange={(e) => setFormData({ 
                ...formData, 
                tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
              })}
              helperText="e.g., filesystem, utilities, database"
              sx={{ mb: 2 }}
            />
            {formErrors.general && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formErrors.general}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateServer}
            variant="contained"
            disabled={createServerMutation.isPending}
          >
            {createServerMutation.isPending ? 'Creating...' : 'Create Server'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Server Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit MCP Server</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Server Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              error={!!formErrors.name}
              helperText={formErrors.name}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={3}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Tags (comma-separated)"
              value={formData.tags.join(', ')}
              onChange={(e) => setFormData({ 
                ...formData, 
                tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
              })}
              helperText="e.g., filesystem, utilities, database"
              sx={{ mb: 2 }}
            />
            {formErrors.general && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formErrors.general}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpdateServer}
            variant="contained"
            disabled={updateServerMutation.isPending}
          >
            {updateServerMutation.isPending ? 'Updating...' : 'Update Server'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete MCP Server</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{serverToDelete?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteServer}
            color="error"
            variant="contained"
            disabled={deleteServerMutation.isPending}
          >
            {deleteServerMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEditClick}>
          <EditIcon sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default RegistryPage;
