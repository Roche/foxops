from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from foxops.dependencies import get_dal, get_hoster, get_settings
from foxops.logger import setup_logging
from foxops.middlewares import request_middleware
from foxops.openapi import custom_openapi
from foxops.routers import incarnations

STATIC_DIR = (Path(__file__).parent / "static").absolute()


def get_app():
    app = FastAPI()

    @app.on_event("startup")
    async def startup():
        settings = get_settings()

        # validate hoster
        hoster = get_hoster(settings)
        await hoster.validate()

        # initialize database
        dal = get_dal(settings)
        await dal.initialize_db()

        setup_logging(level=settings.log_level)

    # Add middlewares
    app.middleware("http")(request_middleware)

    # Add routers to app
    app.include_router(incarnations.router)

    # Add static content
    app.mount("/static", StaticFiles(directory=STATIC_DIR.absolute(), html=True), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(STATIC_DIR / "index.html")

    # Customize OpenAPI specification document
    app.openapi = custom_openapi(app)  # type: ignore

    return app


app = get_app()
