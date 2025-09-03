# SprintConnect Frontend

## Overview

The SprintConnect frontend is a modern React application that provides an intuitive interface for managing MCP servers, testing capabilities, and monitoring utilization. Built with TypeScript and designed for enterprise use, it emphasizes accessibility, security, and user experience.

## Key Features

### MCP Server Management
- **Server Registry Interface**: Comprehensive CRUD operations for MCP server registration
- **Capability Discovery**: Visual representation of server capabilities and schemas
- **Health Monitoring**: Real-time status indicators and health check results
- **Environment Management**: Switch between dev, staging, and production environments

### Discovery & Search
- **Advanced Filtering**: Search servers by capability, tags, environment, and metadata
- **LangGraph Agent Preview**: UI for testing discovery API queries
- **Capability Browser**: Explore available tools and their documentation
- **Policy Visualization**: Understand access controls and permissions

### Chat Testing Console
- **Multi-Server Selection**: Choose multiple MCP servers for testing workflows
- **Real-Time Streaming**: WebSocket-based chat with token-level streaming
- **Tool Call Visualization**: Track LLM tool calls and responses in real-time
- **Session Management**: Save, export, and replay chat sessions
- **Usage Analytics**: Monitor token consumption and costs per session

### Administration & Analytics
- **User Management**: Org-level user administration with role assignment
- **Utilization Dashboards**: Interactive charts and metrics visualization
- **Audit Log Browser**: Search and export security audit trails
- **Webhook Configuration**: Manage external integrations and notifications

## Technology Stack

### Core Framework
- **React 18** with concurrent features and Suspense
- **TypeScript** with strict type checking
- **Vite** as build tool with SWC for fast compilation
- **React Router** for client-side routing and navigation

### UI & Styling
- **Component Library**: Material-UI, Ant Design, or Chakra UI (TBD)
- **Styling**: CSS Modules or styled-components for component isolation
- **Icons**: React Icons or Heroicons for consistent iconography
- **Charts**: Recharts or Chart.js for data visualization

### State Management
- **Zustand** or **Redux Toolkit** for global state management
- **React Query/TanStack Query** for server state and caching
- **React Hook Form** for form state and validation
- **Zod** for runtime type validation and schema parsing

### Authentication & Security
- **OIDC Client** with PKCE flow for secure authentication
- **API Key Management** with secure storage patterns
- **Role-Based UI**: Conditional rendering based on user permissions
- **CSP Headers**: Content Security Policy enforcement

### Real-Time Communication
- **WebSocket Client** for chat streaming and live updates
- **Server-Sent Events** for notifications and status updates
- **Optimistic Updates** for responsive user interactions
- **Connection Management**: Auto-reconnection and error handling

### Development Tools
- **ESLint** with TypeScript and React rules
- **Prettier** for code formatting
- **Husky** for git hooks and pre-commit validation
- **Jest** and **React Testing Library** for unit testing
- **Playwright** for end-to-end testing

## Application Architecture

### Component Structure
```
src/
├── components/           # Reusable UI components
│   ├── common/          # Generic components (Button, Modal, etc.)
│   ├── forms/           # Form components with validation
│   ├── charts/          # Data visualization components
│   └── layout/          # Layout and navigation components
├── pages/               # Route-level page components
│   ├── auth/           # Authentication pages
│   ├── registry/       # MCP server management
│   ├── discovery/      # Discovery and search
│   ├── chat/           # Testing console
│   ├── analytics/      # Dashboards and metrics
│   └── admin/          # Administration pages
├── hooks/               # Custom React hooks
├── services/           # API clients and external services
├── stores/             # State management (Zustand/Redux)
├── types/              # TypeScript type definitions
├── utils/              # Utility functions and helpers
└── styles/             # Global styles and themes
```

### State Management
- **Authentication State**: User profile, tokens, permissions
- **Registry State**: MCP servers, capabilities, health status
- **Chat State**: Active sessions, message history, streaming state
- **UI State**: Modals, notifications, loading states, theme preferences

### Routing Strategy
```typescript
// Route structure
/                          # Dashboard/Landing
/auth/login               # OIDC authentication
/auth/callback           # OIDC callback handler
/registry                # MCP server list
/registry/new            # Register new server
/registry/:id            # Server detail view
/registry/:id/edit       # Edit server configuration
/discovery               # Discovery search interface
/chat                    # Chat session list
/chat/new                # Create new session
/chat/:id                # Active chat session
/analytics               # Utilization dashboards
/analytics/costs         # Cost attribution reports
/admin/users             # User management
/admin/audit             # Audit log browser
/admin/webhooks          # Webhook configuration
/settings                # User preferences
```

## Key User Interfaces

