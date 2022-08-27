import itertools
from http import HTTPStatus
from pathlib import Path

import typer
from ruamel.yaml import YAML

from foxops.cli.v1_compat_reconcile.api import foxops_api
from foxops.cli.v1_compat_reconcile.models import DesiredIncarnationStateConfig
from foxops.logger import get_logger
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    IncarnationBasic,
    IncarnationWithDetails,
)
from foxops.settings import Settings

#: Holds the module logger
logger = get_logger(__name__)

#: Holds a YAML parser
yaml = YAML(typ="safe")


def cmd_reconcile(
    parallelism: int = typer.Option(10, "--parallelism", "-p", help="number of parallel reconciliations"),  # noqa: B008
    config_paths: list[str] = typer.Argument(  # noqa: B008
        None,
        help="Path to the configuration file(s) or folder(s) containing configuration file(s) to use. "
        "The configuration files define the desired incarnation states.",
    ),
    foxops_api_url: str = typer.Option(  # noqa: B008
        default=None,
        help="URL of the FoxOps API to use. If not specified, a local foxops instance is started.",
    ),
):
    logger.warning(
        "This CLI command only exists for backwards-compatibility reasons. "
        "Please use the imperative foxops REST API instead."
    )

    if not config_paths:
        logger.error("no configuration file(s) or folder(s) specified")
        raise typer.Exit(1)

    logger.debug("configuring settings for reconciliation")
    settings = Settings()
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
    flattened_config_files = itertools.chain(*(expand_dir(Path(c)) for c in config_paths))
    for config_file in flattened_config_files:
        try:
            parsed_config = yaml.load(config_file)
            desired_incarnation_states.extend(
                DesiredIncarnationStateConfig.parse_obj(c) for c in parsed_config["incarnations"]
            )
        except Exception as exc:
            logger.error(f"Project definition config at {config_file} is not valid: {exc}")
            raise typer.Exit(1)

    logger.debug(
        f"loaded {len(desired_incarnation_states)} desired incarnation states",
        desired_incarnation_states=desired_incarnation_states,
    )

    with foxops_api(foxops_api_url) as foxops_client:
        for config in desired_incarnation_states:
            logger.info(
                "reconciling desired incarnation state",
                desired_incarnation_state=config,
            )

            incarnation_exists_response = foxops_client.get(
                "/incarnations",
                params={
                    "incarnation_repository": str(config.gitlab_project),
                    "target_directory": str(config.target_directory),
                },
            )
            incarnation_before_update: IncarnationWithDetails | IncarnationBasic
            if incarnation_exists_response.status_code == HTTPStatus.NOT_FOUND:
                logger.info("incarnation does not exist, creating ...")
                dis = DesiredIncarnationState(
                    incarnation_repository=str(config.gitlab_project),
                    target_directory=str(config.target_directory),
                    template_repository=config.template_repository,
                    template_repository_version=config.template_repository_version,
                    template_data=config.template_data,
                    automerge=config.automerge,
                )
                response = foxops_client.post(
                    "/incarnations",
                    params={"allow_import": True},
                    json=dis.dict(),
                )
                if response.status_code != HTTPStatus.CONFLICT:
                    response.raise_for_status()

                incarnation = IncarnationWithDetails(**response.json())

                if response.status_code != HTTPStatus.CONFLICT:
                    logger.info("successfully reconciled", incarnation=incarnation)
                    continue
                else:
                    logger.info(
                        "successfully reconciled, but incarnation already existed and has config mismatches, "
                        "thus needs an update ...",
                        incarnation=incarnation,
                    )
                    incarnation_before_update = incarnation
            else:
                incarnation_exists_response.raise_for_status()
                incarnation_before_update = IncarnationBasic(**incarnation_exists_response.json()[0])

            logger.info(
                "incarnation exists, updating ...",
                incarnation=incarnation_before_update,
            )
            incarnation_id = incarnation_before_update.id
            dis_patch = DesiredIncarnationStatePatch(
                template_repository=config.template_repository,
                template_repository_version=config.template_repository_version,
                template_data=config.template_data,
                automerge=config.automerge,
            )
            response = foxops_client.put(
                f"/incarnations/{incarnation_id}",
                json=dis_patch.dict(),
            )
            response.raise_for_status()
            incarnation = IncarnationWithDetails(**response.json())
            logger.info("successfully reconciled", incarnation=incarnation)
