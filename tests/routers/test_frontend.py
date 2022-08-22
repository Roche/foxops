from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.frontend]


async def should_serve_frontend_index_on_root(unauthenticated_client: AsyncClient):
    # WHEN
    response = await unauthenticated_client.get("/")

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World"


@pytest.mark.parametrize(
    "path",
    [
        "/index.html",
        "/incarnations",
        "/settings",
        "/foo",
        "/bar",
    ],
)
async def should_serve_frontend_index_on_any_url(path: str, unauthenticated_client: AsyncClient):
    # WHEN
    response = await unauthenticated_client.get(path)

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World"
