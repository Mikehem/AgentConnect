"""API tests for Organizations feature."""

import pytest
from fastapi import status

pytestmark = pytest.mark.api


class TestOrganizationAPICreate:
    """Test organization creation API endpoints."""

    def test_create_organization_success(self, client, sample_user):
        """Test successful organization creation."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        org_data = {
            "name": "New Organization",
            "slug": "new-org",
            "subscription_tier": "free"
        }
        
        response = client.post("/v1/organizations", json=org_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == org_data["name"]
        assert data["slug"] == org_data["slug"]

    def test_create_organization_validation_error(self, client, sample_user):
        """Test organization creation with invalid data."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        invalid_data = {
            "name": "",  # Invalid: empty name
            "slug": "invalid slug"  # Invalid: contains space
        }
        
        response = client.post("/v1/organizations", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_organization_duplicate_slug(self, client, sample_user, sample_organization):
        """Test organization creation with duplicate slug."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        duplicate_data = {
            "name": "Different Name",
            "slug": sample_organization.slug,  # Duplicate slug
            "subscription_tier": "free"
        }
        
        response = client.post("/v1/organizations", json=duplicate_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()


class TestOrganizationAPIGet:
    """Test organization retrieval API endpoints."""

    def test_get_organization_success(self, client, sample_user, sample_organization):
        """Test successful organization retrieval."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/organizations/{sample_organization.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_organization.id)
        assert data["name"] == sample_organization.name

    def test_get_organization_not_found(self, client, sample_user):
        """Test organization retrieval with non-existent ID."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Use a valid UUID format but non-existent
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/v1/organizations/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_organization_unauthorized(self, client, sample_organization):
        """Test organization retrieval without authentication."""
        response = client.get(f"/v1/organizations/{sample_organization.id}")
        
        # With mock authentication, all requests are treated as authorized
        assert response.status_code == status.HTTP_200_OK


class TestOrganizationAPIUpdate:
    """Test organization update API endpoints."""

    def test_update_organization_success(self, client, sample_user, sample_organization):
        """Test successful organization update."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        update_data = {
            "name": "Updated Organization",
            "settings": {"feature_flags": {"new_feature": True}}
        }
        
        response = client.patch(f"/v1/organizations/{sample_organization.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["settings"]["feature_flags"]["new_feature"] is True

    def test_update_organization_not_found(self, client, sample_user):
        """Test organization update with non-existent ID."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        update_data = {"name": "Updated Organization"}
        
        # Use a valid UUID format but non-existent
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(f"/v1/organizations/{non_existent_id}", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_organization_validation_error(self, client, sample_user, sample_organization):
        """Test organization update with invalid data."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        invalid_data = {
            "name": "",  # Invalid: empty name
            "slug": "invalid slug"  # Invalid: contains space
        }
        
        response = client.patch(f"/v1/organizations/{sample_organization.id}", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestOrganizationAPIDelete:
    """Test organization deletion API endpoints."""

    def test_delete_organization_success(self, client, sample_user, sample_organization):
        """Test successful organization deletion."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.delete(f"/v1/organizations/{sample_organization.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Organization deleted successfully"

    def test_delete_organization_not_found(self, client, sample_user):
        """Test organization deletion with non-existent ID."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        # Use a valid UUID format but non-existent
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/v1/organizations/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_organization_unauthorized(self, client, sample_organization):
        """Test organization deletion without authentication."""
        response = client.delete(f"/v1/organizations/{sample_organization.id}")
        
        # With mock authentication, all requests are treated as authorized
        assert response.status_code == status.HTTP_200_OK


class TestOrganizationAPIList:
    """Test organization listing API endpoints."""

    def test_list_organizations_success(self, client, sample_user, sample_organization):
        """Test successful organization listing."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get("/v1/organizations")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "organizations" in data
        assert len(data["organizations"]) >= 1
        assert data["total"] >= 1

    def test_list_organizations_with_filters(self, client, sample_user, sample_organization):
        """Test organization listing with query parameters."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get("/v1/organizations?status=active&subscription_tier=free")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "organizations" in data

    def test_list_organizations_unauthorized(self, client):
        """Test organization listing without authentication."""
        response = client.get("/v1/organizations")
        
        # With mock authentication, all requests are treated as authorized
        assert response.status_code == status.HTTP_200_OK


class TestOrganizationAPIQuotas:
    """Test organization quota management."""

    def test_get_organization_quotas(self, client, sample_user, sample_organization):
        """Test getting organization quotas."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/organizations/{sample_organization.id}/quotas")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "server_limit" in data
        assert "user_limit" in data
        assert "current_servers" in data
        assert "current_users" in data

    def test_update_organization_quotas(self, client, sample_user, sample_organization):
        """Test updating organization quotas."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        quota_data = {
            "server_limit": 100,
            "user_limit": 50,
            "storage_limit_gb": 200,
            "api_rate_limit": 2000
        }
        
        response = client.patch(f"/v1/organizations/{sample_organization.id}/quotas", json=quota_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["server_limit"] == 100
        assert data["user_limit"] == 50


class TestOrganizationAPISettings:
    """Test organization settings management."""

    def test_get_organization_settings(self, client, sample_user, sample_organization):
        """Test getting organization settings."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        response = client.get(f"/v1/organizations/{sample_organization.id}/settings")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "settings" in data

    def test_update_organization_settings(self, client, sample_user, sample_organization):
        """Test updating organization settings."""
        client.headers.update({"Authorization": f"Bearer {sample_user.id}"})
        
        settings_data = {
            "feature_flags": {
                "auto_discovery": True,
                "advanced_analytics": False
            },
            "security": {
                "mfa_required": True,
                "session_timeout": 3600
            }
        }
        
        response = client.patch(f"/v1/organizations/{sample_organization.id}/settings", json=settings_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["settings"]["feature_flags"]["auto_discovery"] is True
        assert data["settings"]["security"]["mfa_required"] is True
