# Reset incarnation
There is an option to reset an incarnation by removing all customizations that were done to it and bring it back to
a pristine state as if it was just created freshly from the template.

By default, the target version and data is taken from the last change that was successfully applied
to the incarnation, but they can be overridden. For the data, partial overrides are also allowed.

## Ignore some files from reset
Sometimes, you want to keep some files in the incarnation that were created or modified after the initial
creation of the incarnation. For example, you might have a `pipeline.yaml` which is created by different process.
To achieve this, you can create a file called `.foxops-reset-ignore` in the root of your template. It would propagate it
to the root of your incarnation repository.

This file should contain a list of file paths (one per line) that should be ignored during the reset process.