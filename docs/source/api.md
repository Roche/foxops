# API

## HTTP API

Foxops is mostly intended to be run as a Software-as-a-Service (SaaS) application. It provides an HTTP API that can be used to manage incarnations.

The API is documented using the [OpenAPI](https://swagger.io/specification/) specification and can be found at `/openapi.json` on your foxops instance. Foxops also serves a Swagger UI to interact directly with the API from the browser at `/docs`.

See the [installation](installation) section for details on how to run foxops.

When calling the HTTP API from a Python application, consider using the [foxops-client-python](https://github.com/Roche/foxops-client-python) library!

## Usage as a Python Library

While foxops is mostly intended to be used via the http API, the entire functionality is also available via Python functions that can be called from your custom application.

```{eval-rst}
.. module:: foxops
```

## fengine

The following interfaces are exposed from the `foxops.fengine` package:

### Models

```{eval-rst}
.. autoclass:: foxops.engine.IncarnationState
   :members:

.. autofunction:: foxops.engine.load_incarnation_state

.. autofunction:: foxops.engine.load_incarnation_state_from_string

.. autofunction:: foxops.engine.save_incarnation_state
```

### Initialization

```{eval-rst}
.. autofunction:: foxops.engine.initialize_incarnation
```

### Update

```{eval-rst}
.. autofunction:: foxops.engine.update_incarnation

.. autofunction:: foxops.engine.update_incarnation_from_git_template_repository
```
