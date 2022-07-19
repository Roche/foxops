# type: ignore

from collections import namedtuple

from foxops.external.gitlab import AsyncGitlabClient, ProjectIdentifier, quote_plus

#: Holds the GitLab base group id
GITLAB_BASE_GROUP_ID = 18289


GitlabTestGroup = namedtuple("GitlabTestGroup", ["id", "path"])


class ExtendedAsyncGitlabClient(AsyncGitlabClient):
    async def project_create(
        self, group_id: int, path: str, initialize_with_readme: bool
    ):
        return await self._post(
            "/projects",
            json={
                "path": path,
                "namespace_id": group_id,
                "initialize_with_readme": initialize_with_readme,
                "default_branch": "main",
            },
        )

    async def project_delete(self, project_id: int):
        return await self._delete(f"/projects/{project_id}")

    async def tag_create(self, project_id: int, tag_name: str, ref: str):
        return await self._post(
            f"/projects/{project_id}/repository/tags",
            json={"tag_name": tag_name, "ref": ref},
        )

    async def group_create(self, group_name: str, group_path: str, parent_id: int):
        return await self._post(
            "/groups",
            json={"name": group_name, "path": group_path, "parent_id": parent_id},
        )

    async def group_delete(self, group_id: int):
        return await self._delete(f"/groups/{group_id}")

    async def project_merge_request_changes(
        self, id_: ProjectIdentifier, merge_request_iid: int
    ):
        return await self._get(
            f"/projects/{quote_plus(str(id_))}/merge_requests/{merge_request_iid}/changes"
        )

    async def get_branch_revision(self, id_: ProjectIdentifier, branch: str) -> str:
        branch_data = await self._get(
            f"/projects/{quote_plus(str(id_))}/repository/branches/{branch}"
        )
        return branch_data["commit"]["id"]
