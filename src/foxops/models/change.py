from datetime import datetime

from pydantic import BaseModel

from foxops.engine import TemplateData
from foxops.hosters.types import MergeRequestStatus


class Change(BaseModel):
    id: int

    incarnation_id: int
    revision: int  # highest number is the latest change that was performed

    requested_version: str
    requested_version_hash: str
    requested_data: TemplateData

    created_at: datetime
    commit_sha: str


class ChangeWithMergeRequest(Change):
    merge_request_id: str
    merge_request_branch_name: str

    merge_request_status: MergeRequestStatus
