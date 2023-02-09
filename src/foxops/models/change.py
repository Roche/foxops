from datetime import datetime

from pydantic import BaseModel

from foxops.hosters.types import MergeRequestStatus


class Change(BaseModel):
    id: int

    incarnation_id: int
    revision: int  # highest number is the latest change that was performed

    requested_version: str
    requested_data: dict[str, str]

    created_at: datetime


class ChangeWithDirectCommit(Change):
    commit_sha: str


class ChangeWithMergeRequest(Change):
    merge_request_id: str
    merge_request_status: MergeRequestStatus

    # branch that was originally created for the merge request
    branch_name: str

    # commit that was made to the update branch
    commit_sha: str
    # commit that was created on the main branch as a result of the merge
    # in case of fast-forward merges, this is identical to the commit_sha
    merge_commit_sha: str
