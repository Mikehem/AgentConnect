# SprintConnect Security Architecture

## Overview

SprintConnect implements a comprehensive security framework designed for enterprise environments with stringent security and compliance requirements. The architecture follows defense-in-depth principles, zero-trust networking, and industry best practices for cloud-native applications.

## Ecosystem Security Responsibilities

- AuthGateway: OAuth 2.1 enforcement, JWT/JWKS verification, DPoP/mTLS token binding, context propagation
- API Service: Input validation (Pydantic v2), problem+json errors, org isolation checks, audit event emission
- PDP: Policy evaluation per capability/tool, tenant policy versions, obligation handling (redaction/limits)
- Workers (Discovery/Health): Least-privilege credential access via Vault, signed-manifest verification, egress via proxy
- Egress Proxy: DNS pinning, allowlists, SSRF prevention, per-tenant rate limits and logging
- Frontend: PKCE-only flows, SameSite=strict, CSRF tokens, capability-aware UX to minimize privilege
- Data Tier: Encrypted at rest, tenant-partitioned access, audit integrity (hash chaining)

## Security Principles

### Zero Trust Architecture
- **Never Trust, Always Verify**: No implicit trust between services, users, or networks
- **Least Privilege Access**: Minimal permissions granted by default with explicit escalation
- **Continuous Verification**: Ongoing validation of user and service identity
- **Assume Breach**: Design systems to contain and minimize impact of security incidents

### Defense in Depth
- **Multiple Security Layers**: Network, application, data, and identity controls
- **Redundant Protections**: Overlapping security controls to prevent single points of failure
- **Progressive Hardening**: Security controls increase as access approaches sensitive resources
- **Fail Secure**: Systems default to secure state when security controls fail

### Security by Design
- **Secure Defaults**: Systems ship with secure configuration out of the box
- **Privacy by Design**: Data protection and privacy controls built into system architecture
- **Compliance Ready**: SOC2, GDPR, and other regulatory requirements addressed in design
- **Threat Modeling**: Regular assessment of threats and security controls

## Identity and Access Management

### Authentication

#### OpenID Connect (OIDC) Integration
```yaml
# OIDC Configuration
oidc:
  provider: "https://auth.sprintconnect.com"
  client_id: "sprintconnect-frontend"
  response_type: "code"
  scope: "openid profile email"
  redirect_uri: "https://app.sprintconnect.com/auth/callback"
  
  # PKCE Configuration
  code_challenge_method: "S256"
  code_challenge_length: 128
  
  # Token Configuration
  access_token_lifetime: 3600  # 1 hour
  refresh_token_lifetime: 86400  # 24 hours
  id_token_lifetime: 3600  # 1 hour
  
  # Security Features
  require_https: true
  validate_issuer: true
  validate_audience: true
  clock_skew_tolerance: 300  # 5 minutes
```

#### API Key Management
```python
# API Key Security Model
class ApiKeyConfig:
    # Encryption
    encryption_algorithm = "AES-256-GCM"
    key_derivation = "PBKDF2-SHA256"
    salt_length = 32
    iterations = 100000
    
    # Access Control
    scoped_permissions = True
    role_based_scoping = True
    time_based_expiration = True
    
    # Monitoring
    usage_tracking = True
    anomaly_detection = True
    automatic_rotation = True
    
    # Storage
    hash_algorithm = "SHA-256"
    store_hash_only = True  # Never store plaintext
    secure_comparison = True  # Constant-time comparison
```

#### Multi-Factor Authentication (MFA)
- **TOTP Support**: Time-based One-Time Password (RFC 6238)
- **WebAuthn Integration**: Hardware security keys and biometric authentication
- **SMS/Email Backup**: Secondary factor for account recovery
- **Enterprise SSO**: Integration with enterprise MFA providers

### Authorization

#### Role-Based Access Control (RBAC)
```yaml
# RBAC Schema
roles:
  super_admin:
    description: "Full system administration access"
    permissions:
      - "system:*"
      - "org:*:*"
      - "audit:*"
    
  org_admin:
    description: "Organization administration"
    permissions:
      - "org:{org_id}:*"
      - "users:{org_id}:*"
      - "mcp:{org_id}:*"
      - "audit:{org_id}:read"
    
  mcp_engineer:
    description: "MCP server management"
    permissions:
      - "mcp:{org_id}:servers:*"
      - "mcp:{org_id}:capabilities:read"
      - "chat:{org_id}:sessions:*"
      - "metrics:{org_id}:read"
    
  mcp_viewer:
    description: "Read-only access to MCP resources"
    permissions:
      - "mcp:{org_id}:servers:read"
      - "mcp:{org_id}:capabilities:read"
      - "chat:{org_id}:sessions:read"
      - "metrics:{org_id}:read"
    
  chat_user:
    description: "Chat testing access only"
    permissions:
      - "mcp:{org_id}:servers:read"
      - "chat:{org_id}:sessions:create"
      - "chat:{org_id}:sessions:own:*"
```

#### Attribute-Based Access Control (ABAC)
```python
# Policy Engine Configuration
class PolicyEngine:
    def evaluate_access(self, subject, resource, action, context):
        """
        Evaluate access based on multiple attributes
        """
        policy = {
            "subject": {
                "user_id": subject.user_id,
                "org_id": subject.org_id,
                "roles": subject.roles,
                "clearance_level": subject.clearance_level
            },
            "resource": {
                "type": resource.type,
                "id": resource.id,
                "org_id": resource.org_id,
                "environment": resource.environment,
                "classification": resource.classification
            },
            "action": action,
            "context": {
                "time": context.timestamp,
                "ip_address": context.ip_address,
                "user_agent": context.user_agent,
                "mfa_verified": context.mfa_verified,
                "risk_score": context.risk_score
            }
        }
        
        return self._evaluate_policy_rules(policy)
```

