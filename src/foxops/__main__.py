from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from foxops.dependencies import get_dal, get_hoster, get_settings
from foxops.logger import setup_logging
from foxops.middlewares import request_middleware
from foxops.openapi import custom_openapi
from foxops.routers import incarnations


def get_app():
    app = FastAPI()

    settings = get_settings()

    @app.on_event("startup")
    async def startup():

        # validate hoster
        hoster = get_hoster(settings)
        await hoster.validate()

        # initialize database
        dal = get_dal(settings)
        await dal.initialize_db()

        setup_logging(level=settings.log_level)

    # Add middlewares
    app.middleware("http")(request_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add routers to app
    app.include_router(incarnations.router)

    # Add static content
    app.mount("/assets", StaticFiles(directory=settings.frontend_dist_dir / "assets", html=True), name="ui-assets")
    app.mount("/favicons", StaticFiles(directory=settings.frontend_dist_dir / "favicons"), name="ui-favicons")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(settings.frontend_dist_dir / "index.html")

    # Customize OpenAPI specification document
    app.openapi = custom_openapi(app)  # type: ignore

    return app


if __name__ == "__main__":
    app = get_app()
