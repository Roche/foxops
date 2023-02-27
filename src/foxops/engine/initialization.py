import copy
from pathlib import Path

from foxops.engine.fvars import merge_template_data_with_fvars
from foxops.engine.models import (
    IncarnationState,
    TemplateData,
    fill_missing_optionals_with_defaults,
    load_template_config,
    save_incarnation_state,
)
from foxops.engine.rendering import render_template
from foxops.errors import ReconciliationUserError
from foxops.external.git import GitRepository
from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


async def initialize_incarnation(
    template_root_dir: Path,
    template_repository: str,
    template_repository_version: str,
    template_data: TemplateData,
    incarnation_root_dir: Path,
) -> IncarnationState:
    """Initialize an incarnation repository with a version of a template.

    The initialization process consists of the following steps:
        * ensure incarnation directory exists
        * render template directory file system contents into incarnation directory
    """
    template_data = merge_template_data_with_fvars(
        template_data=template_data,
        fvars_directory=incarnation_root_dir,
    )
    return await _initialize_incarnation(
        template_root_dir=template_root_dir,
        template_repository=template_repository,
        template_repository_version=template_repository_version,
        template_data=template_data,
        incarnation_root_dir=incarnation_root_dir,
    )


async def _initialize_incarnation(
    template_root_dir: Path,
    template_repository: str,
    template_repository_version: str,
    template_data: TemplateData,
    incarnation_root_dir: Path,
) -> IncarnationState:
    # verify that the template data in the desired incarnation state match the required template variables
    template_config = load_template_config(template_root_dir / "fengine.yaml")
    logger.debug(f"load template config from {template_config} to initialize incarnation at {incarnation_root_dir}")
    required_variable_names = set(template_config.required_variables.keys())
    provided_variable_names = set(template_data.keys())
    if not required_variable_names.issubset(provided_variable_names):
        raise ReconciliationUserError(
            f"the template required the variables {sorted(required_variable_names)} "
            "but the provided template data for the incarnation "
            f"where {sorted(provided_variable_names)}. "
            "Please make sure that the provided ones are a superset of the required ones."
        )

    # log additional template data passed for the incarnation
    config_variable_names = set(template_config.variables.keys())
    if additional_values := provided_variable_names - config_variable_names:
        logger.warn(f"got additional template data for the incarnation: {sorted(additional_values)}")

    # fill defaults in passed data
    template_data_with_defaults = fill_missing_optionals_with_defaults(
        provided_template_data=template_data,
        template_config=template_config,
    )

    # add meta-information to the template data.
    # ... we don't want to include that in the "template_data" section of the `.fengine.yaml` file
    template_data_with_defaults_and_metadata = dict(copy.deepcopy(template_data_with_defaults))
    template_data_with_defaults_and_metadata.update(
        {
            "_fengine_template_repository": template_repository,
            "_fengine_template_repository_version": template_repository_version,
        }
    )

    await render_template(
        template_root_dir / "template",
        incarnation_root_dir,
        template_data_with_defaults_and_metadata,
        rendering_filename_exclude_patterns=template_config.rendering.excluded_files,
    )

    template_repository_version_hash = await GitRepository(template_root_dir).head()
    incarnation_state = IncarnationState(
        template_repository=template_repository,
        template_repository_version=template_repository_version,
        template_repository_version_hash=template_repository_version_hash,
        template_data=template_data_with_defaults,
    )

    incarnation_config_path = Path(incarnation_root_dir, ".fengine.yaml")
    save_incarnation_state(incarnation_config_path, incarnation_state)
    logger.debug(f"save incarnation state to {incarnation_config_path} after template initialization")
    return incarnation_state