#### Dynamic Permission Evaluation
```python
# Example Policy Rules
POLICY_RULES = {
    "mcp_server_access": {
        "conditions": [
            "subject.org_id == resource.org_id",
            "action in subject.permissions",
            "resource.environment in subject.allowed_environments",
            "context.mfa_verified == True",
            "context.risk_score < 0.3"
        ],
        "time_restrictions": {
            "business_hours_only": True,
            "timezone": "UTC"
        },
        "location_restrictions": {
            "allowed_countries": ["US", "CA", "EU"],
            "blocked_regions": ["sanctioned_regions"]
        }
    }
}
```

## Network Security

### Network Segmentation

#### Subnet Architecture
```yaml
# Network Topology
networks:
  public_subnet:
    cidr: "10.0.1.0/24"
    components: ["load_balancer", "cdn", "waf"]
    internet_access: "inbound_only"
    
  dmz_subnet:
    cidr: "10.0.2.0/24" 
    components: ["api_gateway", "auth_service"]
    internet_access: "outbound_filtered"
    
  application_subnet:
    cidr: "10.0.3.0/24"
    components: ["api_service", "websocket_gateway", "workers"]
    internet_access: "outbound_proxy"
    
  data_subnet:
    cidr: "10.0.4.0/24"
    components: ["database", "redis", "vault"]
    internet_access: "none"
    
  management_subnet:
    cidr: "10.0.5.0/24"
    components: ["monitoring", "logging", "backup"]
    internet_access: "outbound_secure"
```

#### Firewall Rules
```yaml
# Security Group Rules
security_groups:
  web_tier:
    ingress:
      - protocol: "tcp"
        port: 443
        source: "0.0.0.0/0"
        description: "HTTPS from internet"
      - protocol: "tcp"
        port: 80
        source: "0.0.0.0/0"
        description: "HTTP redirect to HTTPS"
    
  api_tier:
    ingress:
      - protocol: "tcp"
        port: 8000
        source: "sg-web-tier"
        description: "API from web tier"
      - protocol: "tcp"
        port: 8080
        source: "sg-monitoring"
        description: "Health checks"
    
  data_tier:
    ingress:
      - protocol: "tcp"
        port: 5432
        source: "sg-api-tier"
        description: "PostgreSQL from API"
      - protocol: "tcp"
        port: 6379
        source: "sg-api-tier"
        description: "Redis from API"
```

### TLS/SSL Configuration

#### TLS Settings
```yaml
# TLS Configuration
tls:
  min_version: "1.2"
  preferred_version: "1.3"
  
  cipher_suites:
    # TLS 1.3 (preferred)
    - "TLS_AES_256_GCM_SHA384"
    - "TLS_CHACHA20_POLY1305_SHA256"
    - "TLS_AES_128_GCM_SHA256"
    
    # TLS 1.2 (fallback)
    - "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"
    - "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    - "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305"
  
  # Certificate Configuration
  certificate:
    algorithm: "ECDSA P-256"
    key_length: 256
    validity_period: "90 days"
    auto_renewal: true
    transparency_logging: true
  
  # HSTS Configuration
  hsts:
    max_age: 31536000  # 1 year
    include_subdomains: true
    preload: true
```

#### mTLS for Service Communication
```python
# mTLS Configuration for MCP Server Connections
class MTLSConfig:
    def __init__(self):
        self.ca_cert_path = "/etc/ssl/ca/ca-cert.pem"
        self.client_cert_path = "/etc/ssl/client/client-cert.pem"
        self.client_key_path = "/etc/ssl/client/client-key.pem"
        
        # Certificate validation
        self.verify_hostname = True
        self.verify_certificate = True
        self.check_revocation = True
        
        # Certificate rotation
        self.cert_lifetime = timedelta(days=30)
        self.rotation_threshold = timedelta(days=7)
        self.auto_rotate = True

async def connect_to_mcp_server(server_config: McpServerConfig):
    """Establish mTLS connection to MCP server"""
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations(MTLSConfig.ca_cert_path)
    ssl_context.load_cert_chain(
        MTLSConfig.client_cert_path,
        MTLSConfig.client_key_path
    )
    ssl_context.check_hostname = MTLSConfig.verify_hostname
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    return await aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl_context=ssl_context)
    )
```

### Egress Controls

#### Allowlist Management
```yaml
# Egress Allowlist Configuration
egress_controls:
  mcp_servers:
    # Production MCP servers
    - domain: "*.mcp.company.com"
      ports: [80, 443, 8080]
      protocols: ["http", "https", "ws", "wss"]
      
    # Partner MCP servers
    - domain: "partner-mcp.example.com"
      ports: [443]
      protocols: ["https", "wss"]
      certificate_pinning: true
      
  llm_providers:
    - domain: "api.openai.com"
      ports: [443]
      protocols: ["https"]
      rate_limit: "1000/hour"
      
    - domain: "api.anthropic.com" 
      ports: [443]
      protocols: ["https"]
      rate_limit: "1000/hour"
      
  monitoring:
    - domain: "api.datadoghq.com"
      ports: [443]
      protocols: ["https"]
      
  # Default deny all other egress
  default_policy: "deny"
```

