# SprintConnect Backend Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the SprintConnect backend, ensuring enterprise-grade quality and reliability.

## Testing Philosophy

- **Test-Driven Development**: Write tests before implementing features
- **Comprehensive Coverage**: Aim for >90% code coverage
- **Fast Feedback**: Tests should run quickly for developer productivity
- **Isolation**: Each test should be independent and not affect others
- **Realistic Data**: Use realistic test data that mirrors production scenarios

## Test Structure

### Test Categories

1. **Unit Tests** (`@pytest.mark.unit`)
   - Test individual functions and methods in isolation
   - Mock external dependencies
   - Fast execution (< 1 second per test)

2. **Integration Tests** (`@pytest.mark.integration`)
   - Test component interactions
   - Use real database and external services
   - Moderate execution time (1-5 seconds per test)

3. **API Tests** (`@pytest.mark.api`)
   - Test HTTP endpoints through FastAPI TestClient
   - Verify request/response contracts
   - Test authentication and authorization

4. **Service Tests** (`@pytest.mark.service`)
   - Test business logic in service layer
   - Mock database and external dependencies
   - Focus on business rules and validation

5. **Schema Tests** (`@pytest.mark.schema`)
   - Test Pydantic model validation
   - Verify data transformation and serialization
   - Test enum values and constraints

6. **Security Tests** (`@pytest.mark.security`)
   - Test authentication and authorization
   - Verify SSRF protection and input validation
   - Test data sanitization and encryption

7. **Smoke Tests** (`@pytest.mark.smoke`)
   - Basic functionality tests for CI/CD
   - Quick verification of critical paths
   - Must pass for deployment

### Test Organization

```
app/tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_api_mcp_servers.py     # API endpoint tests
├── test_services_mcp_server.py # Service layer tests
├── test_schemas_mcp_server.py  # Schema validation tests
├── test_security.py           # Security-specific tests
├── test_integration.py        # Integration tests
└── test_utils.py              # Utility function tests
```

## Running Tests

### Basic Commands

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest app/tests/test_schemas_mcp_server.py

# Run specific test class
poetry run pytest app/tests/test_schemas_mcp_server.py::TestMcpServerCreateSchema

# Run specific test method
poetry run pytest app/tests/test_schemas_mcp_server.py::TestMcpServerCreateSchema::test_valid_server_data

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run tests by category
poetry run pytest -m api
poetry run pytest -m service
poetry run pytest -m schema
poetry run pytest -m security
```

### Using the Test Runner

```bash
# Run all tests with coverage
python run_tests.py --coverage

# Run specific test types
python run_tests.py --test-type api
python run_tests.py --test-type service
python run_tests.py --test-type schema

# Run with verbose output
python run_tests.py --verbose

# Skip slow tests
python run_tests.py --fast
```

## Test Fixtures

### Database Fixtures

```python
@pytest.fixture(scope="session")
def db_engine():
    """Database engine for testing."""
    # Creates in-memory SQLite database
    # Scope: session (created once per test session)

@pytest.fixture
def db_session(db_engine):
    """Database session for testing."""
    # Creates transaction-wrapped session
    # Scope: function (created for each test)
    # Automatically rolls back after each test
```

### Data Fixtures

```python
@pytest.fixture
def sample_organization(db_session):
    """Create a sample organization."""
    # Creates test organization in database

@pytest.fixture
def sample_user(db_session, sample_organization):
    """Create a sample user."""
    # Creates test user associated with organization

@pytest.fixture
def sample_mcp_server(db_session, sample_organization, sample_user):
    """Create a sample MCP server."""
    # Creates test MCP server with all relationships
```

### Test Data Fixtures

```python
@pytest.fixture
def valid_server_data():
    """Valid server creation data."""
    return {
        "name": "test-server",
        "description": "Test MCP server",
        "environment": "development",
        "base_url": "https://test.example.com",
        "tags": ["test"],
        "metadata": {"test": "data"},
        "auto_discover": True
    }
