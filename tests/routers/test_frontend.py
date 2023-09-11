from http import HTTPStatus
from pathlib import Path

import pytest
from httpx import AsyncClient

from foxops.__main__ import FRONTEND_SUBDIRS, create_app

pytestmark = [pytest.mark.frontend]


@pytest.fixture(scope="module")
def frontend(tmp_path_factory: pytest.TempPathFactory):
    frontend_dir = tmp_path_factory.mktemp("frontend")

    for frontend_subdir in FRONTEND_SUBDIRS:
        (frontend_dir / frontend_subdir).mkdir(parents=True)
    (frontend_dir / "index.html").write_text("Hello World")

    return frontend_dir


@pytest.fixture
async def foxops_client_with_frontend(frontend: Path, monkeypatch):
    monkeypatch.setenv("FOXOPS_FRONTEND_DIST_DIR", str(frontend))
    monkeypatch.setenv("FOXOPS_STATIC_TOKEN", "dummy")

    app = create_app()

    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as ac:
        yield ac


async def test_serves_frontend_index_on_root(foxops_client_with_frontend: AsyncClient):
    # WHEN
    response = await foxops_client_with_frontend.get("/")

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
async def test_serves_frontend_files(path: str, foxops_client_with_frontend: AsyncClient):
    # WHEN
    response = await foxops_client_with_frontend.get(path)

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World"
