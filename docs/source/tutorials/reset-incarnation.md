# Reset incarnation
There is an option to reset an incarnation by removing all customizations that were done to it and bring it back to
a pristine state as if it was just created freshly from the template.

By default, the target version and data is taken from the last change that was successfully applied
to the incarnation, but they can be overridden. For the data, partial overrides are also allowed.

## Ignore some files from reset
Sometimes, you want to keep some files in the incarnation that were created or modified after the initial
creation of the incarnation. For example, you might have a `pipeline.yaml` which is created by different process.
To achieve this, you can create a file called `.fengine-reset-ignore` in the root of your template. It would propagate it
to the root of your incarnation repository.

This file should contain a list of file paths (one per line) that should be ignored during the reset process.

### Examples

#### Ignoring top-level files and directories

To ignore files or directories at the root level:

```
pipeline.yaml
config/
.env
```

This will preserve `pipeline.yaml`, the entire `config/` directory, and `.env` during reset.

#### Ignoring specific nested files

You can also ignore specific files within directories while still allowing other files in the same directory to be reset:

```
example/file1
config/secrets.yaml
src/generated/api.py
```

With this configuration:
- `example/file1` is preserved, but `example/file2` would be deleted
- `config/secrets.yaml` is preserved, but other files in `config/` would be deleted
- `src/generated/api.py` is preserved, but other files in `src/generated/` would be deleted

#### Combining top-level and nested exclusions

You can mix both styles:

```
.env
config/
src/custom/special_file.py
docs/generated/api-reference.md
```

This will:
- Preserve the entire `config/` directory
- Preserve `.env` at the root
- Preserve only `special_file.py` in `src/custom/` (other files in that directory will be deleted)
- Preserve only `api-reference.md` in `docs/generated/` (other files will be deleted)