#### SSRF Protection
```python
# Server-Side Request Forgery Protection
class SSRFProtection:
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),     # Loopback
        ipaddress.ip_network("10.0.0.0/8"),      # Private
        ipaddress.ip_network("172.16.0.0/12"),   # Private
        ipaddress.ip_network("192.168.0.0/16"),  # Private
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local
        ipaddress.ip_network("224.0.0.0/4"),     # Multicast
    ]
    
    BLOCKED_PORTS = [22, 23, 25, 53, 110, 143, 993, 995]
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL against SSRF attacks"""
        parsed = urlparse(url)
        
        # Check protocol
        if parsed.scheme not in ["http", "https", "ws", "wss"]:
            raise SecurityError("Invalid protocol")
        
        # Resolve hostname to IP
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
        except (socket.gaierror, ValueError):
            raise SecurityError("Cannot resolve hostname")
        
        # Check against blocked networks
        for network in cls.BLOCKED_NETWORKS:
            if ip in network:
                raise SecurityError("Blocked network range")
        
        # Check against blocked ports
        port = parsed.port or (443 if parsed.scheme.endswith('s') else 80)
        if port in cls.BLOCKED_PORTS:
            raise SecurityError("Blocked port")
        
        return True
```

## Application Security

### Input Validation and Sanitization

#### Request Validation
```python
# Comprehensive Input Validation
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class McpServerCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        regex=r'^[a-zA-Z0-9\-_]+$',
        description="Alphanumeric with hyphens and underscores only"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Server description"
    )
    
    base_url: HttpUrl = Field(
        ...,
        description="MCP server HTTP endpoint"
    )
    
    environment: Environment = Field(
        ...,
        description="Deployment environment"
    )
    
    tags: List[str] = Field(
        default=[],
        max_items=20,
        description="Server tags"
    )
    
    @validator('base_url')
    def validate_url_security(cls, v):
        """Additional security validation for URLs"""
        # SSRF protection
        SSRFProtection.validate_url(str(v))
        
        # Enforce HTTPS in production
        if v.scheme != 'https' and Environment.is_production():
            raise ValueError("HTTPS required in production")
        
        # Check against allowlist
        if not URLAllowlist.is_allowed(v.host):
            raise ValueError("Host not in allowlist")
        
        return v
    
    @validator('tags', each_item=True)
    def validate_tags(cls, v):
        """Validate individual tags"""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError("Tags must be alphanumeric")
        return v.lower()
    
    @validator('description')
    def sanitize_description(cls, v):
        """Sanitize description field"""
        if v:
            # HTML sanitization
            v = bleach.clean(v, tags=[], attributes={}, strip=True)
            # Additional XSS protection
            v = html.escape(v)
        return v
```

#### SQL Injection Prevention
```python
# Safe Database Queries
from sqlalchemy import text
from sqlalchemy.orm import Session

class SecureQueryBuilder:
    @staticmethod
    def build_server_search_query(
        session: Session,
        filters: Dict[str, Any]
    ) -> Query:
        """Build parameterized queries to prevent SQL injection"""
        
        # Base query with ORM (safe by default)
        query = session.query(McpServer)
        
        # Apply filters with parameterization
        if filters.get('environment'):
            query = query.filter(
                McpServer.environment == bindparam('env')
            ).params(env=filters['environment'])
        
        if filters.get('org_id'):
            query = query.filter(
                McpServer.org_id == bindparam('org_id')
            ).params(org_id=filters['org_id'])
        
        # Dynamic text search with parameterization
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    McpServer.name.ilike(bindparam('search')),
                    McpServer.description.ilike(bindparam('search'))
                )
            ).params(search=search_term)
        
        return query
```

### Cross-Site Scripting (XSS) Prevention

#### Content Security Policy (CSP)
```python
# CSP Configuration
CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": [
        "'self'",
        "'unsafe-inline'",  # Only for specific trusted inline scripts
        "https://cdn.jsdelivr.net",
        "https://unpkg.com"
    ],
    "style-src": [
        "'self'",
        "'unsafe-inline'",  # For CSS-in-JS libraries
        "https://fonts.googleapis.com"
    ],
    "img-src": [
        "'self'",
        "data:",
        "https:"
    ],
    "font-src": [
        "'self'",
        "https://fonts.gstatic.com"
    ],
    "connect-src": [
        "'self'",
        "https://api.sprintconnect.com",
        "wss://api.sprintconnect.com"
    ],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"]
}

def build_csp_header() -> str:
    """Build CSP header string"""
    policies = []
    for directive, sources in CSP_POLICY.items():
        policy = f"{directive} {' '.join(sources)}"
        policies.append(policy)
    return "; ".join(policies)
```

#### Output Encoding
```python
# Safe Output Rendering
import html
import json
from markupsafe import Markup, escape

class SafeRenderer:
    @staticmethod
    def render_text(text: str) -> str:
        """Safely render user text content"""
        return html.escape(text) if text else ""
    
    @staticmethod
    def render_json(data: dict) -> Markup:
        """Safely render JSON data"""
        json_str = json.dumps(data, ensure_ascii=True)
        return Markup(json_str)  # Already safe
    
    @staticmethod
    def render_url(url: str) -> str:
        """Safely render URLs"""
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return ""
        
        # HTML escape
        return html.escape(url)
```

### Cross-Site Request Forgery (CSRF) Protection

#### CSRF Token Implementation
```python
# CSRF Protection
import secrets
import hmac
import hashlib
from datetime import datetime, timedelta

class CSRFProtection:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.token_lifetime = timedelta(hours=1)
    
    def generate_token(self, user_id: str, session_id: str) -> str:
        """Generate CSRF token for user session"""
        timestamp = int(datetime.utcnow().timestamp())
        message = f"{user_id}:{session_id}:{timestamp}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        token = f"{timestamp}:{signature}"
        return secrets.token_urlsafe(32) + ":" + token
    
    def validate_token(
        self,
        token: str,
        user_id: str,
        session_id: str
    ) -> bool:
        """Validate CSRF token"""
        try:
            # Parse token
            random_part, timestamp_str, signature = token.split(":", 2)
            timestamp = int(timestamp_str)
            
            # Check expiration
            token_time = datetime.fromtimestamp(timestamp)
            if datetime.utcnow() - token_time > self.token_lifetime:
                return False
            
            # Verify signature
            message = f"{user_id}:{session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, IndexError):
            return False
```

