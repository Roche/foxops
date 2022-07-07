import base64
import typing
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_fixed

ProjectIdentifier = typing.Union[str, Path, int]


class GitlabException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class GitlabNotFoundException(GitlabException):
    def __init__(self, message: str):
        super().__init__(404, message)


class AsyncGitlabClient:
    def __init__(self, token: str, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = aiohttp.ClientSession(headers={"PRIVATE-TOKEN": token})

    async def __aenter__(self) -> "AsyncGitlabClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.session.close()

    async def _request(
        self,
        method: str,
        url: str,
        json: Any = None,
        data: Any = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        url = self.base_url + url
        async with self.session.request(
            method, url, params=params, json=json, data=data
        ) as response:
            if 200 <= response.status < 300:
                if response.content_type == "application/json":
                    return await response.json()

            data = await response.json()
            if response.status == 404:
                message = data.get("message", data.get("error", "Unknown error"))
                raise GitlabNotFoundException(message)
            raise GitlabException(response.status, data["message"])

    async def _get(self, url: str, params: dict[str, str] | None = None) -> Any:
        return await self._request("GET", url, params=params)

    async def _post(
        self,
        url: str,
        json: Any = None,
        data: Any = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        return await self._request("POST", url, json=json, data=data, params=params)

    async def _put(
        self,
        url: str,
        json: Any = None,
        data: Any = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        return await self._request("PUT", url, json=json, data=data, params=params)

    async def _delete(self, url: str, params: dict[str, str] | None = None) -> Any:
        return await self._request("DELETE", url, params=params)

    async def group_get(self, id_: str | int):
        group_id = quote_plus(str(id_))
        return await self._get(f"/groups/{group_id}")

    async def project_get(self, id_: ProjectIdentifier):
        project_id = quote_plus(str(id_))
        return await self._get(f"/projects/{project_id}")

    async def project_merge_requests_create(
        self,
        id_: ProjectIdentifier,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
    ):
        return await self._post(
            f"/projects/{quote_plus(str(id_))}/merge_requests",
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "remove_source_branch": True,
                "description": description,
            },
        )

    async def automerge_merge_request(
        self,
        id_: ProjectIdentifier,
        merge_request_iid: int,
        timeout: timedelta | None = None,
    ):
        """Automerge the given Merge Request.

        It will immediately merge if possible, otherwise when the pipeline succeeds.
        There won't be made any rebases or similar nor wait for the actual merge to happen.
        """
        if timeout is None:
            timeout = timedelta(minutes=5)

        @retry(
            retry=retry_if_exception_type(GitlabException),
            stop=stop_after_delay(timeout.total_seconds()),
            wait=wait_fixed(1),
        )
        async def __merge():
            merge_request = await self._get(
                f"/projects/{quote_plus(str(id_))}/merge_requests/{merge_request_iid}"
            )
            has_pipeline = merge_request.get("pipeline", None) is not None
            data = {"merge_when_pipeline_succeeds": True} if has_pipeline else None
            return await self._put(
                f"/projects/{quote_plus(str(id_))}/merge_requests/{merge_request_iid}/merge",
                json=data,
            )

        return await __merge()

    async def project_merge_requests_list(
        self,
        id_: ProjectIdentifier,
        state: str | None = None,
        source_branch: str | None = None,
    ):
        params = {}
        if state is not None:
            params["state"] = state
        if source_branch is not None:
            params["source_branch"] = source_branch

        return await self._get(
            f"/projects/{quote_plus(str(id_))}/merge_requests", params=params
        )

    async def project_repository_branches_create(
        self, id_: ProjectIdentifier, branch: str, ref: str
    ):
        await self._post(
            f"/projects/{quote_plus(str(id_))}/repository/branches",
            params={"branch": branch, "ref": ref},
        )

    async def project_repository_branches_list(
        self, id_: ProjectIdentifier, search: str | None = None
    ):
        params = {}
        if search is not None:
            params["search"] = search

        return await self._get(
            f"/projects/{quote_plus(str(id_))}/repository/branches", params=params
        )

    async def project_repository_branches_delete(
        self, id_: ProjectIdentifier, branch: str
    ):
        branch = quote_plus(branch)
        await self._delete(
            f"/projects/{quote_plus(str(id_))}/repository/branches/{branch}"
        )

    async def project_repository_files_get_content(
        self, id_: ProjectIdentifier, branch: str, filepath: str | Path
    ) -> bytes:
        response = await self._get(
            f"/projects/{quote_plus(str(id_))}/repository/files/{quote_plus(str(filepath))}",
            params={"ref": branch},
        )

        if (encoding := response.get("encoding")) != "base64":
            raise ValueError(
                f"Received file content was not base64 encoded. Instead: {encoding}"
            )

        return base64.b64decode(response["content"])
