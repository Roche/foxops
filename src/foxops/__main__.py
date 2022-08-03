from fastapi import FastAPI

from foxops.dependencies import get_dal, get_hoster, get_settings
from foxops.logging import setup_logging
from foxops.middlewares import request_middleware
from foxops.openapi import custom_openapi
from foxops.routers import incarnations


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

    # Customize OpenAPI specification document
    app.openapi = custom_openapi(app)  # type: ignore

    return app


app = get_app()
