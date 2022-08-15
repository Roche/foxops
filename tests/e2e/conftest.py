import base64
import os
import uuid
from urllib.parse import quote_plus

import pytest
from httpx import AsyncClient, Client

#: Holds settings for the GitLab test instance
GITLAB_ADDRESS = "http://127.0.0.1:5002/api/v4"
GITLAB_ADMIN_TOKEN = "ACCTEST1234567890123"


@pytest.fixture(scope="session")
def gitlab_test_address() -> str:
    return GITLAB_ADDRESS


@pytest.fixture(scope="session", name="gitlab_test_user_token")
def create_gitlab_test_user(test_run_id: str):
    client = Client(base_url=GITLAB_ADDRESS, headers={"PRIVATE-TOKEN": GITLAB_ADMIN_TOKEN})

    test_user_name = f"foxops-test-{test_run_id}"
    response = client.post(
        "/users",
        json={
            "name": test_user_name,
            "username": test_user_name,
            "password": test_user_name,
            "email": f"{test_user_name}@foxops.io",
            "skip_confirmation": True,
        },
    )
    response.raise_for_status()
    user_id = response.json()["id"]

    try:
        response = client.post(
            f"/users/{user_id}/personal_access_tokens",
            json={
                "name": test_user_name,
                "scopes": ["api", "read_repository", "write_repository"],
            },
        )
        response.raise_for_status()
        test_user_token = response.json()["token"]

        yield test_user_token
    finally:
        response = client.delete(f"/users/{user_id}")
        response.raise_for_status()


@pytest.fixture(scope="session", autouse=True)
def set_settings_env(gitlab_test_user_token: str, static_api_token: str):
    os.environ["FOXOPS_GITLAB_ADDRESS"] = GITLAB_ADDRESS
    os.environ["FOXOPS_GITLAB_TOKEN"] = gitlab_test_user_token
    os.environ["FOXOPS_STATIC_TOKEN"] = static_api_token


@pytest.fixture(name="gitlab_test_client")
async def create_test_gitlab_client(gitlab_test_user_token: str) -> AsyncClient:
    return AsyncClient(base_url=GITLAB_ADDRESS, headers={"PRIVATE-TOKEN": gitlab_test_user_token})


@pytest.fixture(name="empty_incarnation_gitlab_repository")
async def create_empty_incarnation_gitlab_repository(gitlab_test_client: AsyncClient):
    response = await gitlab_test_client.post("/projects", json={"name": f"incarnation-{str(uuid.uuid4())}"})
    response.raise_for_status()
    project = response.json()
    try:
        # TODO: considering returning `project`, annotated with a `TypedDict` for the fields
        #       required for the tests.
        yield project["path_with_namespace"]
    finally:
        (await gitlab_test_client.delete(f"/projects/{project['id']}")).raise_for_status()


@pytest.fixture(name="incarnation_gitlab_repository_in_v1")
async def create_incarnation_gitlab_repository_in_v1(
    api_client: AsyncClient,
    empty_incarnation_gitlab_repository: str,
    template_repository: str,
):
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    return empty_incarnation_gitlab_repository, str(incarnation["id"])


@pytest.fixture(name="template_repository")
async def create_template_gitlab_repository(gitlab_test_client: AsyncClient):
    response = await gitlab_test_client.post("/projects", json={"name": f"template-{str(uuid.uuid4())}"})
    response.raise_for_status()
    project = response.json()
    try:
        # TODO: considering returning `project`, annotated with a `TypedDict` for the fields
        #       required for the tests.
        (
            await gitlab_test_client.post(
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
"""
                    ).decode("utf-8"),
                    "commit_message": "Initial commit",
                    "branch": project["default_branch"],
                },
            )
        ).raise_for_status()

        # VERSION v1.0.0
        (
            await gitlab_test_client.post(
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
            await gitlab_test_client.post(
                f"/projects/{project['id']}/repository/tags",
                json={"tag_name": "v1.0.0", "ref": project["default_branch"]},
            )
        ).raise_for_status()

        # VERSION: v2.0.0
        (
            await gitlab_test_client.put(
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
            await gitlab_test_client.post(
                f"/projects/{project['id']}/repository/tags",
                json={"tag_name": "v2.0.0", "ref": project["default_branch"]},
            )
        ).raise_for_status()

        yield project["path_with_namespace"]
    finally:
        (await gitlab_test_client.delete(f"/projects/{project['id']}")).raise_for_status()
