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
    type: string
    description: Name of the application. Don't use spaces.
  author:
    type: string
    description: Name of the author. Use format "Name <email>".
  index:
    type: string
    description: The PyPI index
    default: pypi.org
```

### Variable Definitions

The `variables` section defines the variables that are available to the template. Each variable has a name, a type and a description.

The following basic types are supported:

* `string`: A string value
* `integer`: An integer value
* `boolean`: A boolean value

It is mandatory to give a description for every variable definition. A default value can also be specified as shown in the example above.

#### List Variables

A variable can also be a list of values. For now, only string types are supported. Example:

```yaml
variables:
  authors:
    type: list
    element_type: string
    
    description: List of authors
    
    default:
      - John Doe
      - Jane Doe
```

#### Nested Object Variables

Variables can be nested arbitrarily deep. Default values can not be specified on the variables of type object itself - instead specify them on the nested variables. Example:

```yaml
variables:
  address:
    type: object
    description: Address of the author
    
    children:
      street:
        type: string
        description: Street name
      number:
        type: integer
        description: Street number
      city:
        type: string
        description: City name
        default: Zurich
```
