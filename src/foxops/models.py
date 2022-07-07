from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

from foxops.engine import IncarnationState, TemplateData

yaml = YAML(typ="safe")


class DesiredIncarnationStateConfig(BaseModel):
    gitlab_project: Path = Field(
        ..., description="The full GitLab path to the incarnation project"
    )
    target_directory: Path = Field(
        Path("."), description="The target incarnation directory within the repository"
    )
    template_repository: str = Field(
        ..., description="The URL to the template repository"
    )
    template_repository_version: str = Field(
        ..., description="The version of the template repository as a Git revision"
    )
    template_data: TemplateData = Field(
        ..., description="The template data to use when rendering the template"
    )
    automerge: bool = Field(
        False,
        description="Automatically merge the created Merge Request. It won't wait until the merge is complete.",
    )

    class Config:
        allow_mutation = False


class IncarnationRemoteGitRepositoryState(BaseModel):
    """Represents a remote Git repository that contains one or multiple incarnations."""

    # FIXME(TF): this is the only thing GitLab specific here.
    #            We might want to get rid of that ...
    gitlab_project_id: int
    remote_url: str
    default_branch: str
    incarnation_directory: Path
    incarnation_state: Optional[IncarnationState]

    class Config:
        allow_mutation = False
