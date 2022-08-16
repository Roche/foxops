import logging

import typer

from foxops.cli.v1_compat_reconcile import cmd_reconcile
from foxops.logger import get_logger, setup_logging

#: Holds the module logger
logger = get_logger(__name__)

app = typer.Typer()

# add commands
app.command(name="reconcile", help="Reconciles the given files")(cmd_reconcile)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="turn on verbose logging"),  # noqa: B008
):
    """
    Foxops engine ... use it to initialize or update template incarnations.
    """
    if verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)


if __name__ == "__main__":
    app()