#### SameSite Cookie Configuration
```python
# Secure Cookie Configuration
COOKIE_CONFIG = {
    "secure": True,           # HTTPS only
    "httponly": True,         # No JavaScript access
    "samesite": "Strict",     # CSRF protection
    "max_age": 3600,          # 1 hour expiration
    "domain": ".sprintconnect.com",  # Subdomain access
    "path": "/"               # Full site access
}

def set_secure_cookie(response, name: str, value: str):
    """Set secure cookie with proper configuration"""
    response.set_cookie(
        name,
        value,
        **COOKIE_CONFIG
    )
```

## Data Protection

### Encryption at Rest

#### Database Encryption
```yaml
# PostgreSQL TDE Configuration
postgresql:
  encryption:
    method: "AES-256-GCM"
    key_management: "external_kms"
    key_rotation_interval: "90 days"
    
    # Column-level encryption for sensitive data
    encrypted_columns:
      - table: "users"
        columns: ["email", "phone_number"]
      - table: "mcp_credentials"
        columns: ["credential_data"]
      - table: "audit_logs"
        columns: ["details"]
    
    # Tablespace encryption
    encrypted_tablespaces:
      - "sensitive_data"
      - "audit_logs"
      - "user_data"
```

#### Object Storage Encryption
```yaml
# S3-Compatible Storage Encryption
object_storage:
  server_side_encryption:
    method: "SSE-KMS"
    kms_key_id: "arn:aws:kms:region:account:key/key-id"
    
  client_side_encryption:
    enabled: true
    key_wrap_algorithm: "AES-256-GCM"
    data_encryption_algorithm: "AES-256-GCM"
    
  bucket_encryption:
    default_encryption: "AES256"
    bucket_key_enabled: true
    
  lifecycle_management:
    transition_to_ia: "30 days"
    transition_to_glacier: "90 days"
    expiration: "2555 days"  # 7 years
```

#### Application-Level Encryption
```python
# Field-Level Encryption
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class FieldEncryption:
    def __init__(self, master_key: bytes):
        self.master_key = master_key
    
    def _derive_key(self, context: str) -> bytes:
        """Derive encryption key for specific context"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=context.encode(),
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_key))
    
    def encrypt_field(self, plaintext: str, context: str) -> str:
        """Encrypt sensitive field data"""
        key = self._derive_key(context)
        fernet = Fernet(key)
        
        ciphertext = fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(ciphertext).decode()
    
    def decrypt_field(self, ciphertext: str, context: str) -> str:
        """Decrypt sensitive field data"""
        key = self._derive_key(context)
        fernet = Fernet(key)
        
        encrypted_data = base64.urlsafe_b64decode(ciphertext.encode())
        plaintext = fernet.decrypt(encrypted_data)
        return plaintext.decode()

# Usage in models
class McpCredential(BaseModel):
    id: str
    server_id: str
    credential_type: str
    _encrypted_data: str = Field(alias="credential_data")
    
    @property
    def credential_data(self) -> dict:
        """Decrypt credential data on access"""
        encryptor = FieldEncryption(get_master_key())
        decrypted = encryptor.decrypt_field(
            self._encrypted_data,
            f"mcp_credential:{self.id}"
        )
        return json.loads(decrypted)
    
    @credential_data.setter
    def credential_data(self, value: dict):
        """Encrypt credential data on storage"""
        encryptor = FieldEncryption(get_master_key())
        self._encrypted_data = encryptor.encrypt_field(
            json.dumps(value),
            f"mcp_credential:{self.id}"
        )
```

### Encryption in Transit

#### API Communication
```python
# TLS Configuration for API Services
import ssl
from aiohttp import web, ClientSession
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

def create_ssl_context() -> ssl.SSLContext:
    """Create secure SSL context for API service"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # Load certificates
    context.load_cert_chain('/etc/ssl/server-cert.pem', '/etc/ssl/server-key.pem')
    
    # Security settings
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    # Client certificate verification (for mTLS)
    context.verify_mode = ssl.CERT_OPTIONAL
    context.load_verify_locations('/etc/ssl/ca-cert.pem')
    
    return context

async def create_app() -> web.Application:
    """Create FastAPI application with secure settings"""
    app = web.Application()
    
    # Encrypted session storage
    secret_key = get_session_encryption_key()
    setup(app, EncryptedCookieStorage(secret_key))
    
    return app
```

#### WebSocket Security
```python
# Secure WebSocket Implementation
import asyncio
import jwt
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class SecureWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}
        self.rate_limits: Dict[str, asyncio.Queue] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, token: str):
        """Establish secure WebSocket connection"""
        try:
            # Validate JWT token
            payload = jwt.decode(
                token,
                get_jwt_secret(),
                algorithms=["RS256"],
                audience="sprintconnect"
            )
            user_id = payload["sub"]
            
            # Rate limiting check
            if not await self._check_rate_limit(user_id):
                await websocket.close(code=1008, reason="Rate limit exceeded")
                return
            
            # Accept connection
            await websocket.accept()
            
            # Store connection
            self.active_connections[session_id] = websocket
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
            
            # Set up heartbeat
            asyncio.create_task(self._heartbeat(websocket, session_id))
            
        except jwt.InvalidTokenError:
            await websocket.close(code=1008, reason="Invalid token")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await websocket.close(code=1011, reason="Internal error")
    
    async def _check_rate_limit(self, user_id: str) -> bool:
        """Check WebSocket rate limits"""
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = asyncio.Queue(maxsize=10)
        
        queue = self.rate_limits[user_id]
        try:
            queue.put_nowait(time.time())
            return True
        except asyncio.QueueFull:
            return False
    
    async def _heartbeat(self, websocket: WebSocket, session_id: str):
        """Maintain connection with heartbeat"""
        try:
            while True:
                await asyncio.sleep(30)  # 30 second heartbeat
                await websocket.ping()
        except WebSocketDisconnect:
            await self.disconnect(session_id)
```

