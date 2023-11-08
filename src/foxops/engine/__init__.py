"""
foxops engine aka. fengine is a Python package responsible for
rendering a template into a particular incarnation instance.
It also handles updates of said templates.
"""

from foxops.engine.initialization import initialize_incarnation
from foxops.engine.models.incarnation_state import IncarnationState, TemplateData
from foxops.engine.patching.git_diff_patch import diff_and_patch
from foxops.engine.update import (
    update_incarnation,
    update_incarnation_from_git_template_repository,
)

__all__ = [
    "initialize_incarnation",
    "update_incarnation",
    "update_incarnation_from_git_template_repository",
    "diff_and_patch",
    "IncarnationState",
    "TemplateData",
]
