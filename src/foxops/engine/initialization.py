from pathlib import Path

from structlog.stdlib import BoundLogger

from foxops.engine.fvars import merge_template_data_with_fvars
from foxops.engine.models import (
    IncarnationState,
    TemplateData,
    fill_missing_optionals_with_defaults,
    load_template_config,
    save_incarnation_state,
)
from foxops.engine.rendering import render_template
from foxops.external.git import GitRepository


async def initialize_incarnation(
    template_root_dir: Path,
    template_repository: str,
    template_repository_version: str,
    template_data: TemplateData,
    incarnation_root_dir: Path,
    logger: BoundLogger,
) -> IncarnationState:
    """Initialize an incarnation repository with a version of a template.

    The initialization process consists of the following steps:
        * ensure incarnation directory exists
        * render template directory file system contents into incarnation directory
    """
    template_data = merge_template_data_with_fvars(
        template_data=template_data,
        fvars_directory=incarnation_root_dir,
        logger=logger,
    )
    return await _initialize_incarnation(
        template_root_dir=template_root_dir,
        template_repository=template_repository,
        template_repository_version=template_repository_version,
        template_data=template_data,
        incarnation_root_dir=incarnation_root_dir,
        logger=logger,
    )


async def _initialize_incarnation(
    template_root_dir: Path,
    template_repository: str,
    template_repository_version: str,
    template_data: TemplateData,
    incarnation_root_dir: Path,
    logger: BoundLogger,
) -> IncarnationState:
    # verify that the template data in the desired incarnation state match the required template variables
    template_config = load_template_config(template_root_dir / "fengine.yaml")
    logger.debug(
        f"load template config from {template_config} to initialize incarnation at {incarnation_root_dir}"
    )
    required_variable_names = set(template_config.required_variables.keys())
    provided_variable_names = set(template_data.keys())
    if not required_variable_names.issubset(provided_variable_names):
        raise ValueError(
            f"the template required the variables {sorted(required_variable_names)} "
            "but the provided template data for the incarnation "
            f"where {sorted(provided_variable_names)}. "
            "Please make sure that the provided ones are a superset of the required ones."
        )

    # log additional template data passed for the incarnation
    config_variable_names = set(template_config.variables.keys())
    if additional_values := provided_variable_names - config_variable_names:
        logger.warn(
            f"got additional template data for the incarnation: {sorted(additional_values)}"
        )

    # fill defaults in passed data
    template_data_with_defaults = fill_missing_optionals_with_defaults(
        provided_template_data=template_data,
        template_config=template_config,
        logger=logger,
    )

    await render_template(
        template_root_dir / "template",
        incarnation_root_dir,
        template_data_with_defaults,
        rendering_filename_exclude_patterns=template_config.rendering.excluded_files,
        logger=logger,
    )

    template_repository_version_hash = await GitRepository(
        template_root_dir, logger
    ).head()
    incarnation_state = IncarnationState(
        template_repository=template_repository,
        template_repository_version=template_repository_version,
        template_repository_version_hash=template_repository_version_hash,
        template_data=template_data_with_defaults,
    )

    incarnation_config_path = Path(incarnation_root_dir, ".fengine.yaml")
    save_incarnation_state(incarnation_config_path, incarnation_state)
    logger.debug(
        f"save incarnation state to {incarnation_config_path} after template initialization"
    )
    return incarnation_state