### Secrets Management

#### HashiCorp Vault Integration
```python
# Vault Integration for Secret Management
import hvac
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class VaultSecretsManager:
    def __init__(self, vault_url: str, vault_token: str):
        self.client = hvac.Client(url=vault_url, token=vault_token)
        self.client.is_authenticated()
    
    def store_mcp_credentials(
        self,
        server_id: str,
        credentials: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> str:
        """Store MCP server credentials in Vault"""
        path = f"secret/mcp-servers/{server_id}/credentials"
        
        # Add metadata
        secret_data = {
            "credentials": credentials,
            "created_at": datetime.utcnow().isoformat(),
            "server_id": server_id
        }
        
        # Store with TTL if specified
        if ttl:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data,
                ttl=f"{ttl}s"
            )
        else:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data
            )
        
        return path
    
    def get_mcp_credentials(self, server_id: str) -> Dict[str, Any]:
        """Retrieve MCP server credentials from Vault"""
        path = f"secret/mcp-servers/{server_id}/credentials"
        
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response["data"]["data"]["credentials"]
        except hvac.exceptions.InvalidPath:
            raise CredentialNotFoundError(f"Credentials not found for server {server_id}")
    
    def rotate_credentials(self, server_id: str, new_credentials: Dict[str, Any]):
        """Rotate MCP server credentials"""
        path = f"secret/mcp-servers/{server_id}/credentials"
        
        # Store old credentials with timestamp
        old_path = f"{path}/previous"
        try:
            old_creds = self.get_mcp_credentials(server_id)
            old_creds["rotated_at"] = datetime.utcnow().isoformat()
            self.client.secrets.kv.v2.create_or_update_secret(
                path=old_path,
                secret=old_creds,
                ttl="7d"  # Keep old credentials for 7 days
            )
        except CredentialNotFoundError:
            pass  # No existing credentials to backup
        
        # Store new credentials
        self.store_mcp_credentials(server_id, new_credentials)
        
        # Log rotation event
        audit_logger.info(
            "Credentials rotated",
            server_id=server_id,
            rotation_time=datetime.utcnow()
        )
```

#### Credential Rotation
```python
# Automated Credential Rotation
import asyncio
from datetime import datetime, timedelta
from typing import List

class CredentialRotationService:
    def __init__(self, vault_manager: VaultSecretsManager):
        self.vault = vault_manager
        self.rotation_policies = {}
    
    def register_rotation_policy(
        self,
        server_id: str,
        rotation_interval: timedelta,
        credential_generator: callable
    ):
        """Register automatic rotation policy for server"""
        self.rotation_policies[server_id] = {
            "interval": rotation_interval,
            "generator": credential_generator,
            "last_rotation": datetime.utcnow()
        }
    
    async def check_rotations(self):
        """Check and perform necessary credential rotations"""
        for server_id, policy in self.rotation_policies.items():
            time_since_rotation = datetime.utcnow() - policy["last_rotation"]
            
            if time_since_rotation >= policy["interval"]:
                await self._rotate_server_credentials(server_id, policy)
    
    async def _rotate_server_credentials(self, server_id: str, policy: dict):
        """Rotate credentials for a specific server"""
        try:
            # Generate new credentials
            new_credentials = await policy["generator"](server_id)
            
            # Test new credentials
            if await self._test_credentials(server_id, new_credentials):
                # Store in Vault
                self.vault.rotate_credentials(server_id, new_credentials)
                
                # Update last rotation time
                policy["last_rotation"] = datetime.utcnow()
                
                # Notify relevant services
                await self._notify_credential_rotation(server_id)
                
                logger.info(f"Successfully rotated credentials for server {server_id}")
            else:
                logger.error(f"Failed to validate new credentials for server {server_id}")
                
        except Exception as e:
            logger.error(f"Credential rotation failed for server {server_id}: {e}")
            await self._alert_rotation_failure(server_id, str(e))
```

## Audit and Compliance

### Audit Logging

