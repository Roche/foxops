from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from foxops import utils
from foxops.engine import initialize_incarnation
from foxops.engine.models.incarnation_state import IncarnationState, TemplateData
from foxops.engine.patching.git_diff_patch import PatchResult
from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


def _patch_template_data(data: TemplateData, patch: TemplateData) -> None:
    """Patch the template data with the patch data (in-place).

    Will iterate through the provided patch 1-by-1, deeply merging it into the "data" dict.
    If a list is encountered in the patch, it will fully replace the list in the data dict (instead of appending).
    """

    for key, value in patch.items():
        if isinstance(value, dict):
            if key not in data:
                data[key] = {}

            _patch_template_data(data[key], value)
        else:
            data[key] = value


async def update_incarnation_from_git_template_repository(
    template_git_repository: Path,
    update_template_repository_version: str,
    update_template_data: TemplateData,
    incarnation_root_dir: Path,
    diff_patch_func,
    patch_data: bool = False,
) -> tuple[bool, IncarnationState, PatchResult | None]:
    """
    Update an incarnation with a new version of a template.

    The process works roughly like this:
    * create a git worktree from the template repository version ('v1') that is currently in use by the incarnation
    * create a git worktree from the template repository version ('v2') that the incarnation should be updated to
    * initialize two _temporary_ incarnations from both template versions into separate directories:
      - the old template version with the data that is currently in use by the incarnation
      - the new template version with the data that was provided for the update
    * diff the two incarnations - then apply the patch on the actual incarnation that should be updated
    """
    if update_template_repository_version.startswith("-"):
        raise ValueError(
            f"update_template_repository_version must ba a valid git refspec and "
            f"not start with a dash (-): {update_template_repository_version}"
        )

    # initialize pristine incarnation from current incarnation state
    current_incarnation_state = IncarnationState.from_file(incarnation_root_dir / ".fengine.yaml")

    with TemporaryDirectory() as original_template_root_dir, TemporaryDirectory() as updated_template_root_dir:
        logger.debug(
            f"creating git worktree from current template repository "
            f"(version: {current_incarnation_state.template_repository_version_hash}) at {original_template_root_dir}"
        )
        await utils.check_call(
            "git",
            "worktree",
            "add",
            original_template_root_dir,
            current_incarnation_state.template_repository_version_hash,
            cwd=template_git_repository,
        )
        logger.debug(
            f"creating git worktree from updated template repository "
            f"(version: {update_template_repository_version}) at {updated_template_root_dir}"
        )
        await utils.check_call(
            "git",
            "worktree",
            "add",
            updated_template_root_dir,
            update_template_repository_version,
            cwd=template_git_repository,
        )

        return await update_incarnation(
            original_template_root_dir=Path(original_template_root_dir),
            updated_template_root_dir=Path(updated_template_root_dir),
            updated_template_repository_version=update_template_repository_version,
            updated_template_data=update_template_data,
            incarnation_root_dir=incarnation_root_dir,
            diff_patch_func=diff_patch_func,
            patch_data=patch_data,
        )


async def update_incarnation(
    original_template_root_dir: Path,
    updated_template_root_dir: Path,
    updated_template_repository_version: str,
    updated_template_data: TemplateData,
    incarnation_root_dir: Path,
    diff_patch_func,
    patch_data: bool = False,
) -> tuple[bool, IncarnationState, PatchResult | None]:
    """Update an incarnation with a new version of a template.

    If patch_data is True, the updated_template_data will be merged into the current template data.
    """

    # initialize pristine incarnation from current incarnation state
    incarnation_state_path = incarnation_root_dir / ".fengine.yaml"
    incarnation_state = IncarnationState.from_file(incarnation_state_path)

    if patch_data:
        template_data = deepcopy(incarnation_state.template_data)
        _patch_template_data(template_data, updated_template_data)
    else:
        template_data = updated_template_data

    with TemporaryDirectory() as incarnation_v1_dir, TemporaryDirectory() as incarnation_v2_dir:
        logger.debug(
            "initialize pristine incarnation from current incarnation state",
            template_dir=original_template_root_dir,
            incarnation_dir=incarnation_v1_dir,
        )
        await initialize_incarnation(
            template_root_dir=original_template_root_dir,
            template_repository=incarnation_state.template_repository,
            template_repository_version=incarnation_state.template_repository_version,
            template_data=incarnation_state.template_data,
            incarnation_root_dir=Path(incarnation_v1_dir),
        )

        # copy over .fengine.yaml from the actual incarnation, just to make sure there are no formatting differences
        # that would be messing up the patching.
        #
        # there were unclear cases where the YAML rending was slightly different (e.g. strings starting on a newline)
        # during updates, compared to the original incarnation rendering (reason unclear)
        (Path(incarnation_v1_dir) / ".fengine.yaml").write_bytes(incarnation_state_path.read_bytes())

        logger.debug(
            "initialize new incarnation from update incarnation state",
            template_dir=updated_template_root_dir,
            incarnation_dir=incarnation_v2_dir,
        )
        incarnation_v2_state = await initialize_incarnation(
            template_root_dir=updated_template_root_dir,
            template_repository=incarnation_state.template_repository,
            template_repository_version=updated_template_repository_version,
            template_data=template_data,
            incarnation_root_dir=Path(incarnation_v2_dir),
        )

        # diff pristine and new incarnations
        # apply patch on incarnation to update
        logger.debug(
            "applying patch on pristine and new incarnations",
            diff_a_directory=incarnation_v1_dir,
            diff_b_directory=incarnation_v2_dir,
            patch_directory=incarnation_root_dir,
        )
        patch_result = await diff_patch_func(
            diff_a_directory=incarnation_v1_dir,
            diff_b_directory=incarnation_v2_dir,
            patch_directory=incarnation_root_dir,
        )

        if patch_result is not None:
            return True, incarnation_v2_state, patch_result
        else:
            logger.debug("Update didn't change anything")
            return False, incarnation_v2_state, None
