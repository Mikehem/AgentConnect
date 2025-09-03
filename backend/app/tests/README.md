# SprintConnect Backend Tests

This directory contains comprehensive tests for the SprintConnect backend, organized by features for better maintainability and clarity.

## Test Organization

### Feature-Based Structure

Tests are organized by features to make it easier to:
- Find tests related to specific functionality
- Run tests for specific features
- Maintain and update tests as features evolve
- Understand the scope of each test suite

```
app/tests/
├── conftest.py                    # Shared pytest fixtures
├── features/                      # Feature-based test organization
│   ├── mcp_servers/              # MCP Server management tests
│   │   ├── __init__.py
│   │   ├── test_api.py           # API endpoint tests
│   │   ├── test_services.py      # Service layer tests
│   │   └── test_schemas.py       # Schema validation tests
│   ├── auth/                     # Authentication and authorization tests
│   │   ├── __init__.py
│   │   └── test_oidc.py          # OIDC, JWT, API key tests
│   ├── organizations/            # Organization management tests
│   │   ├── __init__.py
│   │   └── test_api.py           # Organization API tests
│   ├── capabilities/             # Capability discovery and testing
│   │   ├── __init__.py
│   │   └── test_discovery.py     # Capability discovery tests
│   ├── health/                   # Health monitoring tests
│   │   ├── __init__.py
│   │   └── test_monitoring.py    # Health check and monitoring tests
│   ├── users/                    # User management tests (future)
│   ├── discovery/                # Auto-discovery tests (future)
│   └── chat/                     # Chat interface tests (future)
└── README.md                     # This file
```

## Test Categories

### 1. MCP Servers (`features/mcp_servers/`)
Tests for MCP server registration, management, and CRUD operations.

**Files:**
- `test_api.py` - API endpoint tests for server CRUD operations
- `test_services.py` - Business logic tests for server management
- `test_schemas.py` - Pydantic schema validation tests

**Coverage:**
- Server creation, retrieval, updating, deletion
- URL validation and SSRF protection
- Organization quota management
- Duplicate name handling
- Metadata sanitization

### 2. Authentication (`features/auth/`)
Tests for authentication and authorization mechanisms.

**Files:**
- `test_oidc.py` - OIDC, JWT, API key, and session management tests

**Coverage:**
- OIDC authentication flow
- JWT token validation
- API key authentication
- Permission validation
- Organization data isolation
- Session management

### 3. Organizations (`features/organizations/`)
Tests for organization management and multi-tenancy.

**Files:**
- `test_api.py` - Organization API tests

**Coverage:**
- Organization CRUD operations
- Quota management
- Settings management
- Multi-tenant isolation

### 4. Capabilities (`features/capabilities/`)
Tests for MCP server capability discovery and testing.

**Files:**
- `test_discovery.py` - Capability discovery and testing

**Coverage:**
- Capability discovery
- Schema validation
- Method testing
- Capability management
- Usage analytics

### 5. Health Monitoring (`features/health/`)
Tests for health monitoring and alerting.

**Files:**
- `test_monitoring.py` - Health check and monitoring tests

**Coverage:**
- Health checks
- Status management
- History tracking
- Alert management
- Metrics and analytics
- Notification channels

## Running Tests

### Using the Test Runner

```bash
# Run all feature tests
python run_tests.py

# Run specific feature tests
python run_tests.py --test-type auth
python run_tests.py --test-type health
python run_tests.py --test-type capabilities

# Run with coverage
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose

# Skip slow tests
python run_tests.py --fast
```

### Using Pytest Directly

```bash
# Run all tests
poetry run pytest

# Run specific feature tests
poetry run pytest app/tests/features/mcp_servers/
poetry run pytest app/tests/features/auth/
poetry run pytest app/tests/features/health/

# Run tests by marker
poetry run pytest -m api
poetry run pytest -m service
poetry run pytest -m schema
poetry run pytest -m auth
poetry run pytest -m health
poetry run pytest -m capabilities

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

## Test Markers

The following pytest markers are used to categorize tests:

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.schema` - Schema validation tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.health` - Health monitoring tests
- `@pytest.mark.capabilities` - Capability discovery tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.smoke` - Smoke tests

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- `db_engine` - Database engine for testing
- `db_session` - Database session with transaction rollback
- `client` - FastAPI test client
- `sample_organization` - Sample organization data
- `sample_user` - Sample user data
- `sample_mcp_server` - Sample MCP server data
- `sample_mcp_credential` - Sample MCP credential data
- `valid_server_data` - Valid server creation data
- `valid_server_data_with_auth` - Valid server data with authentication

## Best Practices

### Test Organization
- Group related tests in feature directories
- Use descriptive test class and method names
- Include docstrings for all test methods
- Use appropriate pytest markers

### Test Data
- Use fixtures for reusable test data
- Create realistic test scenarios
- Test both success and failure cases
- Include edge cases and boundary conditions

### Mocking
- Mock external dependencies (databases, APIs, etc.)
- Use `unittest.mock.patch` for external services
- Mock time-dependent operations
- Test error conditions with mocked failures

### Assertions
- Use specific assertions (e.g., `assert response.status_code == 200`)
- Test response structure and content
- Verify error messages and status codes
- Check side effects (database changes, etc.)

### Coverage
- Aim for high test coverage (>80%)
- Focus on critical business logic
- Test security-sensitive operations
- Include integration tests for key workflows

## Adding New Tests

### For New Features
1. Create a new directory under `features/`
2. Add an `__init__.py` file
3. Create test files following the naming convention
4. Use appropriate pytest markers
5. Add the feature to the test runner

### For Existing Features
1. Add tests to the appropriate feature directory
2. Follow the existing naming and organization patterns
3. Use shared fixtures when possible
4. Update this README if adding new test categories

### Example Structure
```python
"""Tests for new feature."""

import pytest
from fastapi import status

pytestmark = pytest.mark.new_feature


class TestNewFeatureAPI:
    """Test new feature API endpoints."""

    def test_feature_endpoint_success(self, client, sample_user):
        """Test successful feature operation."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.post("/v1/new-feature", json={"data": "test"})
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "success"
```

## Continuous Integration

Tests are automatically run in CI/CD pipelines:
- All tests must pass before merging
- Coverage reports are generated
- Security tests are run separately
- Performance tests are run on schedule

## Troubleshooting

### Common Issues
1. **Database errors**: Ensure test database is properly configured
2. **Import errors**: Check that all dependencies are installed
3. **Mock failures**: Verify mock setup and teardown
4. **Fixture errors**: Check fixture dependencies and scope

### Debugging
- Use `pytest -v` for verbose output
- Use `pytest --tb=long` for detailed tracebacks
- Use `pytest -s` to see print statements
- Use `pytest --pdb` to drop into debugger on failures
