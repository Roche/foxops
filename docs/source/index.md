```{toctree}
:hidden:
:maxdepth: 2

installation
usage
tutorials/index
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: References

terminology
configfile_reference
api
```

# foxops - Templates for Git Repositories

**foxops** helps to initialize Git repositories (or a subdirectory of a Git repository) with a file structure coming from a template.

* It does not only cover initialization, but also helps to keep these "incarnations" up-to-date with any further changes that were applied to the template afterwards
* ... even when the incarnation was customized in the meantime!

:::{note}
Before continuing to read this documentation, make sure to familiarize yourself with the foxops [terminology](terminology).
:::

```{mermaid}
graph LR
    template-->repo1(repo1)
    template-->repo2a(repo2/subdir_a)
    template-->repo2b(repo2/subdir_b)
    template-->...
```

## Components

The foxops tool is split into two components:

* **fengine** is the underlying templating engine which works with _local_ Git repositories for templates and incarnations. Internally it uses [Jinja](https://jinja.palletsprojects.com/) to render the templates.
* **foxops** is the tool on top of fengine that provides a REST API to manage incarnations hosted on GitLab

## Quick Start

First let's create an *incarnation* for my `catcam` Python application based on a Python *template*:

```bash
curl --json '{
  "incarnation_repository": "my-org/catcam",
  "template_repository": https://gitlab.com/my-org/templates/python",
  "template_version": "v1.0.0",
  "template_data": {
    "package_name": "catcam"
  }
}' https://example.com/api/incarnations
```

Once the incarnation initialization finished, you'll have a nice Merge Request in the `my-org/catcam`
Git repository.

:::{tip}
Checkout the [Write Template from Scratch](tutorials/write-template-from-scratch) and
the general [Usage](usage) guides for more detailed information about how to use
foxops and fengine.
:::

## Example Usecases

### A Zoo of Microservices

Imagine a company creating an application based on a large number of microservices that are all (or mostly) built on top of a single tech stack. Like Python. If these microservices are all living in a multi-repository Git structure, there are a bunch of files that are very similar, but need to be replicated in every Git repository. Namely things like CI configuration, basic directory structure and build scripts.

For example the CI configuration in all these repositories needs to be kept up-to-date with the latest best-practices inside the company, which typically results in a lot of manual copy & paste or just having vastly different setups for every microservice.

### GitOps with Multiple Environments

Classical GitOps has a 1:1 mapping of Git Repositories to pieces of infrastructure. FoxOps is a great match if a number of similar environments needs to be maintained, i.e. a prod and staging environment. Or if a separate environment must be created for every customer.

In such cases it is often advantageous to have separate Git repositories, one for every environment - as that would allow to quickly deploy hotfixes to individual environments if necessary.
