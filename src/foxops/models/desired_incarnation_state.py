from pydantic import BaseModel

import foxops.engine as fengine


class DesiredIncarnationState(BaseModel):
    """A DesiredIncarnationState represents the desired state of an incarnation."""

    incarnation_repository: str
    target_directory: str = "."
    template_repository: str
    template_repository_version: str
    template_data: fengine.TemplateData
    automerge: bool = False

    class Config:
        orm_mode = True


class DesiredIncarnationStatePatch(BaseModel):
    """A DesiredIncarnationStatePatch represents the patch for the desired state of an incarnation."""

    template_repository_version: str | None = None
    template_data: fengine.TemplateData = {}
    automerge: bool
