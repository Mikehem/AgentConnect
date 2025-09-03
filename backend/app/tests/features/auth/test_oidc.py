"""OIDC authentication tests."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status

pytestmark = pytest.mark.auth


class TestOIDCAuthentication:
    """Test OIDC authentication flow."""

    def test_oidc_login_redirect(self, client):
        """Test OIDC login redirect."""
        response = client.get("/v1/auth/oidc/login")
        
        assert response.status_code == status.HTTP_302_FOUND
        assert "authorization_endpoint" in response.headers.get("location", "")

    def test_oidc_callback_success(self, client):
        """Test successful OIDC callback."""
        # Mock OIDC token exchange
        with patch('app.services.auth.exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "mock_access_token",
                "id_token": "mock_id_token"
            }
            
            response = client.get("/v1/auth/oidc/callback?code=test_code")
            
            assert response.status_code == status.HTTP_200_OK

    def test_oidc_callback_invalid_code(self, client):
        """Test OIDC callback with invalid code."""
        with patch('app.services.auth.exchange_code_for_token') as mock_exchange:
            mock_exchange.side_effect = ValueError("Invalid authorization code")
            
            response = client.get("/v1/auth/oidc/callback?code=invalid_code")
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_oidc_logout(self, client):
        """Test OIDC logout."""
        response = client.post("/v1/auth/oidc/logout")
        
        assert response.status_code == status.HTTP_200_OK


class TestJWTTokenValidation:
    """Test JWT token validation."""

    def test_valid_jwt_token(self, client, sample_user):
        """Test valid JWT token."""
        # Mock JWT token generation and validation
        with patch('app.core.security.create_access_token') as mock_create:
            mock_create.return_value = "valid_jwt_token"
            
            token = mock_create.return_value
            client.headers.update({"Authorization": f"Bearer {token}"})
            
            # Test protected endpoint
            response = client.get("/v1/mcp/servers")
            
            # Should not return 401 (unauthorized)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_invalid_jwt_token(self, client):
        """Test invalid JWT token."""
        client.headers.update({"Authorization": "Bearer invalid_token"})
        
        response = client.get("/v1/mcp/servers")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_jwt_token(self, client):
        """Test missing JWT token."""
        response = client.get("/v1/mcp/servers")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_jwt_token(self, client):
        """Test expired JWT token."""
        # Mock expired token
        with patch('app.core.security.verify_token') as mock_verify:
            mock_verify.side_effect = ValueError("Token has expired")
            
            client.headers.update({"Authorization": "Bearer expired_token"})
            response = client.get("/v1/mcp/servers")
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPIKeyAuthentication:
    """Test API key authentication."""

    def test_valid_api_key(self, client, sample_user):
        """Test valid API key authentication."""
        # Mock API key validation
        with patch('app.services.auth.validate_api_key') as mock_validate:
            mock_validate.return_value = sample_user
            
            client.headers.update({"X-API-Key": "valid_api_key"})
            response = client.get("/v1/mcp/servers")
            
            assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_invalid_api_key(self, client):
        """Test invalid API key."""
        with patch('app.services.auth.validate_api_key') as mock_validate:
            mock_validate.return_value = None
            
            client.headers.update({"X-API-Key": "invalid_api_key"})
            response = client.get("/v1/mcp/servers")
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_api_key(self, client):
        """Test missing API key."""
        response = client.get("/v1/mcp/servers")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_key_scope_validation(self, client, sample_user):
        """Test API key scope validation."""
        # Mock API key with limited scope
        with patch('app.services.auth.validate_api_key') as mock_validate:
            mock_user = MagicMock()
            mock_user.has_permission.return_value = False
            mock_validate.return_value = mock_user
            
            client.headers.update({"X-API-Key": "limited_scope_key"})
            response = client.post("/v1/mcp/servers", json={})
            
            assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPermissionValidation:
    """Test permission validation."""

    def test_user_with_permission(self, client, sample_user):
        """Test user with required permission."""
        # Mock user with permission
        with patch('app.core.security.get_current_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.has_permission.return_value = True
            mock_get_user.return_value = mock_user
            
            client.headers.update({"Authorization": "Bearer valid_token"})
            response = client.post("/v1/mcp/servers", json={})
            
            # Should not return 403 (forbidden)
            assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_user_without_permission(self, client):
        """Test user without required permission."""
        # Mock user without permission
        with patch('app.core.security.get_current_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.has_permission.return_value = False
            mock_get_user.return_value = mock_user
            
            client.headers.update({"Authorization": "Bearer valid_token"})
            response = client.post("/v1/mcp/servers", json={})
            
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_organization_isolation(self, client, sample_user):
        """Test organization data isolation."""
        # Mock user from different organization
        with patch('app.core.security.get_current_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.org_id = "different-org-id"
            mock_get_user.return_value = mock_user
            
            client.headers.update({"Authorization": "Bearer valid_token"})
            response = client.get("/v1/mcp/servers")
            
            # Should only return servers from user's organization
            data = response.json()
            assert all(server["org_id"] == mock_user.org_id for server in data.get("servers", []))


class TestSessionManagement:
    """Test session management."""

    def test_session_creation(self, client, sample_user):
        """Test session creation on login."""
        with patch('app.services.auth.create_user_session') as mock_create_session:
            mock_create_session.return_value = "session_id"
            
            response = client.post("/v1/auth/login", json={
                "email": "test@example.com",
                "password": "password"
            })
            
            assert response.status_code == status.HTTP_200_OK
            assert "session_id" in response.json()

    def test_session_validation(self, client):
        """Test session validation."""
        with patch('app.services.auth.validate_session') as mock_validate:
            mock_validate.return_value = {
                "session_id": "valid_session_id",
                "user_id": "user-123",
                "org_id": "org-123",
                "valid": True
            }
            
            client.headers.update({"X-Session-ID": "valid_session_id"})
            response = client.get("/v1/mcp/servers")
            
            assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_session_expiration(self, client):
        """Test session expiration."""
        with patch('app.services.auth.validate_session') as mock_validate:
            mock_validate.return_value = False
            
            client.headers.update({"X-Session-ID": "expired_session_id"})
            response = client.get("/v1/mcp/servers")
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_session_logout(self, client):
        """Test session logout."""
        with patch('app.services.auth.invalidate_session') as mock_invalidate:
            mock_invalidate.return_value = True
            
            response = client.post("/v1/auth/logout", headers={
                "X-Session-ID": "session_id"
            })
            
            assert response.status_code == status.HTTP_200_OK
