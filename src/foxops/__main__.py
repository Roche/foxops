import asyncio
import itertools
import logging
import warnings
from pathlib import Path

import typer
from pydantic import ValidationError
from ruamel.yaml import YAML
from structlog.stdlib import BoundLogger

from foxops.logging import get_logger, setup_logging
from foxops.models import DesiredIncarnationStateConfig
from foxops.reconciliation import AsyncGitlabClient, ReconciliationState, reconcile
from foxops.settings import Settings

app = typer.Typer()

yaml = YAML(typ="safe")

logger: BoundLogger


def get_settings():
    try:
        warnings.simplefilter("ignore", category=UserWarning)
        settings = Settings()
    except ValidationError as exc:
        for error in exc.errors():
            error_loc = " -> ".join(str(e) for e in error["loc"])
            logger.error(
                f"error when creating Settings due to the field '{error_loc}': {error['msg']}",
                settings_field=error_loc,
                field_error_reason=error["msg"],
            )
        raise typer.Exit(1)
    else:
        return settings


@app.command(name="reconcile")
def cmd_reconcile(
    parallelism: int = typer.Option(  # noqa: B008
        10, "--parallelism", "-p", help="number of parallel reconciliations"
    ),
    config_paths: list[str] = typer.Argument(  # noqa: B008
        None,
        help="Path to the configuration file(s) or folder(s) containing configuration file(s) to use. The configuration files define the desired incarnation states.",
    ),
):
    if not config_paths:
        logger.error("no configuration file(s) or folder(s) specified")
        raise typer.Exit(1)

    logger.debug("configuring settings for reconciliation")
    settings = get_settings()
    logger.debug("configured settings", settings=settings)

    logger.debug(
        "loading desired incarnation states configurations ...",
        desired_incarnation_state_config_paths=config_paths,
    )

    def expand_dir(path: Path) -> list[Path]:
        if path.is_dir():
            return list(path.glob("**/*.yml")) + list(path.glob("**/*.yaml"))
        return [path]

    desired_incarnation_states: list[DesiredIncarnationStateConfig] = []
    flattened_config_files = itertools.chain(
        *(expand_dir(Path(c)) for c in config_paths)
    )
    for config_file in flattened_config_files:
        try:
            parsed_config = yaml.load(config_file)
            desired_incarnation_states.extend(
                DesiredIncarnationStateConfig.parse_obj(c)
                for c in parsed_config["incarnations"]
            )
        except Exception as exc:
            logger.error(
                f"Project definition config at {config_file} is not valid: {exc}"
            )
            raise typer.Exit(1)

    logger.debug(
        f"loaded {len(desired_incarnation_states)} desired incarnation states",
        desired_incarnation_states=desired_incarnation_states,
    )

    async def main():
        async with AsyncGitlabClient(
            base_url=settings.gitlab_address,
            token=settings.gitlab_token.get_secret_value(),
        ) as gitlab:
            reconciliation_states = await reconcile(
                gitlab, desired_incarnation_states, parallelism=parallelism
            )
            return reconciliation_states

    logger.info("starting reconciliation")
    reconciliation_states = asyncio.run(main())
    logger.info("finished reconciliation")

    for desired_incarnation_state, reconciliation_state in sorted(
        zip(desired_incarnation_states, reconciliation_states),
        key=lambda x: (x[1], x[0].gitlab_project),
    ):
        logger.info(
            f"project '{desired_incarnation_state.gitlab_project}' reconciled with state '{reconciliation_state.name.lower()}'",
            reconciliation_state=reconciliation_state,
            category="summary",
        )

    if any(s == ReconciliationState.FAILED for s in reconciliation_states):
        raise typer.Exit(2)


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
    Foxops for MegOps, or something.
    """
    if verbose:
        setup_logging(logging.DEBUG, logs_as_json)
    else:
        setup_logging(logging.INFO, logs_as_json)

    global logger
    logger = get_logger("app")


if __name__ == "__main__":
    app()
