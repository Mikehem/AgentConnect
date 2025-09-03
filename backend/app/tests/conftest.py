"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db, create_tables
from app.models.mcp_server import McpServer, McpCredential, McpCapability, McpHealthCheck
from app.models.user import User
from app.models.organization import Organization
from app.schemas.mcp_server import Environment, CredentialType, ServerStatus, HealthStatus


# Create in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db_engine():
    """Database engine for testing."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Database session for testing."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    """Test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_organization(db_session):
    """Create a sample organization."""
    import uuid
    org = Organization(
        name="Test Organization",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        settings={},
        subscription_tier="free",
        status="active"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def sample_user(db_session, sample_organization):
    """Create a sample user."""
    user = User(
        org_id=sample_organization.id,
        email="test@example.com",
        name="Test User",
        roles=["admin"],
        status="active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_mcp_server(db_session, sample_organization, sample_user):
    """Create a sample MCP server."""
    server = McpServer(
        org_id=sample_organization.id,
        name="test-server",
        description="Test MCP server",
        environment="development",
        base_url="https://api.openai.com",
        tags=["test"],
        server_metadata={"test": "data"},
        owner_user_id=sample_user.id,
        status=ServerStatus.ACTIVE.value,
        health_status=HealthStatus.HEALTHY.value
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


@pytest.fixture
def sample_mcp_credential(db_session, sample_mcp_server):
    """Create a sample MCP credential."""
    credential = McpCredential(
        mcp_server_id=sample_mcp_server.id,
        credential_type=CredentialType.BEARER_TOKEN.value,
        vault_path="mcp/test-org/credentials/test-server",
        scope=[],
        credential_metadata={}
    )
    db_session.add(credential)
    db_session.commit()
    db_session.refresh(credential)
    return credential


@pytest.fixture
def valid_server_data():
    """Valid server creation data."""
    return {
        "name": "test-server",
        "description": "Test MCP server",
        "environment": "development",
        "base_url": "https://api.openai.com",
        "tags": ["test"],
        "metadata": {"test": "data"},
        "auto_discover": True
    }


@pytest.fixture
def valid_server_data_with_auth():
    """Valid server creation data with authentication."""
    return {
        "name": "test-server-auth",
        "description": "Test MCP server with auth",
        "environment": "development",
        "base_url": "https://api.openai.com",
        "auth_config": {
            "type": "bearer_token",
            "vault_path": "mcp/test-org/credentials/test-server"
        },
        "auto_discover": False
    }
