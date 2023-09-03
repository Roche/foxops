# Write a Template from Scratch

A valid template that can be used by fengine only consists of a few components:

* A Git repository in which the template resides.
* A `fengine.yaml` file that contains the templates metadata.
* A `template/` subdirectory that contains the files that should be rendered into the incarnation.

## Create a New Template

To initialize a new, empty template you need to create the elements described in the list above.
If you're lazy, just use the following set of bash commands to do that:

```shell
# create template scaffolding
fengine new mytemplate

# initialize git repository
git init
git commit -am 'initial commit'
```

Be aware that only the files within the `template/` directory will be rendered into the incarnation.
Therefore you can use the root directory of the template Git repository to place other subdirectories or files for documentation,
tests or a CI configuration file for the template repository itself.

## Template Configuration

In the above section you've just created an empty template configuration in the `fengine.yaml` file.
There are a few things you can configure for a template:

### Template Variables

Probably the most important template configuration are *variables* or *template data*.
Every template can have zero or more variables that it must define in the `fengine.yaml` file
and which can be used in files inside the `template/` folder. When an incarnation is being rendered
these variables are being substituted in the defined places.

:::{tip}
foxops uses [Jinja](https://jinja.palletsprojects.com/) to render the template files, including
the variables.
:::

Variables can be defined with the following syntax:

```yaml
variables:
    <variable_1_name>:
        type: str | int | float
        description: <some description for this variable>
        default: <an optional default value>
```

The values in `<>` are meant to be replaced, for example to define a variable called `name` of type `string`
with the default `Jane Doe` use the following:

```yaml
variables:
    name:
        type: str
        description: The name of the author
        default: Jane Doe
```

## Exclude Files from Rendering

Sometimes you don't want to render every file in `template/`, but only copy&paste them as-is
to the incarnation. You can use the `exclude_files` field to list the files you don't want
to have render with Jinja.

For example to exclude the files `template/dummy` and all `*.txt` files in `template/` from rendering
use the following config:

```yaml
exclude_files:
    - 'dummy'
    - '*.txt'

variables:
    ...
```

## Change an Existing Template

Nothing special to consider here. Just change the files in the repository and commit to git as normal.

As best practice we recommend to version your template on the main branch using git tags like `v1.2.0` (for example following [semantic versioning](https://semver.org/) or [calendar versioning](https://calver.org/)). Especially in production environments it's strongly recommended to always specify exact version numbers (= git tags) when reconciling incarnations with foxops.

:::{tip}
Learn [here](backwards-compatible-template-changes) how to make template changes in a backwards-compatible way.
:::
