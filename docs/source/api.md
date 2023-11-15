# API

## HTTP API

Foxops is mostly intended to be run as a Software-as-a-Service (SaaS) application. It provides an HTTP API that can be used to manage incarnations.

The API is documented using the [OpenAPI](https://swagger.io/specification/) specification and can be found at `/openapi.json` on your foxops instance. Foxops also serves a Swagger UI to interact directly with the API from the browser at `/docs`.

See the [installation](installation) section for details on how to run foxops.

When calling the HTTP API from a Python application, consider using the [foxops-client-python](https://github.com/Roche/foxops-client-python) library!
