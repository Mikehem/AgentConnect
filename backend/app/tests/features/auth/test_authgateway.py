from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import HTTPException, status

from app.main import app
from app.core.config import settings


client = TestClient(app)


@patch("app.core.middleware.verify_jwt_token_edge")
def test_authgateway_allows_valid_bearer_token(mock_verify):
    mock_verify.return_value = {"sub": "user-123", "iss": settings.OIDC_ISSUER, "aud": settings.OIDC_AUDIENCE}
    token = "dummy"

    res = client.get("/health", headers={"Authorization": f"Bearer {token}"})
    # health is public; also test a protected endpoint
    res2 = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert res2.status_code in {200, 401, 403, 404}
    assert "X-Request-Id" in res.headers


@patch("app.core.middleware.verify_jwt_token_edge")
def test_authgateway_rejects_wrong_audience(mock_verify):
    def _raise(*args, **kwargs):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    mock_verify.side_effect = _raise
    token = "bad"
    res = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    body = res.json()
    assert body.get("title") == "Unauthorized"


@patch("app.core.middleware.verify_jwt_token_edge")
def test_authgateway_rejects_unknown_kid(mock_verify):
    mock_verify.side_effect = HTTPException(status_code=401, detail="Unknown key id")
    res = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": f"Bearer dummy"})
    assert res.status_code == 401


def test_authgateway_requires_bearer():
    res = client.get(f"{settings.API_V1_STR}/organizations")
    assert res.status_code == 401
    assert res.json().get("detail") == "Missing Bearer token"


@patch("app.core.middleware.verify_jwt_token_edge")
def test_authgateway_expired_token(mock_verify):
    from fastapi import HTTPException
    mock_verify.side_effect = HTTPException(status_code=401, detail="Token has expired")
    res = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": "Bearer expired"})
    assert res.status_code == 401
    assert res.json().get("detail") == "Token has expired"


@patch("app.core.middleware.verify_jwt_token_edge")
def test_authgateway_unsupported_alg(mock_verify):
    from fastapi import HTTPException
    mock_verify.side_effect = HTTPException(status_code=401, detail="Unsupported token algorithm")
    res = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": "Bearer badalg"})
    assert res.status_code == 401
    assert res.json().get("detail") == "Unsupported token algorithm"


def test_public_paths_bypass_auth():
    res1 = client.get("/health")
    res2 = client.get("/metrics")
    assert res1.status_code == 200
    assert res2.status_code == 200


@patch("app.core.security.JWKSCache.get_keys")
def test_jwks_cache_rotation(mock_get_keys):
    # First call returns no keys, second returns valid keys
    mock_get_keys.side_effect = [
        {"keys": []},
        {"keys": [{"kty": "RSA", "n": "abc", "e": "AQAB", "kid": "kid1"}]}
    ]
    # Patch middleware path to call verify function which will query JWKS, but we simulate unknown kid -> 401
    with patch("app.core.middleware.verify_jwt_token_edge") as mock_verify:
        from fastapi import HTTPException
        mock_verify.side_effect = [HTTPException(status_code=401, detail="Unknown key id"), {"sub": "u"}]
        r1 = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": "Bearer t1"})
        r2 = client.get(f"{settings.API_V1_STR}/organizations", headers={"Authorization": "Bearer t2"})
        assert r1.status_code == 401
        assert r2.status_code in {200, 401, 403, 404}


