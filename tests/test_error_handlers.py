import logging
import uuid
from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from foxops.dependencies import get_change_service


class _FailingChangeService:
    async def get_incarnation_with_details(self, incarnation_id: int):
        raise RuntimeError("boom")


@pytest.fixture
async def failing_client(app: FastAPI, static_api_token: str):
    app.dependency_overrides[get_change_service] = lambda: _FailingChangeService()

    # Starlette re-raises unhandled errors after the error handler has run. Turn that off so the
    # test sees the 500 response, the same as a real client would.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {static_api_token}"
        yield client


def _error_handler_events(caplog: pytest.LogCaptureFixture) -> list[dict]:
    return [r.msg for r in caplog.records if r.name == "foxops.error_handlers" and isinstance(r.msg, dict)]


async def test_unhandled_error_is_logged_with_request_context(failing_client: AsyncClient, caplog):
    with caplog.at_level(logging.ERROR, logger="foxops.error_handlers"):
        response = await failing_client.get("/api/incarnations/42")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    (event,) = _error_handler_events(caplog)
    assert event["event"] == "boom"
    assert event["method"] == "GET"
    assert event["path"] == "/api/incarnations/42"
    assert event["incarnation_id"] == "42"
    assert uuid.UUID(event["request_id"])
