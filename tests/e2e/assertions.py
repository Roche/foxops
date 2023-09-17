from urllib.parse import quote_plus

from httpx import AsyncClient, Client


def assert_file_in_repository(
    gitlab_client: Client,
    repository: str,
    file_path: str,
    file_content: str,
    branch: str | None = None,
):
    params = {}
    if branch is not None:
        params["ref"] = branch

    response = gitlab_client.get(
        f"/projects/{quote_plus(repository)}/repository/files/{quote_plus(file_path)}/raw",
        params=params,
    )
    response.raise_for_status()
    assert response.text == file_content


async def assert_initialization_merge_request_exists(
    gitlab_test_client: AsyncClient,
    repository: str,
) -> str:
    params = {"state": "opened", "target_branch": "main"}
    response = await gitlab_test_client.get(f"/projects/{quote_plus(repository)}/merge_requests", params=params)
    response.raise_for_status()
    merge_requests = response.json()

    merge_request = next(
        (m for m in merge_requests if m["source_branch"].startswith("foxops/initialize-to-")),
        None,
    )
    assert (
        merge_request is not None
    ), f"No initialization merge request found, merge requests available: {merge_requests}"

    assert merge_request["title"].startswith("Initialize to")
    return merge_request["source_branch"]


def assert_update_merge_request_exists(
    gitlab_client: Client,
    repository: str,
):
    params = {"state": "opened", "target_branch": "main"}
    response = gitlab_client.get(f"/projects/{quote_plus(repository)}/merge_requests", params=params)
    response.raise_for_status()
    merge_requests = response.json()

    merge_request = next(
        (m for m in merge_requests if m["source_branch"].startswith("foxops/update-to-")),
        None,
    )
    assert merge_request is not None, f"No update merge request found, merge requests available: {merge_requests}"

    assert merge_request["title"].startswith("Update to")
    return merge_request["source_branch"]


def assert_update_merge_request_with_conflicts_exists(
    gitlab_client: Client, repository: str, files_with_conflicts: list[str]
):
    params = {"state": "opened", "target_branch": "main"}
    response = gitlab_client.get(f"/projects/{quote_plus(repository)}/merge_requests", params=params)
    response.raise_for_status()
    merge_requests = response.json()

    merge_request = next(
        (m for m in merge_requests if m["source_branch"].startswith("foxops/update-to-")),
        None,
    )
    assert merge_request is not None, f"No update merge request found, merge requests available: {merge_requests}"

    assert merge_request["title"].startswith("🚧 - CONFLICT: Update to")

    # Assert that there is a rejection file in the Merge Request changes
    response = gitlab_client.get(f"/projects/{quote_plus(repository)}/merge_requests/{merge_request['iid']}/changes")
    response.raise_for_status()

    changes = response.json()["changes"]

    for f in files_with_conflicts:
        assert any(
            c["new_path"] == f"{f}.rej" and c["new_file"] for c in changes
        ), f"No rejection file found for file {f}. Changes: {changes}. Merge request: {merge_request}"

    assert all(f"- {f}" in merge_request["description"] for f in files_with_conflicts)

    return merge_request["source_branch"]
