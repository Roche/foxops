import base64
from typing import Any, Awaitable, Callable, NamedTuple
from urllib.parse import quote_plus

import pytest
from httpx import AsyncClient, Client

from foxops.__main__ import create_app
from foxops.engine.models.template_config import TemplateConfig

TemplateVersion = NamedTuple(
    "TemplateVersion",
    [
        ("version", str),
        ("config", TemplateConfig),
        ("files", dict[str, bytes]),
    ],
)

TemplateFactory = Callable[[list[TemplateVersion]], str]


@pytest.fixture(scope="session")
def gitlab_template_factory(gitlab_client: Client, gitlab_project_factory: Callable[[str], dict]) -> TemplateFactory:
    def _create_template(versions: list[TemplateVersion]) -> str:
        project = gitlab_project_factory("template")

        for version in versions:
            (
                gitlab_client.post(
                    f"/projects/{project['id']}/repository/files/{quote_plus('fengine.yaml')}",
                    json={
                        "encoding": "base64",
                        "content": base64.b64encode(version.config.yaml().encode()).decode(),
                        "commit_message": "Initial commit",
                        "branch": project["default_branch"],
                    },
                )
            ).raise_for_status()

            for path, content in version.files.items():
                (
                    gitlab_client.post(
                        f"/projects/{project['id']}/repository/files/{quote_plus('template/' + path)}",
                        json={
                            "encoding": "base64",
                            "content": base64.b64encode(content).decode(),
                            "commit_message": "commitmessage",
                            "branch": project["default_branch"],
                        },
                    )
                ).raise_for_status()

            (
                gitlab_client.post(
                    f"/projects/{project['id']}/repository/tags",
                    json={"tag_name": version.version, "ref": project["default_branch"]},
                )
            ).raise_for_status()

        return project["path_with_namespace"]

    return _create_template


@pytest.fixture(scope="session")
def gitlab_template_repository(gitlab_client: Client, gitlab_project_factory: Callable[[str], dict]) -> str:
    project = gitlab_project_factory("template")

    (
        gitlab_client.post(
            f"/projects/{project['id']}/repository/files/{quote_plus('fengine.yaml')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(
                    b"""
variables:
    name:
        type: str
        description: The name of the person

    age:
        type: int
        description: The age of the person

    country:
        type: str
        description: The country of the person
        default: Switzerland
"""
                ).decode("utf-8"),
                "commit_message": "Initial commit",
                "branch": project["default_branch"],
            },
        )
    ).raise_for_status()

    # VERSION v1.0.0
    (
        gitlab_client.post(
            f"/projects/{project['id']}/repository/files/{quote_plus('template/README.md')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"{{ name }} is of age {{ age }}").decode("utf-8"),
                "commit_message": "Add template README",
                "branch": project["default_branch"],
            },
        )
    ).raise_for_status()
    (
        gitlab_client.post(
            f"/projects/{project['id']}/repository/tags",
            json={"tag_name": "v1.0.0", "ref": project["default_branch"]},
        )
    ).raise_for_status()

    # VERSION: v2.0.0
    (
        gitlab_client.put(
            f"/projects/{project['id']}/repository/files/{quote_plus('template/README.md')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"Hello {{ name }}, age: {{ age }}").decode("utf-8"),
                "commit_message": "Change template README",
                "branch": project["default_branch"],
            },
        )
    ).raise_for_status()
    (
        gitlab_client.post(
            f"/projects/{project['id']}/repository/tags",
            json={"tag_name": "v2.0.0", "ref": project["default_branch"]},
        )
    ).raise_for_status()

    return project["path_with_namespace"]


@pytest.fixture
async def foxops_client(gitlab_address: str, gitlab_access_token: str, foxops_database: str, monkeypatch):
    static_token = "test-token"

    monkeypatch.setenv("FOXOPS_DATABASE_URL", foxops_database)
    monkeypatch.setenv("FOXOPS_HOSTER_TYPE", "gitlab")
    monkeypatch.setenv("FOXOPS_HOSTER_GITLAB_ADDRESS", gitlab_address)
    monkeypatch.setenv("FOXOPS_HOSTER_GITLAB_TOKEN", gitlab_access_token)
    monkeypatch.setenv("FOXOPS_STATIC_TOKEN", static_token)
    monkeypatch.setenv("FOXOPS_LOG_LEVEL", "DEBUG")

    async with AsyncClient(
        app=create_app(),
        base_url="http://test",
    ) as client:
        client.headers["Authorization"] = f"Bearer {static_token}"

        yield client


@pytest.fixture
async def gitlab_incarnation_repository_in_v1(
    foxops_client: AsyncClient,
    gitlab_project_factory: Callable[[str], dict],
    gitlab_template_repository: str,
):
    incarnation_repo = gitlab_project_factory("incarnation")["path_with_namespace"]

    response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": incarnation_repo,
            "template_repository": gitlab_template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    return incarnation_repo, str(incarnation["id"])


IncarnationFactory = Callable[[list[TemplateVersion], dict[str, Any]], Awaitable[tuple[str, str]]]


@pytest.fixture
def gitlab_incarnation_factory(
    foxops_client: AsyncClient,
    gitlab_project_factory: Callable[[str], dict],
    gitlab_template_factory: TemplateFactory,
) -> IncarnationFactory:
    async def _create_incarnation(
        template_versions: list[TemplateVersion],
        template_data: dict[str, Any],
    ) -> tuple[str, str]:
        template_repo = gitlab_template_factory(template_versions)
        incarnation_repo = gitlab_project_factory("incarnation")["path_with_namespace"]

        response = await foxops_client.post(
            "/api/incarnations",
            json={
                "incarnation_repository": incarnation_repo,
                "template_repository": template_repo,
                "template_repository_version": template_versions[-1].version,
                "template_data": template_data,
            },
        )
        response.raise_for_status()
        incarnation = response.json()

        return incarnation_repo, str(incarnation["id"])

    return _create_incarnation
