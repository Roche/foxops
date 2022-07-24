# foxops 🦊

A modest templating tool to keep your projects up-to-date.

more coming soon, stay tuned! 🚧

## Documentation

The documentation is available on rtd: https://foxops.readthedocs.io

## Installation

The `foxops` package is available on PyPI and can be installed using `pip`:

```shell
python -m pip install foxops
```

The `foxops` is available in a container image hosted on [ghcr](https://github.com/Roche/foxops/pkgs/container/foxops):

```shell
docker run -it --rm ghcr.io/roche/foxops --help
```

# Future Improvements

* Add an imperative REST API to foxops to create/update and list incarnations
* Add a web UI on top of the foxops API
* Add the capability to work with multiple different Git Hosting instances (i.e. various gitlab instances) in a single foxops deployment
* Add user authentication & rbac
* Add support for GitHub, BitBucket, ...
