# Usage

foxops is primarily a command line interface and can be installed by following [these instructions](installation).

## Command Line Interfaces

The foxops Python package will install two console scripts:

* `foxops`: main console script to initialize and update incarnation from a template and interacting with GitLab.
* `fengine`: a lower level console script used by `foxops` to do the heavy lifting around incarnation initialization and updates.
             It's primarily used to develop templates.

## Initialize an Incarnation from a Template

:::{note}
Checkout the [Write Template from Scratch](tutorials/write-template-from-scratch) tutorial to
learn more about templates.
:::

Let's assume you have a template at `https://gitlab.com/my-org/templates/python` with two variables, one is called `name` and one `category`.

The first thing you need to initialize an incarnation is a *desired incarnation state* configuration.
This configuration must be in a YAML file, e.g. `incarnations.yaml`.

The following example configures the incarnation to an already existing Git repository at `my-org/catcam`:

```yaml
incarnations:
  - gitlab_project: my-org/catcam
    template_repository: https://gitlab.com/my-org/templates/python
    template_version: v1.0.0
    template_data:
      name: catcam
      category: utils
```

foxops can now be used to *reconcile* the incarnation from the actual to the desired state given the above config:

```sh
foxops reconcile incarnations.yaml
```

## Update an Incarnation

When an update to the template was made it's sometimes worthwhile to update the incarnation to reflect these changes, too.
The same `foxops reconcile` command as for the [initialization](#initialize-an-incarnation-from-a-template) can be used
for an update.

The only thing which may change is the `template_version` or `template_data` values.
Using the following *desired incarnation state* configuration to change to the update template version `v2.0.0` and change
the category from `utils` to `extras`:

```yaml
incarnations:
  - gitlab_project: my-org/catcam
    template_repository: https://gitlab.com/my-org/templates/python
    template_version: v2.0.0
    template_data:
      name: catcam
      category: extras
```

To perform the actual update, run `foxops` again:

```sh
foxops reconcile incarnations.yaml
```

An update will always create a Merge Request on the incarnation repository with the changes, ready to be reviewed and merged.

In case the update wasn't successful because of conflicts between the template and the incarnation the Merge Request will
reflect that.

You may add an `automerge: true` option to the incarnation configuration so that the update Merge Request is automatically merged.

## Local Development

The `fengine` CLI tool is especially useful when you're working on a template,
as it allows you to quickly create or update an incarnation locally to test your changes.

### Bootstrap a Template

fengine is able to bootstrap a new template in a folder you specify, e.g. to create a new template in the `catcam` folder,
run the following command:

```sh
fengine new catcam
```

This will scaffold the following structure:

* `fengine.yaml`: a basic template configuration file with a predefined `author` variable.
* `template/README.md`: a markdown template file which will render the string `Created by {{ author }}` to the incarnation
                        whereas `{{ author }}` will be replaced by the actual value fo the incarnation.

To create a proper template we will initialize the `catcam` directory as Git repository and create a commit and first tag:

```sh
git init catcam
cd catcam
git add .
git commit -a -m 'Initial commit'
git tag v1.0.0
```

### Initialize an Incarnation

The `fengine initialize` command can be used to create a local incarnation of a template.
To create an incarnation in the `mycat` folder from the `catcam` template created in [Bootstrap a Template](#bootstrap-a-template)
with the `author` name `Albert Einstein` use the following command:

```sh
fengine initialize catcam/ --template-version v1.0.0 mycat -d author="Albert Einstein"
```

This will create the `mycat/` folder and render the file `README.md` with the contents:

```txt
Created by Albert Einstein
```

In addition, it also render a special file called `.fengine.yaml` which is owned by foxops
and shouldn't be manually edited. It's sole purpose is to calculate updates and have a reference
to the underlying template and its version.
It may look something like this:

```yaml
# This file is auto-generated and owned by foxops.
# DO NOT EDIT MANUALLY.
template_data:
  author: Albert Einstein
template_repository: /Users/.../catcam
template_repository_version: v1.0.0
template_repository_version_hash: 437b0efc7c6515e1ec613d08ce70a9a1d84fe7dc
```

### Update an incarnation

Let's assume the template as updated and a `v2.0.0` version exists
and is available in the local `catcam` template directory.

You can update the `mycat` incarnation using the following command:

```sh
fengine update mycat/ -u v2.0.0
```

You may also provide other values for the template data like the `author` variable.

## `default.fvars` File

In addition to configuring the `template_data` in the desired incarnation state configuration,
variable values can be provided in the `default.fvars` file located in the target incarnation directory.

The file format is in `key=value` pairs (like `.env` files), e.g.:

```ini
author=Jon
age=42
```

### Behavior details

Foxops will submit a Merge Request during incarnation initialization in the case the repository
is not empty.
If the incarnation repository only contains a `default.fvars` file, it's considered empty and
no Merge Request will be submitted.
