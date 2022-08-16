# Installation

The **foxops** Python package can be installed from the PyPI:

```bash
pip install foxops
```

The foxops Python package contains multiple console scripts:

* `fengine` - exposes the initialize and update APIs to manually execute the template rendering
* `foxops` - the legacy command line

And the main foxops API server can be started using uvicorn:

```
uvicorn foxops.__main__:app --host localhost --port 5001 --reload
```

## Docker

`foxops` is also deployed in the GitHub Container Registry and can be pulled from there:

```bash
docker pull ghcr.io/roche/foxops:<version>
```

```{note}
Make sure to replace the `<version>` with a [valid version](https://github.com/Roche/foxops/releases).
```