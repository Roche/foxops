from http import HTTPStatus

from httpx import AsyncClient


async def test_returns_current_version(unauthenticated_client: AsyncClient):
    # WHEN
    response = await unauthenticated_client.get("/version")

    # THEN
    assert response.status_code == HTTPStatus.OK
