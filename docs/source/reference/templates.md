# Templates

## Directory Structure

The directory structure of a template is as follows:

```
root folder (git repo root)/
├── template/
│   └── ... any files / folders
└── fengine.yaml
```

## Metadata (fengine.yaml)
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

(list-variables)=
#### List Variables

A variable can also be a list of values. For now, two types of variables are supported: string types and nested object type. Example:

String list variable:
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

Nested object list variable:
```yaml
variables:
  my_object_list:
    type: list
    element_type: object
    description: "A list of complex objects"
    children:
      name:
        type: string
        description: "Name of the item"
      count:
        type: integer
        description: "Count of the item"
```

## Template Variables & Engine

Foxops will render all files within the `template/` folder into the incarnation - and uses the Jinja2 template engine to render the files. This means that you can use all the features of Jinja2 in your templates.

Here you can find the [full documentation](https://jinja.palletsprojects.com/en/3.1.x/templates) of that template language.

### Using Variables

To use a variable in a file, you can use the `{{ .. }}` syntax, e.g.:

```jinja
This template was incarnated by {{ author }}.

Template version that was used {{ fengine.template.version }}
{# note: this is the syntax for accessing nested variables #}
{# ... and this btw. is a comment which will be excluded in the rendered file #}
```

#### Conditionals

To use a conditional in a file, you can use the `{% if .. %}` syntax, e.g.:

```jinja
{% if author == "foxops" %}
This template was incarnated by foxops.
{% else %}
This template was incarnated by someone else.
{% endif %}
```

#### Loops

To use a loop in a file, you can use the `{% for .. %}` syntax, e.g.:

```jinja
This template was incarnated by:
{% for author in authors %}
* {{ author }}
{% endfor %}
```

To use for loops, you need a [list variable](#list-variables) to get started.

#### ... and much more (includes, macros, assignments, ...)

Consult the [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/templates) documentation for more information.

### Predefined Variables

Foxops comes with a few predefined variables that you can use in every template without explicitly defining them:

* `{{ fengine.template.repository}}` - The path of the template repository
* `{{ fengine.template.repository_version }}` - The version of the template that is being used to render the incarnation
