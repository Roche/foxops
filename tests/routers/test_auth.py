from fastapi import FastAPI, status
from httpx import AsyncClient

from foxops.dependencies import group_auth_scheme, user_auth_scheme


async def test_returns_err_if_authorization_header_is_missing(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test")

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Missing Authorization header"}


async def test_returns_err_if_authorization_header_is_empty(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": ""})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Missing Authorization header"}


async def test_returns_err_if_authorization_header_is_not_bearer(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "foobar"})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization header must start with 'Bearer ' followed by the token"}


async def test_returns_err_if_authorization_header_is_empty_bearer(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "Bearer"})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization header must start with 'Bearer ' followed by the token"}


async def test_returns_err_if_authorization_header_is_missing_bearer_token(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "Bearer "})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization header must start with 'Bearer ' followed by the token"}


async def test_returns_err_if_token_is_wrong(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "Bearer wrong"})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Token is invalid"}


async def test_allow_access_if_token_is_correct(app: FastAPI, static_api_token: str):
    app.dependency_overrides[group_auth_scheme] = lambda: None  # Disable group auth for this test
    app.dependency_overrides[user_auth_scheme] = lambda: None  # Disable user auth for this test

    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": f"Bearer {static_api_token}"})

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert response.text
