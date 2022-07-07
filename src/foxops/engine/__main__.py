import asyncio
import logging
from dataclasses import asdict
from pathlib import Path
from subprocess import PIPE, check_output
from typing import Optional

import typer
from structlog.stdlib import BoundLogger

from foxops.engine.initialization import initialize_incarnation
from foxops.engine.models import (
    IncarnationState,
    TemplateConfig,
    TemplateData,
    VariableDefinition,
    load_incarnation_state,
)
from foxops.engine.patching.git_diff_patch import diff_and_patch
from foxops.engine.update import update_incarnation_from_git_template_repository
from foxops.logging import get_logger, setup_logging

app = typer.Typer()

logger: BoundLogger


@app.command(name="new", help="Creates a new template scaffold in the given directory")
def cmd_new(
    target_directory: Path = typer.Argument(  # noqa: B008
        ...,
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
    )
):
    # Make sure the target_directory exists and is empty. Create it if it doesn't exist.
    if target_directory.exists():
        if any(target_directory.iterdir()):
            raise typer.Abort("Target directory is not empty.")
    else:
        target_directory.mkdir(0o755, parents=True)

    # Create sample fengine.yaml
    template_config = TemplateConfig(
        variables={
            "author": VariableDefinition(
                type="str",
                description="The author of the project",
            )
        }
    )
    template_config.to_yaml(target_directory / "fengine.yaml")

    # Create sample README in template directory
    (target_directory / "template").mkdir(0o755)
    (target_directory / "template" / "README.md").write_text(
        "Created by {{ author }}\n"
    )


@app.command(name="initialize")
def cmd_initialize(
    template_repository: Path = typer.Argument(  # noqa: B008
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    incarnation_dir: Path = typer.Argument(  # noqa: B008
        ...,
        exists=False,
        file_okay=False,
        dir_okay=False,
    ),
    raw_template_data: list[str] = typer.Option(  # noqa: B008
        [],
        "--data",
        "-d",
        help="Template data variables in the format of `key=value`",
    ),
    template_repository_version: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--template-version",
        help="Template repository version to use",
    ),
):
    """Initialize an incarnation repository with a version of a template and some data."""
    template_data: TemplateData = dict(
        tuple(x.split("=", maxsplit=1)) for x in raw_template_data  # type: ignore
    )

    log = logger.bind(
        template_repository=template_repository,
        incarnation_dir=incarnation_dir,
        template_data=template_data,
    )

    log.debug("creating empty incarnation directory")
    incarnation_dir.mkdir(parents=True, exist_ok=False)

    if template_repository_version:
        log.debug(
            f"checking out template repository version {template_repository_version}"
        )
        check_output(
            ["git", "checkout", template_repository_version],
            cwd=template_repository,
            stderr=PIPE,
        )

    repository_version = (
        check_output(["git", "rev-parse", "HEAD"], cwd=template_repository)
        .decode()
        .strip()
    )

    log.info(
        "starting initialization incarnation ...",
        template_repository=str(template_repository),
        template_repository_version=repository_version,
        template_data=template_data,
    )

    try:
        asyncio.run(
            initialize_incarnation(
                template_root_dir=template_repository,
                template_repository=str(template_repository),
                template_repository_version=repository_version,
                template_data=template_data,
                incarnation_root_dir=incarnation_dir,
                logger=log,
            )
        )
    except Exception as exc:
        log.exception(f"initialization failed: {exc}")
    else:
        log.info("successfully initialized incarnation")
    finally:
        if template_repository_version:
            check_output(
                ["git", "checkout", "-"],
                cwd=template_repository,
                stderr=PIPE,
            )


