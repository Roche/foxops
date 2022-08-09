from pathlib import Path

from pydantic import BaseModel, Field

import foxops.engine as fengine


class DesiredIncarnationStateConfig(BaseModel):
    gitlab_project: Path = Field(..., description="The full GitLab path to the incarnation project")
    target_directory: Path = Field(Path("."), description="The target incarnation directory within the repository")
    template_repository: str = Field(..., description="The URL to the template repository")
    template_repository_version: str = Field(
        ..., description="The version of the template repository as a Git revision"
    )
    template_data: fengine.TemplateData = Field(..., description="The template data to use when rendering the template")
    automerge: bool = Field(
        False,
        description="Automatically merge the created Merge Request. It won't wait until the merge is complete.",
    )

    class Config:
        allow_mutation = False
