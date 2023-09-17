import uuid
from typing import Self
from urllib.parse import urlparse

import pytest
from httpx import Client, HTTPStatusError, Timeout
from pydantic import SecretStr, model_validator, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitlabTestSettings(BaseSettings):
    address: str = "https://gitlab.com"

    @field_validator("address", mode="after")
    @classmethod
    def check_address_does_not_include_apiversion(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.path:
            raise ValueError("The address must not include a path (especially /api/v4)")

        return v

    # either a username/password or a token must be provided
    username: str | None = None
    password: SecretStr | None = None

    token: SecretStr | None = None

    @model_validator(mode="after")
    def check_credentials_or_token_are_provided(self) -> Self:
        if self.username or self.password:
            if self.username and self.password:
                return self
            else:
                raise ValueError("Either a username or a password was provided, but not both. Please provide both.")
        elif self.token:
            return self

        raise ValueError("Either a username and password must be provided, or a token")

    root_group_id: int | None = None

    model_config = SettingsConfigDict(env_prefix="FOXOPS_TESTS_GITLAB_", env_file=".env.test")


@pytest.fixture(scope="session")
def gitlab_address(gitlab_settings: GitlabTestSettings) -> str:
    return gitlab_settings.address


@pytest.fixture(scope="session")
def gitlab_settings():
    try:
        gitlab_settings = GitlabTestSettings()
    except ValidationError:
        pytest.skip("No information provided about a Gitlab instance that can be used for tests "
                    "(via FOXOPS_TESTS_GITLAB_* environment variables). Skipping.")

    return gitlab_settings


@pytest.fixture(scope="session")
def gitlab_access_token(gitlab_settings: GitlabTestSettings) -> str:
    """Get an access token for the Gitlab instance that can be used for API calls."""
    if gitlab_settings.token:
        return gitlab_settings.token.get_secret_value()

    assert gitlab_settings.username is not None
    assert gitlab_settings.password is not None

    client = Client(base_url=gitlab_settings.address, timeout=Timeout(120))

    response = client.post(
        "/oauth/token",
        data={
            "grant_type": "password",
            "username": gitlab_settings.username,
            "password": gitlab_settings.password.get_secret_value(),
        },
    )
    response.raise_for_status()

    return response.json()["access_token"]


@pytest.fixture(scope="session")
def gitlab_client(gitlab_address: str, gitlab_access_token: str) -> Client:
    return Client(
        base_url=gitlab_address + "/api/v4",
        headers={"Authorization": f"Bearer {gitlab_access_token}"},
        timeout=Timeout(120),
    )


@pytest.fixture(scope="session")
def gitlab_root_group_id(gitlab_settings: GitlabTestSettings):
    return gitlab_settings.root_group_id


@pytest.fixture(scope="session")
def gitlab_project_factory(gitlab_client: Client, gitlab_root_group_id: int):
    def _factory(name: str, initialize_with_readme: bool = False):
        suffix = str(uuid.uuid4())[:8]
        response = gitlab_client.post(
            "/projects",
            json={
                "name": f"{name}-{suffix}",
                "namespace_id": gitlab_root_group_id,
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
