from pathlib import Path

from pydantic import ValidationError

from foxops.engine.errors import ProvidedTemplateDataInvalidError
from foxops.engine.models.incarnation_state import IncarnationState, TemplateData
from foxops.engine.models.template_config import TemplateConfig
from foxops.engine.rendering import render_template
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
        * validate the provided template data against the required template variables
        * render template directory file system contents into incarnation directory
    """

    # verify that the template data match the required template variables
    template_config = TemplateConfig.from_path(template_root_dir / "fengine.yaml")

    try:
        template_data_model = template_config.data_model().model_validate(template_data)
    except ValidationError as e:
        raise ProvidedTemplateDataInvalidError from e

    # and dump it again to enrich it with the specified default values
    full_template_data = template_data_model.model_dump()
    full_template_data.update(
        {
            "fengine": {
                "template": {
                    "repository": template_repository,
                    "repository_version": template_repository_version,
                }
            }
        }
    )

    await render_template(
        template_root_dir / "template",
        incarnation_root_dir,
        full_template_data,
        rendering_filename_exclude_patterns=template_config.rendering.excluded_files,
    )

    # save the incarnation state to a file in the incarnation repo
    template_repository_version_hash = await GitRepository(template_root_dir).head()

    incarnation_state = IncarnationState(
        template_repository=template_repository,
        template_repository_version=template_repository_version,
        template_repository_version_hash=template_repository_version_hash,
        template_data=template_data,
        template_data_full=full_template_data,
    )
    incarnation_state.save(incarnation_root_dir / ".fengine.yaml")

    return incarnation_state
