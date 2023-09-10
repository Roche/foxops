from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from foxops.dependencies import get_settings, static_token_auth_scheme
from foxops.error_handlers import __error_handlers__
from foxops.logger import get_logger, setup_logging
from foxops.middlewares import request_id_middleware, request_time_middleware
from foxops.openapi import custom_openapi
from foxops.routers import auth, incarnations, not_found, version

#: Holds the module logger instance
logger = get_logger(__name__)

#: Holds a list of directories within the frontend build distribution.
#  Those directories are mounted under `/`.
#  FIXME: figure out a way how we could wildcard this ...
FRONTEND_SUBDIRS = ["assets", "favicons"]


def create_app():
    settings = get_settings()
    setup_logging(level=settings.log_level)

    app = FastAPI()

    # Add middlewares
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(request_time_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    for exc_type, handler in __error_handlers__.items():
        app.add_exception_handler(exc_type, handler)  # type: ignore

    # Add routes to the publicly available router (no authentication)
    public_router = APIRouter()
    public_router.include_router(version.router)
    public_router.include_router(auth.router)

    # Add routes to the protected router (authentication required)
    protected_router = APIRouter(dependencies=[Depends(static_token_auth_scheme)])
    protected_router.include_router(incarnations.router)

    app.include_router(public_router)
    app.include_router(protected_router)

    app.include_router(not_found.router)

    # Add static content
    for frontend_dir in FRONTEND_SUBDIRS:
        path = settings.frontend_dist_dir / frontend_dir
        if not path.exists():
            logger.warning(f"The static asset path at {path} does not exist, skipping ...")
            continue

        app.mount(
            f"/{frontend_dir}",
            StaticFiles(directory=path, html=True),
            name=f"ui-{frontend_dir}",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _(full_path: str):
        """Serve the frontend."""
        logger.debug("Serving frontend path", path=full_path)
        return FileResponse(settings.frontend_dist_dir / "index.html")

    # Customize OpenAPI specification document
    app.openapi = custom_openapi(app)  # type: ignore

    return app


def main_dev():
    """Main entrypoint for LOCAL DEVELOPMENT ONLY!"""
    import uvicorn  # type: ignore

    uvicorn.run(
        app=create_app(),
        host="127.0.0.1",
        port=5001,
        reload=False,
        log_level="debug",
        debug=True,
        workers=1,
        limit_concurrency=1,
        limit_max_requests=1,
    )


if __name__ == "__main__":
    main_dev()