@app.command(name="update")
def cmd_update(
    incarnation_dir: Path = typer.Argument(  # noqa: B008
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        writable=True,
    ),
    raw_template_data: list[str] = typer.Option(  # noqa: B008
        [],
        "--data",
        "-d",
        help="Template data variables in the format of `key=value`",
    ),
    remove_template_data: list[str] = typer.Option(  # noqa: B008
        [],
        "--remove-data",
        help="Template data variables to remove",
    ),
    update_repository_version: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--update-repository-version",
        "-u",
        help="the version of the template repository to update to",
    ),
    overridden_template_repository: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--template-repository",
        "-r",
        help="Override the template repository with a local path recorded in the incarnation state",
    ),
):
    """Initialize an incarnation repository with a version of a template and some data."""
    template_data: dict[str, str] = dict(
        tuple(x.split("=", maxsplit=1)) for x in raw_template_data  # type: ignore
    )

    incarnation_state_path = incarnation_dir / ".fengine.yaml"
    logger.debug(
        f"getting template repository path from incarnation state at {incarnation_state_path}"
    )
    incarnation_state = load_incarnation_state(incarnation_state_path)

    logger.debug(
        f"loaded incarnation state from incarnation repository {incarnation_state_path}",
        incarnation_state=incarnation_state,
    )

    if overridden_template_repository is not None:
        logger.debug(
            f"overriding template repository with {overridden_template_repository}"
        )
        incarnation_state = IncarnationState(
            **{
                **asdict(incarnation_state),  # type: ignore
                "template_repository": str(overridden_template_repository),
            }
        )

    if not Path(incarnation_state.template_repository).is_dir():
        logger.error(
            f"template repository at {incarnation_state.template_repository} is not a local directory. "
            "Might it be an URL? If, so, use `-r` to override the template repository from the "
            "incarnation state with a path to the local clone of that template repository."
        )
        raise typer.Exit(1)

    logger.debug(
        "updating template data from incarnation state with given data from user",
        incarnation_state_data=incarnation_state.template_data,
        user_template_data=template_data,
    )
    merged_template_data = incarnation_state.template_data.copy()
    merged_template_data.update(template_data)
    merged_template_data = {
        k: v for k, v in merged_template_data.items() if k not in remove_template_data
    }

    log = logger.bind(
        template_repository=incarnation_state.template_repository,
        incarnation_dir=incarnation_dir,
        template_data=merged_template_data,
    )

    if update_repository_version is None:
        update_repository_version = (
            check_output(
                ["git", "rev-parse", "HEAD"], cwd=incarnation_state.template_repository
            )
            .decode("utf-8")
            .strip()
        )

    log.info(
        f"starting update of incarnation to version {update_repository_version}...",
        template_repository=str(incarnation_state.template_repository),
        template_repository_version=update_repository_version,
        template_data=merged_template_data,
    )

    try:
        files_with_conflicts = asyncio.run(
            update_incarnation_from_git_template_repository(
                template_git_root_dir=Path(incarnation_state.template_repository),
                update_template_repository=str(incarnation_state.template_repository),
                update_template_repository_version=update_repository_version,
                update_template_data=merged_template_data,
                incarnation_root_dir=incarnation_dir,
                diff_patch_func=diff_and_patch,
                logger=log,
            )
        )

        if files_with_conflicts:
            log.error(
                f"update failed, there were conflicts while updating the following files: {', '.join([str(f) for f in files_with_conflicts])}"
            )
        else:
            log.info("successfully updated incarnation")
    except Exception as exc:
        log.exception(f"update failed: {exc}")


@app.callback()
def main(
    verbose: bool = typer.Option(  # noqa: B008
        False, "--verbose", "-v", help="turn on verbose logging"
    ),
    logs_as_json: bool = typer.Option(  # noqa: B008
        False, "--json-logs", "-j", help="render logs as JSON"
    ),
):
    """
    Foxops engine ... use it to initialize or update template incarnations.
    """
    if verbose:
        setup_logging(logging.DEBUG, logs_as_json)
    else:
        setup_logging(logging.INFO, logs_as_json)

    global logger
    logger = get_logger("app")


if __name__ == "__main__":
    app()
