import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  Chip,
  Avatar,
  Paper,
  Divider,
  Alert,
  CircularProgress,
  Stack,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse
} from '@mui/material';
import {
  Send as SendIcon,
  Settings as SettingsIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Code as CodeIcon,
  Storage as StorageIcon,
  BugReport as TestIcon,
  History as HistoryIcon,
  Clear as ClearIcon,
  AttachFile as AttachFileIcon,
  InsertDriveFile as FileIcon,
  Image as ImageIcon,
  Description as DocumentIcon,
  TableChart as TableIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { mcpService } from '../../services/mcpService';
import { McpServer } from '../../types/mcp';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  content: string | ArrayBuffer;
  uploadedAt: Date;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'tool_call' | 'tool_result';
  content: string;
  timestamp: Date;
  files?: UploadedFile[];
  metadata?: {
    serverId?: string;
    toolName?: string;
    executionTime?: number;
    success?: boolean;
    error?: string;
  };
}

interface ChatSession {
  id: string;
  name: string;
  serverId: string;
  serverName: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

const ChatPage: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // State management
  const [selectedServer, setSelectedServer] = useState<McpServer | null>(null);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showServerList, setShowServerList] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

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

  const {
    data: discoveryResult,
    isLoading: discoveryLoading
  } = useQuery({
    queryKey: ['mcp-discovery', selectedServer?.id],
    queryFn: () => selectedServer ? mcpService.discoverCapabilities(selectedServer.id) : null,
    enabled: !!selectedServer,
    staleTime: 300000, // 5 minutes
  });

  // Mutations
  const sendMessageMutation = useMutation({
    mutationFn: async (): Promise<{ response: string; executionTime: number; success: boolean }> => {
      // Simulate MCP tool execution
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
      
      // Mock response based on message content
      const responses = [
        "I've processed your request successfully. Here are the results...",
        "The tool execution completed with the following output...",
        "I found the information you requested. Here's what I discovered...",
        "The operation was successful. Here are the details...",
        "I've analyzed the data and here are my findings..."
      ];
      
      return {
        response: responses[Math.floor(Math.random() * responses.length)],
        executionTime: Math.floor(Math.random() * 2000) + 500,
        success: Math.random() > 0.1 // 90% success rate
      };
    },
    onSuccess: (result) => {
      if (currentSession) {
        const newMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'assistant',
          content: result.response,
          timestamp: new Date(),
          metadata: {
            serverId: selectedServer?.id,
            executionTime: result.executionTime,
            success: result.success
          }
        };
        
        const updatedSession = {
          ...currentSession,
          messages: [...currentSession.messages, newMessage],
          updatedAt: new Date()
        };
        
        setCurrentSession(updatedSession);
        setIsTyping(false);
      }
    },
    onError: (error) => {
      if (currentSession) {
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'system',
          content: `Error: ${(error as Error).message}`,
          timestamp: new Date(),
          metadata: {
            serverId: selectedServer?.id,
            success: false,
            error: (error as Error).message
          }
        };
        
        const updatedSession = {
          ...currentSession,
          messages: [...currentSession.messages, errorMessage],
          updatedAt: new Date()
        };
        
        setCurrentSession(updatedSession);
        setIsTyping(false);
      }
    }
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages]);

  // Helper functions
  const handleServerSelect = (server: McpServer) => {
    setSelectedServer(server);
    setShowServerList(false);
    
    // Create new session for the selected server
    const newSession: ChatSession = {
      id: Date.now().toString(),
      name: `Chat with ${server.name}`,
      serverId: server.id,
      serverName: server.name,
      messages: [
        {
          id: '1',
          type: 'system',
          content: `Connected to ${server.name}. You can now test MCP capabilities through natural language.`,
          timestamp: new Date()
        }
      ],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    setCurrentSession(newSession);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    const newFiles: UploadedFile[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert(`File ${file.name} is too large. Maximum size is 10MB.`);
        continue;
      }

      // Validate file type
      const allowedTypes = [
        'text/csv',
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/plain',
        'application/json',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
      ];

      if (!allowedTypes.includes(file.type)) {
        alert(`File type ${file.type} is not supported.`);
        continue;
      }

      try {
        const content = await new Promise<string | ArrayBuffer>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result!);
          reader.onerror = reject;
          
          // For text files, read as text; for others, read as ArrayBuffer
          if (file.type.startsWith('text/') || file.type === 'application/json') {
            reader.readAsText(file);
          } else {
            reader.readAsArrayBuffer(file);
          }
        });

        const uploadedFile: UploadedFile = {
          id: Date.now().toString() + i,
          name: file.name,
          size: file.size,
          type: file.type,
          content,
          uploadedAt: new Date()
        };

        newFiles.push(uploadedFile);
      } catch (error) {
        console.error('Error reading file:', error);
        alert(`Error reading file ${file.name}`);
      }
    }

    setAttachedFiles(prev => [...prev, ...newFiles]);
    setIsUploading(false);
    
    // Clear the input
    event.target.value = '';
  };

  const removeFile = (fileId: string) => {
    setAttachedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handleSendMessage = () => {
    if ((!messageInput.trim() && attachedFiles.length === 0) || !currentSession || sendMessageMutation.isPending) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: messageInput.trim() || (attachedFiles.length > 0 ? `Uploaded ${attachedFiles.length} file(s)` : ''),
      timestamp: new Date(),
      files: attachedFiles.length > 0 ? [...attachedFiles] : undefined
    };

    const updatedSession = {
      ...currentSession,
      messages: [...currentSession.messages, userMessage],
      updatedAt: new Date()
    };

    setCurrentSession(updatedSession);
    setMessageInput('');
    setAttachedFiles([]);
    setIsTyping(true);

    // Send message to MCP server
    sendMessageMutation.mutate();
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const clearSession = () => {
    if (currentSession) {
      const clearedSession = {
        ...currentSession,
        messages: [
          {
            id: '1',
            type: 'system' as const,
            content: `Session cleared. You can continue testing ${currentSession.serverName} capabilities.`,
            timestamp: new Date()
          }
        ],
        updatedAt: new Date()
      };
      setCurrentSession(clearedSession);
    }
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user': return <PersonIcon />;
      case 'assistant': return <BotIcon />;
      case 'system': return <SettingsIcon />;
      case 'tool_call': return <TestIcon />;
      case 'tool_result': return <CodeIcon />;
      default: return <PersonIcon />;
    }
  };

  const getMessageColor = (type: string) => {
    switch (type) {
      case 'user': return 'primary';
      case 'assistant': return 'secondary';
      case 'system': return 'info';
      case 'tool_call': return 'warning';
      case 'tool_result': return 'success';
      default: return 'default';
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <ImageIcon />;
    if (fileType.includes('csv') || fileType.includes('excel') || fileType.includes('spreadsheet')) return <TableIcon />;
    if (fileType.includes('pdf') || fileType.includes('document') || fileType.includes('word')) return <DocumentIcon />;
    return <FileIcon />;
  };

  const getFileTypeColor = (fileType: string) => {
    if (fileType.startsWith('image/')) return 'success';
    if (fileType.includes('csv') || fileType.includes('excel')) return 'info';
    if (fileType.includes('pdf') || fileType.includes('document')) return 'warning';
    return 'default';
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" component="h1" gutterBottom>
              MCP Chat Testing Console
            </Typography>
            {selectedServer && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  icon={<StorageIcon />}
                  label={selectedServer.name}
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={selectedServer.health_status}
                  color={selectedServer.health_status === 'healthy' ? 'success' : 'error'}
                  size="small"
                />
              </Box>
            )}
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<StorageIcon />}
              onClick={() => setShowServerList(!showServerList)}
            >
              {selectedServer ? 'Change Server' : 'Select Server'}
            </Button>
            
            {currentSession && (
              <>
                <Button
                  variant="outlined"
                  startIcon={<HistoryIcon />}
                  onClick={() => setShowSessions(!showSessions)}
                >
                  Sessions
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={clearSession}
                  color="warning"
                >
                  Clear
                </Button>
              </>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Server Selection Panel */}
      <Collapse in={showServerList}>
        <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
          <Typography variant="h6" gutterBottom>
            Select MCP Server
          </Typography>
          {serversLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress />
            </Box>
          ) : serversError ? (
            <Alert severity="error">
              Failed to load servers: {(serversError as Error).message}
            </Alert>
          ) : (
            <List>
              {serversData?.servers?.map((server) => (
                <ListItem
                  key={server.id}
                  component="div"
                  onClick={() => handleServerSelect(server)}
                  sx={{ 
                    borderRadius: 1, 
                    mb: 1, 
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' }
                  }}
                >
                  <ListItemIcon>
                    <StorageIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={server.name}
                    secondary={server.base_url}
                  />
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                    <Chip
                      label={server.health_status}
                      color={server.health_status === 'healthy' ? 'success' : 'error'}
                      size="small"
                    />
                    <Chip
                      label={server.environment}
                      color="info"
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </ListItem>
              ))}
            </List>
          )}
        </Paper>
      </Collapse>

      {/* Main Chat Area */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Chat Messages */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {!selectedServer ? (
            <Box sx={{ 
              flex: 1, 
              display: 'flex', 
              flexDirection: 'column', 
              justifyContent: 'center', 
              alignItems: 'center',
              p: 4
            }}>
              <BotIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Select a Server to Start Testing
              </Typography>
              <Typography variant="body2" color="text.secondary" textAlign="center">
                Choose an MCP server from the list above to begin interactive testing of its capabilities
              </Typography>
            </Box>
          ) : (
            <>
              {/* Messages */}
              <Box sx={{ 
                flex: 1, 
                overflow: 'auto', 
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                gap: 2
              }}>
                {currentSession?.messages.map((message) => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                      mb: 2
                    }}
                  >
                    <Box sx={{ 
                      display: 'flex', 
                      alignItems: 'flex-start', 
                      gap: 1,
                      maxWidth: '70%',
                      flexDirection: message.type === 'user' ? 'row-reverse' : 'row'
                    }}>
                      <Avatar sx={{ 
                        bgcolor: `${getMessageColor(message.type)}.main`,
                        width: 32,
                        height: 32
                      }}>
                        {getMessageIcon(message.type)}
                      </Avatar>
                      
                      <Paper
                        elevation={1}
                        sx={{
                          p: 2,
                          bgcolor: message.type === 'user' ? 'primary.light' : 'background.paper',
                          color: message.type === 'user' ? 'primary.contrastText' : 'text.primary',
                          borderRadius: 2
                        }}
                      >
                        <Typography variant="body1" sx={{ mb: 1 }}>
                          {message.content}
                        </Typography>
                        
                        {/* Display attached files */}
                        {message.files && message.files.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                              Attached Files:
                            </Typography>
                            <Stack spacing={1}>
                              {message.files.map((file) => (
                                <Paper
                                  key={file.id}
                                  elevation={1}
                                  sx={{
                                    p: 1.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1,
                                    bgcolor: 'background.default'
                                  }}
                                >
                                  <Avatar
                                    sx={{
                                      bgcolor: `${getFileTypeColor(file.type)}.main`,
                                      width: 32,
                                      height: 32
                                    }}
                                  >
                                    {getFileIcon(file.type)}
                                  </Avatar>
                                  <Box sx={{ flex: 1, minWidth: 0 }}>
                                    <Typography variant="body2" noWrap>
                                      {file.name}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      {formatFileSize(file.size)} • {file.type}
                                    </Typography>
                                  </Box>
                                </Paper>
                              ))}
                            </Stack>
                          </Box>
                        )}
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" sx={{ opacity: 0.7 }}>
                            {formatTimestamp(message.timestamp)}
                          </Typography>
                          
                          {message.metadata?.executionTime && (
                            <Chip
                              label={`${message.metadata.executionTime}ms`}
                              size="small"
                              color={message.metadata.success ? 'success' : 'error'}
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Paper>
                    </Box>
                  </Box>
                ))}
                
                {isTyping && (
                  <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                        <BotIcon />
                      </Avatar>
                      <Paper elevation={1} sx={{ p: 2, borderRadius: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CircularProgress size={16} />
                          <Typography variant="body2" color="text.secondary">
                            Processing...
                          </Typography>
                        </Box>
                      </Paper>
                    </Box>
                  </Box>
                )}
                
                <div ref={messagesEndRef} />
              </Box>

              {/* Attached Files Preview */}
              {attachedFiles.length > 0 && (
                <Paper elevation={1} sx={{ p: 2, borderRadius: 0, bgcolor: 'background.default' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Attached Files ({attachedFiles.length})
                  </Typography>
                  <Stack spacing={1}>
                    {attachedFiles.map((file) => (
                      <Paper
                        key={file.id}
                        elevation={1}
                        sx={{
                          p: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          bgcolor: 'background.paper'
                        }}
                      >
                        <Avatar
                          sx={{
                            bgcolor: `${getFileTypeColor(file.type)}.main`,
                            width: 32,
                            height: 32
                          }}
                        >
                          {getFileIcon(file.type)}
                        </Avatar>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography variant="body2" noWrap>
                            {file.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatFileSize(file.size)} • {file.type}
                          </Typography>
                        </Box>
                        <IconButton
                          size="small"
                          onClick={() => removeFile(file.id)}
                          color="error"
                        >
                          <CloseIcon />
                        </IconButton>
                      </Paper>
                    ))}
                  </Stack>
                </Paper>
              )}

              {/* Message Input */}
              <Paper elevation={2} sx={{ p: 2, borderRadius: 0 }}>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                  <input
                    type="file"
                    multiple
                    accept=".csv,.pdf,.docx,.doc,.xlsx,.xls,.txt,.json,.jpg,.jpeg,.png,.gif,.webp"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    id="file-upload"
                    disabled={isUploading}
                  />
                  <label htmlFor="file-upload">
                    <IconButton
                      component="span"
                      disabled={isUploading || sendMessageMutation.isPending}
                      color="primary"
                    >
                      {isUploading ? (
                        <CircularProgress size={20} />
                      ) : (
                        <AttachFileIcon />
                      )}
                    </IconButton>
                  </label>
                  
                  <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    placeholder="Type your message to test MCP capabilities..."
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={sendMessageMutation.isPending}
                    variant="outlined"
                    size="small"
                  />
                  <Button
                    variant="contained"
                    onClick={handleSendMessage}
                    disabled={(!messageInput.trim() && attachedFiles.length === 0) || sendMessageMutation.isPending}
                    sx={{ minWidth: 'auto', px: 2 }}
                  >
                    {sendMessageMutation.isPending ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : (
                      <SendIcon />
                    )}
                  </Button>
                </Box>
                
                {/* File Upload Instructions */}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Supported formats: CSV, PDF, DOCX, XLSX, TXT, JSON, Images (JPG, PNG, GIF, WebP) • Max 10MB per file
                </Typography>
              </Paper>
            </>
          )}
        </Box>

        {/* Sidebar - Server Info & Capabilities */}
        {selectedServer && (
          <Paper elevation={1} sx={{ width: 300, p: 2, borderRadius: 0, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Server Information
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                {selectedServer.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedServer.description}
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip
                  label={`Health: ${selectedServer.health_status}`}
                  color={selectedServer.health_status === 'healthy' ? 'success' : 'error'}
                  size="small"
                />
                <Chip
                  label={`Environment: ${selectedServer.environment}`}
                  color="info"
                  size="small"
                  variant="outlined"
                />
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Available Capabilities
            </Typography>
            
            {discoveryLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                <CircularProgress size={20} />
              </Box>
            ) : discoveryResult ? (
              <Box>
                {Object.keys(discoveryResult.capabilities.tools || {}).length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Tools ({Object.keys(discoveryResult.capabilities.tools || {}).length})
                    </Typography>
                    <Stack spacing={1}>
                      {Object.entries(discoveryResult.capabilities.tools || {}).map(([name]) => (
                        <Chip
                          key={name}
                          icon={<TestIcon />}
                          label={name}
                          size="small"
                          variant="outlined"
                          sx={{ justifyContent: 'flex-start' }}
                        />
                      ))}
                    </Stack>
                  </Box>
                )}
                
                {Object.keys(discoveryResult.capabilities.resources || {}).length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Resources ({Object.keys(discoveryResult.capabilities.resources || {}).length})
                    </Typography>
                    <Stack spacing={1}>
                      {Object.entries(discoveryResult.capabilities.resources || {}).map(([name]) => (
                        <Chip
                          key={name}
                          icon={<StorageIcon />}
                          label={name}
                          size="small"
                          variant="outlined"
                          sx={{ justifyContent: 'flex-start' }}
                        />
                      ))}
                    </Stack>
                  </Box>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No capabilities discovered yet
              </Typography>
            )}
          </Paper>
        )}
      </Box>
    </Box>
  );
};

export default ChatPage;