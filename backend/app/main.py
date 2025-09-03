"""Main FastAPI application."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import structlog

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.mcp_servers import router as mcp_servers_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.auth import router as auth_router
from app.api.v1.capabilities import router as capabilities_router
from app.api.v1.health import router as health_router
from app.core.middleware import AuthGatewayMiddleware

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting SprintConnect API", version=settings.APP_VERSION)
    
    yield
    
    # Shutdown
    logger.info("Shutting down SprintConnect API")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade MCP server discovery and testing platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(AuthGatewayMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # TODO: Configure allowed hosts
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and metrics."""
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = str(time.time())
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(process_time)
    
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with structured logging."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "HTTP request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, 'request_id', None)
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        "HTTP response",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# API routes
app.include_router(
    mcp_servers_router,
    prefix=f"{settings.API_V1_STR}/mcp/servers",
    tags=["MCP Servers"]
)

app.include_router(
    organizations_router,
    prefix=f"{settings.API_V1_STR}/organizations",
    tags=["Organizations"]
)

app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Authentication"]
)

app.include_router(
    capabilities_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Capabilities"]
)

app.include_router(
    health_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Health Monitoring"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SprintConnect API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