#### Comprehensive Audit Trail
```python
# Audit Logging System
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AuditEventType(Enum):
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    MCP_SERVER_CREATE = "mcp.server.create"
    MCP_SERVER_UPDATE = "mcp.server.update"
    MCP_SERVER_DELETE = "mcp.server.delete"
    CHAT_SESSION_CREATE = "chat.session.create"
    CREDENTIAL_ACCESS = "credential.access"
    ADMIN_ACTION = "admin.action"

class AuditLogger:
    def __init__(self, vault_manager: VaultSecretsManager):
        self.vault = vault_manager
        self.hash_chain = []  # For tamper detection
    
    def log_event(
        self,
        event_type: AuditEventType,
        actor_id: str,
        actor_type: str,
        target_id: Optional[str],
        target_type: Optional[str],
        action: str,
        result: str,
        details: Dict[str, Any],
        request_context: Dict[str, Any]
    ) -> str:
        """Log audit event with tamper detection"""
        
        # Create audit record
        audit_record = {
            "event_id": generate_event_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "actor": {
                "id": actor_id,
                "type": actor_type
            },
            "target": {
                "id": target_id,
                "type": target_type
            } if target_id else None,
            "action": action,
            "result": result,
            "details": details,
            "context": {
                "ip_address": request_context.get("ip_address"),
                "user_agent": request_context.get("user_agent"),
                "request_id": request_context.get("request_id"),
                "session_id": request_context.get("session_id")
            }
        }
        
        # Calculate hash for tamper detection
        record_hash = self._calculate_record_hash(audit_record)
        audit_record["hash"] = record_hash
        audit_record["previous_hash"] = self.hash_chain[-1] if self.hash_chain else None
        
        # Store in database with encryption
        encrypted_record = self._encrypt_audit_record(audit_record)
        self._store_audit_record(encrypted_record)
        
        # Update hash chain
        self.hash_chain.append(record_hash)
        
        # Store hash chain checkpoint in Vault
        if len(self.hash_chain) % 1000 == 0:
            self._store_hash_checkpoint()
        
        return audit_record["event_id"]
    
    def _calculate_record_hash(self, record: Dict[str, Any]) -> str:
        """Calculate cryptographic hash of audit record"""
        # Remove hash fields for calculation
        record_copy = record.copy()
        record_copy.pop("hash", None)
        record_copy.pop("previous_hash", None)
        
        # Canonical JSON serialization
        canonical_json = json.dumps(record_copy, sort_keys=True, separators=(',', ':'))
        
        # Calculate SHA-256 hash
        return hashlib.sha256(canonical_json.encode()).hexdigest()
    
    def verify_audit_integrity(self, start_date: datetime, end_date: datetime) -> bool:
        """Verify integrity of audit logs in date range"""
        records = self._retrieve_audit_records(start_date, end_date)
        
        for i, record in enumerate(records):
            # Verify individual record hash
            calculated_hash = self._calculate_record_hash(record)
            if calculated_hash != record["hash"]:
                logger.error(f"Audit record {record['event_id']} has been tampered with")
                return False
            
            # Verify hash chain
            if i > 0:
                if record["previous_hash"] != records[i-1]["hash"]:
                    logger.error(f"Audit chain broken at record {record['event_id']}")
                    return False
        
        return True
```

#### PII Protection in Audit Logs
```python
# PII Sanitization for Audit Logs
import re
from typing import Any, Dict

class PIISanitizer:
    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s?\d{3}-\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    
    @classmethod
    def sanitize_audit_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize PII from audit log data"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_audit_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls._sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @classmethod
    def _sanitize_string(cls, text: str) -> str:
        """Sanitize PII from string value"""
        # Replace email addresses
        text = cls.EMAIL_PATTERN.sub('[EMAIL]', text)
        
        # Replace phone numbers
        text = cls.PHONE_PATTERN.sub('[PHONE]', text)
        
        # Replace SSNs
        text = cls.SSN_PATTERN.sub('[SSN]', text)
        
        # Replace credit card numbers
        text = cls.CREDIT_CARD_PATTERN.sub('[CREDIT_CARD]', text)
        
        return text
```

### Compliance Controls

#### GDPR Compliance
```python
# GDPR Data Subject Rights Implementation
from datetime import datetime, timedelta
from typing import List, Dict, Any

class GDPRCompliance:
    def __init__(self, db_session, vault_manager: VaultSecretsManager):
        self.db = db_session
        self.vault = vault_manager
    
    async def handle_data_subject_request(
        self,
        request_type: str,
        subject_email: str,
        verification_token: str
    ) -> Dict[str, Any]:
        """Handle GDPR data subject requests"""
        
        # Verify request authenticity
        if not self._verify_subject_identity(subject_email, verification_token):
            raise ValueError("Invalid verification token")
        
        user = self._find_user_by_email(subject_email)
        if not user:
            return {"status": "no_data", "message": "No data found for subject"}
        
        if request_type == "access":
            return await self._handle_access_request(user)
        elif request_type == "portability":
            return await self._handle_portability_request(user)
        elif request_type == "erasure":
            return await self._handle_erasure_request(user)
        elif request_type == "rectification":
            return await self._handle_rectification_request(user)
        else:
            raise ValueError(f"Unknown request type: {request_type}")
    
    async def _handle_access_request(self, user) -> Dict[str, Any]:
        """Provide user with access to their personal data"""
        data_inventory = {
            "personal_information": {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "mcp_servers": [],
            "chat_sessions": [],
            "audit_logs": []
        }
        
        # Collect MCP servers owned by user
        servers = self.db.query(McpServer).filter(McpServer.owner_id == user.id).all()
        for server in servers:
            data_inventory["mcp_servers"].append({
                "id": server.id,
                "name": server.name,
                "created_at": server.created_at.isoformat(),
                "environment": server.environment
            })
        
        # Collect chat sessions
        sessions = self.db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
        for session in sessions:
            data_inventory["chat_sessions"].append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "message_count": len(session.messages)
            })
        
        # Collect relevant audit logs (last 12 months)
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        audit_logs = self.db.query(AuditLog).filter(
            AuditLog.actor_id == user.id,
            AuditLog.timestamp >= cutoff_date
        ).all()
        
        for log in audit_logs:
            data_inventory["audit_logs"].append({
                "event_type": log.event_type,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "result": log.result
            })
        
        return {
            "status": "completed",
            "data": data_inventory,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_erasure_request(self, user) -> Dict[str, Any]:
        """Handle right to erasure (right to be forgotten)"""
        
        # Check for legal basis to retain data
        retention_requirements = self._check_retention_requirements(user)
        if retention_requirements:
            return {
                "status": "partial_erasure",
                "message": "Some data must be retained for legal compliance",
                "retained_data": retention_requirements
            }
        
        # Pseudonymize audit logs (replace PII with pseudonyms)
        self._pseudonymize_audit_logs(user.id)
        
        # Delete personal data
        await self._delete_user_data(user)
        
        # Log erasure action
        audit_logger.log_event(
            AuditEventType.GDPR_ERASURE,
            actor_id="system",
            actor_type="automated_process",
            target_id=user.id,
            target_type="user",
            action="data_erasure",
            result="success",
            details={"request_type": "erasure", "user_email": user.email},
            request_context={}
        )
        
        return {
            "status": "completed",
            "message": "Personal data has been erased",
            "completed_at": datetime.utcnow().isoformat()
        }
```

