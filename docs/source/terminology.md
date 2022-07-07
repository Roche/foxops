# Terminology

Throughout this documentation the following terms are often used and you it's good if you are familiar with them:

**template**: A Git repository which are rendered into *incarnation*. A *template* consists of a `template/` folder and a `fengine.yaml` configuration file.

**incarnation**: A Git repository which is a concrete instance of a rendered *template*. It may or may not contain *customizations* specific to that *incarnation*.

**reconcile**: The process of bringing a set of incarnations to a desired state in terms of the template, template version and template variables.
