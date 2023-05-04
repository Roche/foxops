from pathlib import Path
from tempfile import TemporaryDirectory

from foxops import utils
from foxops.engine.fvars import merge_template_data_with_fvars
from foxops.engine.initialization import _initialize_incarnation
from foxops.engine.models import IncarnationState, TemplateData, load_incarnation_state
from foxops.engine.patching.git_diff_patch import PatchResult
from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


async def update_incarnation_from_git_template_repository(
    template_git_repository: Path,
    update_template_repository_version: str,
    update_template_data: TemplateData,
    incarnation_root_dir: Path,
    diff_patch_func,
) -> tuple[bool, IncarnationState, PatchResult | None]:
    if update_template_repository_version.startswith("-"):
        raise ValueError(
            f"update_template_repository_version must ba a valid git refspec and "
            f"not start with a dash (-): {update_template_repository_version}"
        )

    # initialize pristine incarnation from current incarnation state
    current_incarnation_state_path = incarnation_root_dir / ".fengine.yaml"
    current_incarnation_state = load_incarnation_state(current_incarnation_state_path)

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
        )


async def update_incarnation(
    original_template_root_dir: Path,
    updated_template_root_dir: Path,
    updated_template_repository_version: str,
    updated_template_data: TemplateData,
    incarnation_root_dir: Path,
    diff_patch_func,
) -> tuple[bool, IncarnationState, PatchResult | None]:
    """Update an incarnation with a new version of a template."""
    # initialize pristine incarnation from current incarnation state
    current_incarnation_state_path = incarnation_root_dir / ".fengine.yaml"
    current_incarnation_state = load_incarnation_state(current_incarnation_state_path)

    with TemporaryDirectory() as tmp_pristine_incarnation_dir, TemporaryDirectory() as tmp_updated_incarnation_dir:
        logger.debug(
            "initialize pristine incarnation from current incarnation state",
            template_dir=original_template_root_dir,
            incarnation_dir=tmp_pristine_incarnation_dir,
        )
        await _initialize_incarnation(
            template_root_dir=original_template_root_dir,
            template_repository=current_incarnation_state.template_repository,
            template_repository_version=current_incarnation_state.template_repository_version,
            template_data=current_incarnation_state.template_data,
            incarnation_root_dir=Path(tmp_pristine_incarnation_dir),
        )

        # copy over .fengine.yaml from the actual incarnation, just to make sure there are no formatting differences
        # that would be messing up the patching.
        #
        # there were unclear cases where the YAML rending was slightly different (e.g. strings starting on a newline)
        # during updates, compared to the original incarnation rendering (reason unclear)
        (Path(tmp_pristine_incarnation_dir) / ".fengine.yaml").write_bytes(current_incarnation_state_path.read_bytes())

        logger.debug(
            "initialize new incarnation from update incarnation state",
            template_dir=updated_template_root_dir,
            incarnation_dir=tmp_updated_incarnation_dir,
        )
        updated_incarnation_state = await _initialize_incarnation(
            template_root_dir=updated_template_root_dir,
            template_repository=current_incarnation_state.template_repository,
            template_repository_version=updated_template_repository_version,
            template_data=merge_template_data_with_fvars(
                updated_template_data,
                incarnation_root_dir,
            ),
            incarnation_root_dir=Path(tmp_updated_incarnation_dir),
        )

        # diff pristine and new incarnations
        # apply patch on incarnation to update
        logger.debug(
            "applying patch on pristine and new incarnations",
            diff_a_directory=tmp_pristine_incarnation_dir,
            diff_b_directory=tmp_updated_incarnation_dir,
            patch_directory=incarnation_root_dir,
        )
        if (
            patch_result := await diff_patch_func(
                diff_a_directory=tmp_pristine_incarnation_dir,
                diff_b_directory=tmp_updated_incarnation_dir,
                patch_directory=incarnation_root_dir,
            )
        ) is not None:
            return True, updated_incarnation_state, patch_result
        else:
            logger.debug("Update didn't change anything")
            return False, updated_incarnation_state, None