```

## Test Patterns

### API Test Pattern

```python
class TestMcpServerAPICreate:
    """Test MCP server creation endpoints."""
    
    def test_create_server_success(self, client, valid_server_data):
        """Test successful server creation."""
        response = client.post("/v1/mcp/servers/", json=valid_server_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "test-server"
        assert data["status"] == "pending_discovery"
```

### Service Test Pattern

```python
class TestMcpServerServiceCreate:
    """Test MCP server service creation methods."""
    
    def test_create_server_success(self, db_session, sample_user, valid_server_data):
        """Test successful server creation."""
        service = McpServerService(db_session)
        
        server_data = McpServerCreate(**valid_server_data)
        server = service.create_server(server_data, sample_user, "test-request-id")
        
        assert server.name == "test-server"
        assert server.org_id == sample_user.org_id
```

### Schema Test Pattern

```python
class TestMcpServerCreateSchema:
    """Test McpServerCreate schema validation."""
    
    def test_valid_server_data(self):
        """Test valid server creation data."""
        data = {
            "name": "test-server",
            "base_url": "https://test.example.com",
            "environment": "development"
        }
        
        server = McpServerCreate(**data)
        assert server.name == "test-server"
        assert server.environment == Environment.DEVELOPMENT
```

## Test Data Management

### Test Data Principles

1. **Realistic Data**: Use data that mirrors production scenarios
2. **Minimal Data**: Use only the data necessary for the test
3. **Consistent Data**: Use fixtures to ensure consistent test data
4. **Isolated Data**: Each test should have its own data set

### Data Cleanup

- Database transactions are automatically rolled back after each test
- No manual cleanup required
- Tests are isolated and don't affect each other

## Coverage Requirements

### Minimum Coverage Targets

- **Overall Coverage**: >90%
- **Critical Paths**: >95%
- **Business Logic**: >95%
- **API Endpoints**: >90%
- **Security Functions**: >95%

### Coverage Reports

```bash
# Generate HTML coverage report
poetry run pytest --cov=app --cov-report=html

# Generate XML coverage report (for CI/CD)
poetry run pytest --cov=app --cov-report=xml

# View coverage in terminal
poetry run pytest --cov=app --cov-report=term-missing
```

## Performance Testing

### Test Performance Requirements

- **Unit Tests**: < 1 second per test
- **Integration Tests**: < 5 seconds per test
- **API Tests**: < 2 seconds per test
- **Full Test Suite**: < 30 seconds

### Performance Monitoring

```bash
# Run tests with timing information
poetry run pytest --durations=10

# Profile slow tests
poetry run pytest --profile
```

## Security Testing

### Security Test Categories

1. **Input Validation**
   - Test SSRF protection
   - Test SQL injection prevention
   - Test XSS prevention

2. **Authentication & Authorization**
   - Test permission checks
   - Test organization isolation
   - Test role-based access control

3. **Data Protection**
   - Test data sanitization
   - Test encryption
   - Test audit logging

### Security Test Examples

```python
def test_ssrf_protection(self, client):
    """Test SSRF protection."""
    server_data = {
        "name": "ssrf-test",
        "base_url": "http://localhost:8080",
        "environment": "production"
    }
    
    response = client.post("/v1/mcp/servers/", json=server_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "URL validation failed" in response.json()["detail"]
```

## Continuous Integration

### CI/CD Pipeline

1. **Pre-commit Hooks**
   - Run unit tests
   - Check code formatting
   - Run linting

2. **Pull Request Checks**
   - Run full test suite
   - Generate coverage report
   - Security scanning

3. **Deployment Checks**
   - Run integration tests
   - Performance tests
   - Smoke tests

### Test Commands for CI

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    poetry install
    poetry run pytest --cov=app --cov-report=xml
    poetry run pytest -m smoke  # Smoke tests for deployment
```

## Best Practices

### Test Writing Guidelines

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one thing
3. **Arrange-Act-Assert**: Structure tests with clear sections
4. **Meaningful Assertions**: Assert the behavior, not implementation
5. **Test Documentation**: Document complex test scenarios

### Test Maintenance

1. **Keep Tests Fast**: Avoid slow operations in tests
2. **Minimize Dependencies**: Mock external services
3. **Update Tests**: Update tests when requirements change
4. **Review Coverage**: Regularly review and improve coverage
5. **Refactor Tests**: Refactor tests as code evolves

### Common Pitfalls

1. **Testing Implementation**: Don't test implementation details
2. **Over-Mocking**: Don't mock everything; use real dependencies when appropriate
3. **Flaky Tests**: Ensure tests are deterministic
4. **Slow Tests**: Keep tests fast for developer productivity
5. **Complex Setup**: Keep test setup simple and readable

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check database URL configuration
   - Verify database is running
   - Check connection pool settings

2. **Import Errors**
   - Check Python path configuration
   - Verify package installation
   - Check import statements

3. **Test Isolation Issues**
   - Ensure proper fixture scoping
   - Check for shared state between tests
   - Verify transaction rollback

### Debugging Tests

```bash
# Run tests with debug output
poetry run pytest -v -s

# Run specific test with debugger
poetry run pytest -s --pdb

# Run tests with detailed error information
poetry run pytest --tb=long
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction)
- [Pydantic Testing](https://docs.pydantic.dev/latest/concepts/testing/)
