from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from foxops import __version__

#: Holds the router for the version endpoint
router = APIRouter(tags=["version"])


@router.get("/version", response_class=PlainTextResponse)
def get_version():
    """Retrieve the foxops version of this instance."""
    return __version__
