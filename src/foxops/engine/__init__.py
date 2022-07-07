"""
foxops engine aka. fengine is a Python package responsible for
rendering a template into a particular incarnation instance.
It also handles updates of said templates.
"""

from foxops.engine.fvars import FVARS_FILENAME  # noqa
from foxops.engine.initialization import initialize_incarnation  # noqa
from foxops.engine.models import IncarnationState  # noqa
from foxops.engine.models import TemplateData  # noqa
from foxops.engine.models import load_incarnation_state  # noqa
from foxops.engine.models import load_incarnation_state_from_string  # noqa
from foxops.engine.models import save_incarnation_state  # noqa
from foxops.engine.patching.git_diff_patch import diff_and_patch  # noqa
from foxops.engine.update import (  # noqa
    update_incarnation,
    update_incarnation_from_git_template_repository,
)
