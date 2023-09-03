# Terminology

Throughout this documentation the following terms are often used and you it's good if you are familiar with them:

**template**: A Git repository which are rendered into *incarnation*. A *template* consists of a `template/` folder and a `fengine.yaml` configuration file.

**incarnation**: A Git repository which is a concrete instance of a rendered *template*. It may or may not contain *customizations* specific to that *incarnation*.

**change**: Represents an update that was performed by foxops on an incarnation repository. For example when updating it to a newer template version or when changing variable values. Every change is assigned a revision number - with the latest change having the highest revision.
