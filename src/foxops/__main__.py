import logging

from fastapi import FastAPI

from foxops.dal import get_dal
from foxops.logging import setup_logging
from foxops.middlewares import request_middleware
from foxops.openapi import custom_openapi
from foxops.routers import incarnations

app = FastAPI()


@app.on_event("startup")
async def startup():
    dal = get_dal()
    await dal.initialize_db()

    setup_logging(level=logging.DEBUG)


# Add middlewares
app.middleware("http")(request_middleware)

# Add routers to app
app.include_router(incarnations.router)

# Customize OpenAPI specification document
app.openapi = custom_openapi(app)  # type: ignore
