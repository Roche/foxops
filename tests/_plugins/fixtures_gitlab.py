import uuid

import pytest
from httpx import Client, HTTPStatusError, Timeout
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitlabTestSettings(BaseSettings):
    address: str = "https://gitlab.com"
    token: SecretStr | None = None

    # "foxops-e2e" group on gitlab.com
    root_group_id: int = 73622910

    model_config = SettingsConfigDict(env_prefix="FOXOPS_TESTS_GITLAB_", env_file=".env.test")


@pytest.fixture(scope="session")
def gitlab_settings():
    gitlab_settings = GitlabTestSettings()
    if gitlab_settings.token is None:
        pytest.skip(
            f"No Gitlab token provided (via FOXOPS_TESTS_GITLAB_TOKEN environment variable) "
            f"to access group '{gitlab_settings.root_group_id}' on '{gitlab_settings.address}'"
        )

    return gitlab_settings


@pytest.fixture(scope="session")
def gitlab_client(gitlab_settings: GitlabTestSettings) -> Client:
    assert gitlab_settings.token is not None

    return Client(
        base_url=gitlab_settings.address + "/api/v4",
        headers={"PRIVATE-TOKEN": gitlab_settings.token.get_secret_value()},
        timeout=Timeout(120),
    )


@pytest.fixture(scope="session")
def gitlab_project_factory(gitlab_client: Client, gitlab_settings: GitlabTestSettings):
    def _factory(name: str, initialize_with_readme: bool = False):
        suffix = str(uuid.uuid4())[:8]
        response = gitlab_client.post(
            "/projects",
            json={
                "name": f"{name}-{suffix}",
                "namespace_id": gitlab_settings.root_group_id,
                "initialize_with_readme": initialize_with_readme,
            },
        )
        response.raise_for_status()
        project = response.json()

        created_project_ids.append(project["id"])

        return project

    created_project_ids: list[int] = []

    yield _factory

    # cleanup all projects that were created during the test, ignoring those that were already remove in the test
    for project_id in created_project_ids:
        response = gitlab_client.delete(f"/projects/{project_id}")
        try:
            response.raise_for_status()
        except HTTPStatusError as e:
            if e.response.status_code != 404:
                raise