### Dashboard
- **Overview Cards**: Quick stats on servers, capabilities, usage
- **Recent Activity**: Latest chat sessions and server registrations
- **Health Status**: System-wide health indicators and alerts
- **Quick Actions**: Shortcuts to common tasks

### MCP Server Registry
- **Server List**: Filterable table with health status and metadata
- **Server Detail**: Comprehensive view with capabilities and metrics
- **Registration Form**: Multi-step wizard for server onboarding
- **Capability Explorer**: Interactive browser for discovered tools

### Discovery Interface
- **Search Builder**: Visual query builder for capability searches
- **Results Grid**: Card-based layout with server previews
- **Filter Sidebar**: Faceted search with tag clouds and ranges
- **API Playground**: Test discovery API queries interactively

### Chat Testing Console
- **Server Selection**: Multi-select with capability preview
- **Chat Interface**: Modern chat UI with streaming support
- **Tool Call Timeline**: Visual representation of LLM tool usage
- **Session Management**: Save, load, and export conversations
- **Debug Panel**: Detailed view of requests/responses and timing

### Analytics Dashboard
- **Usage Charts**: Time-series charts for various metrics
- **Top Lists**: Most used servers, capabilities, and users
- **Cost Attribution**: Token usage and cost breakdown
- **Export Tools**: CSV/JSON export with custom date ranges

## Authentication & Authorization

### OIDC Integration
```typescript
// OIDC configuration
const oidcConfig = {
  authority: process.env.REACT_APP_OIDC_AUTHORITY,
  client_id: process.env.REACT_APP_OIDC_CLIENT_ID,
  redirect_uri: `${window.location.origin}/auth/callback`,
  response_type: 'code',
  scope: 'openid profile email',
  post_logout_redirect_uri: window.location.origin,
  automaticSilentRenew: true,
  includeIdTokenInSilentRenew: true,
  loadUserInfo: true
};
```

### Role-Based UI Rendering
```typescript
// Permission-based component rendering
const CanAccess = ({ permission, children }) => {
  const { hasPermission } = useAuth();
  return hasPermission(permission) ? children : null;
};

// Usage in components
<CanAccess permission="mcp:servers:delete">
  <DeleteButton onDelete={handleDelete} />
</CanAccess>
```

### API Key Management
- **Secure Storage**: No sensitive data in localStorage
- **Memory-based**: Store in React state with refresh token flow
- **Automatic Refresh**: Handle token expiration transparently
- **Logout Cleanup**: Clear all auth state on logout

## Real-Time Features

### WebSocket Integration
```typescript
// Chat streaming implementation
const useChatStream = (sessionId: string) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/chat/sessions/${sessionId}/stream`);
    
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleStreamingMessage(data);
    };
    ws.onclose = () => setIsConnected(false);
    
    return () => ws.close();
  }, [sessionId]);
  
  return { messages, isConnected, sendMessage };
};
```

### Live Updates
- **Health Status**: Real-time server health indicators
- **Usage Metrics**: Live charts with WebSocket or SSE updates
- **Notifications**: Toast messages for system events
- **Presence Indicators**: Show other users in shared sessions

## Performance Optimization

### Code Splitting
```typescript
// Route-based code splitting
const Registry = lazy(() => import('./pages/registry/Registry'));
const Chat = lazy(() => import('./pages/chat/Chat'));
const Analytics = lazy(() => import('./pages/analytics/Analytics'));

// Component-based splitting for large components
const HeavyChart = lazy(() => import('./components/charts/HeavyChart'));
```

### Caching Strategy
- **React Query**: Server state caching with background updates
- **Service Worker**: Cache static assets and API responses
- **Memoization**: React.memo and useMemo for expensive calculations
- **Virtual Scrolling**: For large lists and tables

### Bundle Optimization
- **Tree Shaking**: Eliminate unused code from bundles
- **Dynamic Imports**: Load components and libraries on demand
- **Asset Optimization**: Image compression and format selection
- **CDN Integration**: Serve static assets from CDN

## Testing Strategy

### Unit Testing
```typescript
// Component testing with React Testing Library
describe('ServerCard', () => {
  it('renders server information correctly', () => {
    const server = mockMcpServer();
    render(<ServerCard server={server} />);
    
    expect(screen.getByText(server.name)).toBeInTheDocument();
    expect(screen.getByText(server.environment)).toBeInTheDocument();
  });
  
  it('handles health status updates', async () => {
    const server = mockMcpServer({ status: 'unhealthy' });
    render(<ServerCard server={server} />);
    
    expect(screen.getByTestId('health-indicator')).toHaveClass('status-unhealthy');
  });
});
```

### Integration Testing
- **API Integration**: Mock backend responses with MSW
- **WebSocket Testing**: Mock WebSocket connections
- **Authentication Flow**: Test OIDC login and logout
- **State Management**: Test complex state interactions

### E2E Testing
```typescript
// Playwright test example
test('complete chat session workflow', async ({ page }) => {
  await page.goto('/chat/new');
  
  // Select MCP servers
  await page.click('[data-testid="server-selector"]');
  await page.check('[data-testid="server-checkbox-1"]');
  await page.check('[data-testid="server-checkbox-2"]');
  
  // Start chat session
  await page.click('[data-testid="start-session"]');
  
  // Send message and verify response
  await page.fill('[data-testid="chat-input"]', 'Hello, test message');
  await page.click('[data-testid="send-button"]');
  
  await expect(page.locator('[data-testid="chat-message"]')).toBeVisible();
});
```

## Development Workflow

### Environment Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run E2E tests
npm run test:e2e

# Lint and format
npm run lint
npm run format

# Type checking
npm run type-check

# Build for production
npm run build
```

