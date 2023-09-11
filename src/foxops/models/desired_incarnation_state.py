from pydantic import BaseModel, ConfigDict

import foxops.engine as fengine


class DesiredIncarnationState(BaseModel):
    """A DesiredIncarnationState represents the desired state of an incarnation."""

    incarnation_repository: str
    target_directory: str = "."
    template_repository: str
    template_repository_version: str
    template_data: fengine.TemplateData
    automerge: bool = False

    model_config = ConfigDict(from_attributes=True)

    def __eq__(self, other) -> bool:
        if isinstance(other, fengine.IncarnationState):
            same_template_repository = self.template_repository == other.template_repository
            same_template_repository_version = self.template_repository_version == other.template_repository_version
            same_template_data = self.template_data == other.template_data
            return same_template_repository and same_template_repository_version and same_template_data

        return super().__eq__(other)


class DesiredIncarnationStatePatch(BaseModel):
    """A DesiredIncarnationStatePatch represents the patch for the desired state of an incarnation."""

    template_repository_version: str | None = None
    template_data: fengine.TemplateData = {}
    automerge: bool