#### SOC2 Controls
```python
# SOC2 Security Controls Implementation
from typing import Dict, List, Any
from datetime import datetime, timedelta

class SOC2Controls:
    def __init__(self):
        self.control_checks = {}
    
    def register_control(self, control_id: str, check_function: callable):
        """Register SOC2 control check"""
        self.control_checks[control_id] = check_function
    
    async def run_control_assessment(self) -> Dict[str, Any]:
        """Run comprehensive SOC2 control assessment"""
        results = {
            "assessment_date": datetime.utcnow().isoformat(),
            "controls": {},
            "overall_status": "compliant"
        }
        
        for control_id, check_function in self.control_checks.items():
            try:
                control_result = await check_function()
                results["controls"][control_id] = control_result
                
                if control_result["status"] != "compliant":
                    results["overall_status"] = "non_compliant"
                    
            except Exception as e:
                results["controls"][control_id] = {
                    "status": "error",
                    "message": str(e),
                    "checked_at": datetime.utcnow().isoformat()
                }
                results["overall_status"] = "error"
        
        return results

# Example SOC2 control implementations
async def cc6_1_logical_access_controls():
    """CC6.1 - Logical and Physical Access Controls"""
    findings = []
    
    # Check for unused accounts
    inactive_threshold = datetime.utcnow() - timedelta(days=90)
    inactive_users = db.query(User).filter(
        User.last_login < inactive_threshold,
        User.status == "active"
    ).count()
    
    if inactive_users > 0:
        findings.append(f"{inactive_users} inactive user accounts found")
    
    # Check for privileged access reviews
    privileged_users = db.query(User).filter(
        User.roles.contains("admin")
    ).all()
    
    for user in privileged_users:
        last_review = get_last_access_review(user.id)
        if not last_review or last_review < datetime.utcnow() - timedelta(days=90):
            findings.append(f"Privileged access for {user.email} not reviewed in 90 days")
    
    return {
        "control_id": "CC6.1",
        "status": "compliant" if not findings else "non_compliant",
        "findings": findings,
        "checked_at": datetime.utcnow().isoformat()
    }

async def cc6_7_transmission_of_data():
    """CC6.7 - Data Transmission Controls"""
    findings = []
    
    # Check TLS configuration
    tls_config = get_tls_configuration()
    if tls_config["min_version"] < "1.2":
        findings.append("TLS version below 1.2 detected")
    
    # Check for unencrypted data transmission
    unencrypted_endpoints = check_unencrypted_endpoints()
    if unencrypted_endpoints:
        findings.append(f"Unencrypted endpoints found: {unencrypted_endpoints}")
    
    return {
        "control_id": "CC6.7",
        "status": "compliant" if not findings else "non_compliant",
        "findings": findings,
        "checked_at": datetime.utcnow().isoformat()
    }
```

## Incident Response

### Security Incident Detection
```python
# Security Incident Detection and Response
import asyncio
from typing import List, Dict, Any
from enum import Enum

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityIncidentDetector:
    def __init__(self):
        self.detection_rules = []
        self.active_incidents = {}
    
    def register_detection_rule(self, rule: callable):
        """Register security incident detection rule"""
        self.detection_rules.append(rule)
    
    async def monitor_security_events(self):
        """Continuously monitor for security incidents"""
        while True:
            try:
                for rule in self.detection_rules:
                    incidents = await rule()
                    for incident in incidents:
                        await self._handle_incident(incident)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _handle_incident(self, incident: Dict[str, Any]):
        """Handle detected security incident"""
        incident_id = incident["id"]
        
        if incident_id not in self.active_incidents:
            self.active_incidents[incident_id] = incident
            
            # Log incident
            audit_logger.log_event(
                AuditEventType.SECURITY_INCIDENT,
                actor_id="security_system",
                actor_type="automated_detection",
                target_id=incident_id,
                target_type="security_incident",
                action="incident_detected",
                result="alert_created",
                details=incident,
                request_context={}
            )
            
            # Execute response actions
            await self._execute_incident_response(incident)

# Example detection rules
async def detect_brute_force_attacks():
    """Detect brute force login attempts"""
    incidents = []
    
    # Check for multiple failed logins
    threshold_time = datetime.utcnow() - timedelta(minutes=15)
    failed_attempts = db.query(AuditLog).filter(
        AuditLog.event_type == "user.login_failed",
        AuditLog.timestamp >= threshold_time
    ).all()
    
    # Group by source IP
    ip_attempts = {}
    for attempt in failed_attempts:
        ip = attempt.context.get("ip_address")
        if ip:
            ip_attempts[ip] = ip_attempts.get(ip, 0) + 1
    
    # Alert on high failure rates
    for ip, count in ip_attempts.items():
        if count >= 10:  # 10 failed attempts in 15 minutes
            incidents.append({
                "id": f"brute_force_{ip}_{int(time.time())}",
                "type": "brute_force_attack",
                "severity": IncidentSeverity.HIGH,
                "source_ip": ip,
                "attempt_count": count,
                "time_window": "15_minutes",
                "description": f"Brute force attack detected from {ip} ({count} attempts)"
            })
    
    return incidents

async def detect_privilege_escalation():
    """Detect unauthorized privilege escalation"""
    incidents = []
    
    # Check for role changes
    recent_role_changes = db.query(AuditLog).filter(
        AuditLog.event_type == "user.role_changed",
        AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
    ).all()
    
    for change in recent_role_changes:
        # Check if elevation was authorized
        if not await _verify_role_change_authorization(change):
            incidents.append({
                "id": f"privilege_escalation_{change.target_id}_{int(time.time())}",
                "type": "privilege_escalation",
                "severity": IncidentSeverity.CRITICAL,
                "user_id": change.target_id,
                "old_roles": change.details.get("old_roles"),
                "new_roles": change.details.get("new_roles"),
                "actor_id": change.actor_id,
                "description": f"Unauthorized privilege escalation for user {change.target_id}"
            })
    
    return incidents
```