### Environment Variables
```bash
# Authentication
REACT_APP_OIDC_AUTHORITY=https://auth.example.com
REACT_APP_OIDC_CLIENT_ID=sprintconnect-frontend

# API Configuration
REACT_APP_API_BASE_URL=https://api.sprintconnect.com
REACT_APP_WS_BASE_URL=wss://api.sprintconnect.com

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_WEBHOOKS=true
REACT_APP_DEBUG_MODE=false

# Monitoring
REACT_APP_SENTRY_DSN=https://your-sentry-dsn
REACT_APP_ANALYTICS_ID=GA-XXXXXXXX-X
```

### Build Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@mui/material', '@emotion/react'],
          charts: ['recharts', 'chart.js']
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
```

## Accessibility

### WCAG Compliance
- **Keyboard Navigation**: Full keyboard accessibility for all interactions
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Color Contrast**: WCAG AA compliant color schemes
- **Focus Management**: Logical focus order and visible focus indicators

### Implementation
```typescript
// Accessible component example
const AccessibleButton = ({ children, onClick, ...props }) => {
  return (
    <button
      onClick={onClick}
      aria-describedby={props['aria-describedby']}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick();
        }
      }}
      {...props}
    >
      {children}
    </button>
  );
};
```

## Security Considerations

### Content Security Policy
```typescript
// CSP configuration
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://trusted-scripts.com;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  img-src 'self' data: https:;
  connect-src 'self' ${API_BASE_URL} ${WS_BASE_URL};
  font-src 'self' https://fonts.gstatic.com;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
`;
```

### XSS Prevention
- **Input Sanitization**: Sanitize all user inputs and outputs
- **Trusted Types**: Use Trusted Types API where supported
- **Safe innerHTML**: Use DOMPurify for any dynamic HTML content
- **Template Security**: Validate template strings and JSX props

### CSRF Protection
- **SameSite Cookies**: Use SameSite=Strict for session cookies
- **CSRF Tokens**: Include CSRF tokens in state-changing requests
- **Origin Validation**: Verify Origin and Referer headers

## Deployment & Production

### Build Optimization
```bash
# Production build with optimization
npm run build

# Analyze bundle size
npm run analyze

# Docker build
docker build -t sprintconnect-frontend .
```

### Static Hosting
- **CDN Distribution**: Serve assets from global CDN
- **Gzip/Brotli**: Enable compression for text assets
- **Cache Headers**: Set appropriate cache headers for assets
- **Health Checks**: Include health check endpoint for load balancers

### Monitoring & Analytics
- **Error Tracking**: Sentry for error monitoring and alerting
- **Performance Monitoring**: Web Vitals and custom metrics
- **User Analytics**: Privacy-compliant usage analytics
- **A/B Testing**: Feature flag integration for gradual rollouts

## Future Enhancements

### Planned Features
- **Progressive Web App**: Offline capability and installability
- **Real-Time Collaboration**: Multi-user chat sessions
- **Advanced Visualizations**: 3D network graphs for server relationships
- **Mobile Responsive**: Optimized mobile experience
- **Dark Mode**: User preference for dark/light themes

### Technical Improvements
- **Micro-Frontend Architecture**: Split into smaller deployable units
- **Server-Side Rendering**: Next.js migration for SEO and performance
- **Advanced State Management**: Consider Recoil or Jotai for complex state
- **GraphQL Integration**: Migrate from REST to GraphQL for flexible queries

## Contributing

### Code Standards
- Follow TypeScript strict mode guidelines
- Use functional components with hooks
- Implement proper error boundaries
- Write comprehensive tests for all features
- Document complex logic with JSDoc comments

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Run linting and type checking
4. Update documentation if needed
5. Submit PR with detailed description
6. Address review feedback
7. Merge after approval and CI success
