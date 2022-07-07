# API

While foxops was mostly intended to be used via the existing CLI applications, the entire functionality is also available Python functions that can be called from your custom application.

```{eval-rst}
.. module:: foxops
```

## fengine API

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

### Diff and Patch

```{eval-rst}
.. autofunction:: foxops.engine.diff_and_patch
```
