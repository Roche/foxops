from http import HTTPStatus

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def should_respond_with_current_version(unauthenticated_client: AsyncClient):
    # WHEN
    response = await unauthenticated_client.get("/version")

    # THEN
    assert response.status_code == HTTPStatus.OK