### Automated Response Actions
```python
# Automated Incident Response
class IncidentResponseOrchestrator:
    def __init__(self):
        self.response_playbooks = {}
    
    def register_playbook(self, incident_type: str, playbook: callable):
        """Register incident response playbook"""
        self.response_playbooks[incident_type] = playbook
    
    async def execute_response(self, incident: Dict[str, Any]):
        """Execute appropriate response for incident"""
        incident_type = incident["type"]
        
        if incident_type in self.response_playbooks:
            playbook = self.response_playbooks[incident_type]
            await playbook(incident)
        else:
            # Default response
            await self._default_incident_response(incident)

# Response playbooks
async def brute_force_response_playbook(incident: Dict[str, Any]):
    """Response playbook for brute force attacks"""
    source_ip = incident["source_ip"]
    
    # 1. Block source IP
    await firewall_manager.block_ip(source_ip, duration=timedelta(hours=24))
    
    # 2. Alert security team
    await notification_service.send_alert(
        channel="security",
        message=f"🚨 Brute force attack blocked from {source_ip}",
        severity="high"
    )
    
    # 3. Increase monitoring for affected accounts
    affected_accounts = await get_accounts_targeted_by_ip(source_ip)
    for account in affected_accounts:
        await enable_enhanced_monitoring(account)
    
    # 4. Generate incident report
    report = await generate_incident_report(incident)
    await store_incident_report(report)

async def privilege_escalation_response_playbook(incident: Dict[str, Any]):
    """Response playbook for privilege escalation"""
    user_id = incident["user_id"]
    
    # 1. Immediately suspend user account
    await user_manager.suspend_account(user_id, reason="security_incident")
    
    # 2. Revoke all active sessions
    await session_manager.revoke_all_sessions(user_id)
    
    # 3. Alert security team immediately
    await notification_service.send_urgent_alert(
        channel="security",
        message=f"🚨 CRITICAL: Privilege escalation detected for user {user_id}",
        severity="critical"
    )
    
    # 4. Initiate security investigation
    await security_investigation.initiate(
        incident_id=incident["id"],
        investigation_type="privilege_escalation",
        priority="critical"
    )
```

This comprehensive security architecture provides enterprise-grade protection for SprintConnect while maintaining usability and compliance with regulatory requirements. The layered security approach ensures that even if one control fails, multiple backup protections remain in place.

---

## Addendums: OAuth 2.1, Token Binding, PDP, OWASP LLM

### OAuth 2.1 Alignment
```yaml
oauth_2_1:
  pkce_required: true
  implicit_flow: disabled
  exact_redirect_uri_match: true
  https_only: true
  refresh_rotation: enabled
```

### Advanced OAuth Features
```yaml
par_jar:
  pushed_authorization_requests: enabled   # RFC 9126
  jwt_secured_authorization_request: enabled   # RFC 9101

token_binding:
  dpop: enabled     # RFC 9449
  mtls: enabled     # RFC 8705

access_tokens:
  format: jwt
  alg_allowlist: ["RS256", "ES256"]
  required_claims: ["iss", "sub", "aud", "exp", "nbf"]
  jwks_cache_ttl_seconds: 300
  audience: "sprintconnect"

token_lifecycle:
  introspection: enabled    # RFC 7662
  revocation: enabled       # RFC 7009
  reuse_detection: enabled  # refresh rotation reuse
```

### Capability-Scoped Authorization
```yaml
scopes:
  - name: "mcp:server:{server_id}:capability:{capability}:invoke"
  - name: "mcp:server:{server_id}:capability:list"
  - name: "mcp:server:{server_id}:discover"

resource_indicators:
  enabled: true
  audience_binding: true   # RFC 8707

token_exchange:
  enabled: true            # RFC 8693
  on_behalf_of: true
  actor_token: supported
```

### Tenant-Aware Egress Proxy
```yaml
egress_proxy:
  dns_pinning: true
  private_ip_block: true
  deny_ports: [22, 23, 25, 53, 110, 143, 993, 995]
  per_tenant_allowlists: true
  decision_logging: true
```

### OWASP Top 10 for LLM Applications
```yaml
llm_security:
  prompt_injection:
    - tool_allowlist_enforcement
    - system_prompt_guardrails
    - argument_schema_validation
  insecure_output_handling:
    - schema_conformance_required
    - content_classification_and_redaction
    - policy_gate_before_side_effects
  training_data_poisoning:
    - segregate_untrusted_feedback
    - provenance_tracking
```

### Audit Enrichment
```yaml
audit_enrichment:
  include_claims: ["iss", "aud", "sub", "jti", "client_id", "scope"]
  include_context: ["request_id", "tenant_id", "token_binding", "pdp_policy_version"]
```

