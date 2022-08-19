from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from foxops import __version__


def custom_openapi(app: FastAPI):
    def _wrapper():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="foxops 🦊",
            version=__version__,
            description="OpenAPI Specification for foxops 🦊",
            routes=app.routes,
        )
        openapi_schema["info"]["x-logo"] = {
            "url": "https://emoji.beeimg.com/%F0%9F%A6%8A",
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return _wrapper
