from fastapi import FastAPI, status
from httpx import AsyncClient


async def should_err_if_authorization_header_is_missing(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test")

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Missing Authorization header"}


async def should_err_if_authorization_header_is_empty(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": ""})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Missing Authorization header"}


async def should_err_if_authorization_header_is_not_bearer(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "foobar"})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Token scheme must be Bearer"}


async def should_err_if_authorization_header_is_empty_bearer(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "Bearer"})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Missing token"}


async def should_err_if_authorization_header_is_missing_bearer_token(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "Bearer "})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Missing token"}


async def should_err_if_token_is_wrong(app: FastAPI):
    # WHEN
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/auth/test", headers={"Authorization": "Bearer wrong"})

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not enough segments"}


async def should_fail_if_client_unauthenticated(unauthenticated_client: AsyncClient):
    # WHEN
    response = await unauthenticated_client.get("/auth/test")

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Missing Authorization header"}


async def should_fail_if_client_misauthenticated(misauthenticated_client: AsyncClient):
    # WHEN
    response = await misauthenticated_client.get("/auth/test")

    # THEN
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid TEST token"}


async def should_allow_access_if_token_is_correct(authenticated_client: AsyncClient):
    # WHEN
    response = await authenticated_client.get("/auth/test")

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert response.text == "OK"
