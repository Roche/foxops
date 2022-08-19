import pytest
from fastapi import Depends, FastAPI, status
from httpx import AsyncClient

from foxops.dependencies import static_token_auth_scheme


@pytest.mark.asyncio
async def should_err_if_authorization_header_is_missing(app: FastAPI):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test")

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Missing Authorization header"}


@pytest.mark.asyncio
async def should_err_if_authorization_header_is_empty(app: FastAPI):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test", headers={"Authorization": ""})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Missing Authorization header"}


@pytest.mark.asyncio
async def should_err_if_authorization_header_is_not_bearer(app: FastAPI):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test", headers={"Authorization": "foobar"})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization header must start with 'Bearer ' followed by the token"}


@pytest.mark.asyncio
async def should_err_if_authorization_header_is_empty_bearer(app: FastAPI):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test", headers={"Authorization": "Bearer"})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization header must start with 'Bearer ' followed by the token"}


@pytest.mark.asyncio
async def should_err_if_authorization_header_is_missing_bearer_token(app: FastAPI):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test", headers={"Authorization": "Bearer "})

    # THEN
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization header must start with 'Bearer ' followed by the token"}


@pytest.mark.asyncio
async def should_err_if_token_is_wrong(app: FastAPI):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test", headers={"Authorization": "Bearer wrong"})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Token is invalid"}


@pytest.mark.asyncio
async def should_allow_access_if_token_is_correct(app: FastAPI, static_api_token: str):
    # GIVEN
    @app.get("/api/test")
    async def _(_=Depends(static_token_auth_scheme)):
        return "OK"

    # WHEN
    async with AsyncClient(app=app, base_url="http://test/api", follow_redirects=True) as client:
        response = await client.get("/test", headers={"Authorization": f"Bearer {static_api_token}"})

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert response.text == '"OK"'
