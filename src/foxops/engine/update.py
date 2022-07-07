from pathlib import Path
from tempfile import TemporaryDirectory

from dictdiffer import diff
from structlog.stdlib import BoundLogger

from foxops import utils
from foxops.engine.fvars import merge_template_data_with_fvars
from foxops.engine.initialization import _initialize_incarnation
from foxops.engine.models import (
    IncarnationState,
    TemplateData,
    fill_missing_optionals_with_defaults,
    load_incarnation_state,
    load_template_config,
)


def get_data_mismatch(
    desired_template_data: TemplateData,
    actual_template_data: TemplateData,
    template_root_dir: Path,
    logger: BoundLogger,
) -> list:
    template_config = load_template_config(template_root_dir / "fengine.yaml")

    # fill defaults in passed data
    template_data_with_defaults = fill_missing_optionals_with_defaults(
        provided_template_data=desired_template_data,
        template_config=template_config,
        logger=logger,
    )

    return list(
        diff(
            actual_template_data,
            template_data_with_defaults,
        )
    )


async def update_incarnation_from_git_template_repository(
    template_git_root_dir: Path,
    update_template_repository: str,
    update_template_repository_version: str,
    update_template_data: TemplateData,
    incarnation_root_dir: Path,
    diff_patch_func,
    logger: BoundLogger,
) -> tuple[IncarnationState, list[Path]]:
    # initialize pristine incarnation from current incarnation state
    current_incarnation_state_path = incarnation_root_dir / ".fengine.yaml"
    current_incarnation_state = load_incarnation_state(current_incarnation_state_path)

    with TemporaryDirectory() as template_root_dir, TemporaryDirectory() as updated_template_root_dir:
        logger.debug(
            f"creating git worktree from current template repository (version: {current_incarnation_state.template_repository_version_hash}) at {template_root_dir}"
        )
        await utils.check_call(
            "git",
            "worktree",
            "add",
            template_root_dir,
            current_incarnation_state.template_repository_version_hash,
            cwd=template_git_root_dir,
        )
        logger.debug(
            f"creating git worktree from updated template repository (version: {update_template_repository_version}) at {updated_template_root_dir}"
        )
        await utils.check_call(
            "git",
            "worktree",
            "add",
            updated_template_root_dir,
            update_template_repository_version,
            cwd=template_git_root_dir,
        )

        return await update_incarnation(
            template_root_dir=Path(template_root_dir),
            update_template_root_dir=Path(updated_template_root_dir),
            update_template_repository=update_template_repository,
            update_template_repository_version=update_template_repository_version,
            update_template_data=update_template_data,
            incarnation_root_dir=incarnation_root_dir,
            diff_patch_func=diff_patch_func,
            logger=logger,
        )


async def update_incarnation(
    template_root_dir: Path,
    update_template_root_dir: Path,
    update_template_repository: str,
    update_template_repository_version: str,
    update_template_data: TemplateData,
    incarnation_root_dir: Path,
    diff_patch_func,
    logger: BoundLogger,
) -> tuple[IncarnationState, list[Path]]:
    """Update an incarnation with a new version of a template."""
    # initialize pristine incarnation from current incarnation state
    current_incarnation_state_path = incarnation_root_dir / ".fengine.yaml"
    current_incarnation_state = load_incarnation_state(current_incarnation_state_path)

    with TemporaryDirectory() as tmp_pristine_incarnation_dir, TemporaryDirectory() as tmp_updated_incarnation_dir:
        logger.debug(
            "initialize pristine incarnation from current incarnation state",
            template_dir=template_root_dir,
            incarnation_dir=tmp_pristine_incarnation_dir,
        )
        await _initialize_incarnation(
            template_root_dir=template_root_dir,
            template_repository=current_incarnation_state.template_repository,
            template_repository_version=current_incarnation_state.template_repository_version,
            template_data=current_incarnation_state.template_data,
            incarnation_root_dir=Path(tmp_pristine_incarnation_dir),
            logger=logger,
        )

        logger.debug(
            "initialize new incarnation from update incarnation state",
            template_dir=update_template_root_dir,
            incarnation_dir=tmp_updated_incarnation_dir,
        )
        updated_incarnation_state = await _initialize_incarnation(
            template_root_dir=update_template_root_dir,
            template_repository=update_template_repository,
            template_repository_version=update_template_repository_version,
            template_data=merge_template_data_with_fvars(
                update_template_data,
                incarnation_root_dir,
                logger,
            ),
            incarnation_root_dir=Path(tmp_updated_incarnation_dir),
            logger=logger,
        )

        # diff pristine and new incarnations
        # apply patch on incarnation to update
        logger.debug(
            "applying patch on pristine and new incarnations",
            diff_a_directory=tmp_pristine_incarnation_dir,
            diff_b_directory=tmp_updated_incarnation_dir,
            patch_directory=incarnation_root_dir,
        )
        files_with_conflicts = await diff_patch_func(
            diff_a_directory=tmp_pristine_incarnation_dir,
            diff_b_directory=tmp_updated_incarnation_dir,
            patch_directory=incarnation_root_dir,
            logger=logger,
        )
        return updated_incarnation_state, files_with_conflicts
