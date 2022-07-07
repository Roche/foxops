from pathlib import Path

from structlog.stdlib import BoundLogger

from foxops.engine.models import TemplateData

#: Holds the filename for the fvars file.
FVARS_FILENAME = "default.fvars"


def merge_template_data_with_fvars(
    template_data: TemplateData,
    fvars_directory: Path,
    logger: BoundLogger,
) -> TemplateData:
    """Merge the given Template data with fvars.

    The fvars filename is hardcoded as `default.fvars`.

    The `template_data` takes precedence over fvars.
    If no fvars file in `fvars_directory` exists, the `template_data` is returned.
    """
    fvars_path = fvars_directory / FVARS_FILENAME
    fvars = read_variables_from_fvars_file(fvars_path, logger)
    return {**fvars, **template_data}


def read_variables_from_fvars_file(path: Path, logger: BoundLogger) -> TemplateData:
    """Read variables from a fvars file.

    If the file does not exist an empty `TemplateData` is returned.
    """
    if not path.exists():
        return {}

    raw_variables = path.read_text().strip()
    variables: TemplateData = dict(line.strip().split("=", maxsplit=1) for line in raw_variables.splitlines())  # type: ignore
    logger.debug(f"read fvars from {path}: {variables}")
    return variables
