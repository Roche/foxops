from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.api]


async def test_returns_err_with_404_for_unknown_uri(api_client: AsyncClient):
    # WHEN
    response = await api_client.get("/unknown")

    # THEN
    assert response.status_code == HTTPStatus.NOT_FOUND
