# Installation

The **foxops** Python package can be installed from the Roche GitLab Package Registry:

```bash
pip install foxops
```

```{note}
Make sure to replace `<your_personal_token>` with a valid Personal Access Token.
```

The foxops Python package contains multiple console scripts:

* `foxops` - the main foxops tool to manage the full MegOps lifecycle
* `fengine` - exposes the initialize and update APIs to manually execute the template rendering

## Docker

`foxops` is also deployed in the GitHub Container Registry and can be pulled from there:

```bash
docker pull ghcr.io/roche/foxops:<version>
```

```{note}
Make sure to replace the `<version>` with a [valid version](https://github.com/Roche/foxops/releases).
```

The default entrypoint for the `foxops` docker image is the `foxops` console script.
However, you may also specify the `fengine` console script as entrypoint.
