# Configuration Files

## fengine.yaml File Reference

The `fengine.yaml` file holds metadata that is required by fengine when rendering the template into an incarnation. Most importantly it contains definitions of template variables, but can also override some settings that affect the rendering process.

An example `fengine.yaml` file looks like this:

```yaml
rendering:
  excluded_files:
    - vendor/**/*

variables:
  application_name:
    type: str
    description: Name of the application. Don't use spaces.
  author:
    type: str
    description: Name of the author. Use format "Name <email>".
  index:
    type: str
    description: The PyPI index
    default: pypi.org
```
