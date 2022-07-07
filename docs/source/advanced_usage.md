# Advanced Usage

## Authentication to Git Repositories

tbd.

## Deployment of foxops

Foxops is typically deployed in a GitLab CI pipeline. The fundamental approach here is to also use the GitOps principle for the configuration of your desired template incarnations.

As a general approach we would recommend to setup the Git repository like this:

```text
/v1/
.gitlab-ci.yml
```

The `v1` folder is here to indicate that the contained incarnation definition files follow the foxops v1 schema. It will help to future-proof the repository, in case future versions of foxops will bring breaking changes.

In the GitLab CI pipeline, the `foxops reconcile v1/` command can be used, to ensure that all incarnations match the desired state as defined in the files within the `v1/` directory.

### Example .gitlab-ci.yaml

Do note that foxops requires a GitLab API token. For the example above this token must be present in the `GITLAB_API_TOKEN` environment variable.

```yaml
variables:
  FOXOPS_VERSION: "1"
  FOXOPS_GITLAB_TOKEN: $GITLAB_API_TOKEN
  FILES_TO_RECONCILE: v1/

stages:
  - run

reconcile:
  stage: run

  # resource_group prevents parallel executions of foxops.
  # This can be removed, to allow executing multiple "foxops reconcile" runs in parallel
  # => at the risk of undefined behavior, if multiple commits affecting the same files
  #    are created in short intervals
  resource_group: main

  image:
    name: ghcr.io/roche/foxops:$FOXOPS_VERSION
    entrypoint: [""]

  # only run on the default branch
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'

  # logic that collects the files that were added/modified in the commit.
  # improves the execution speed of `foxops reconcile` by only running it on those files
  before_script:
    - |
      if [[ -z ${FILES_TO_RECONCILE} ]];then
        FILES_TO_RECONCILE=()

        for file in $(git diff-tree -M --diff-filter=AM --no-commit-id --name-only -r "${CI_COMMIT_SHA}"); do
          if [[ "${file}" =~ ^(v1|v0.7).*\.(yaml|yml)$ ]] ; then
            FILES_TO_RECONCILE[${#FILES_TO_RECONCILE[@]}]="${file}"
          fi
        done
      fi

      echo "Files to reconcile: ${FILES_TO_RECONCILE[@]}"

  # gitlab-runners apparently always use `-e` causing the real `foxops` exit code
  # to be ignored and always use `1` instead. We have to manually handle it ourselves.
  script:
    - |
      if [[ ${#FILES_TO_RECONCILE[@]} == 0 ]];then
       echo "No incarnation configuration changes, skip running foxops reconcile ..."

       exit 0
      fi

      foxops reconcile ${FILES_TO_RECONCILE[@]} || EXIT_CODE=$?

      exit $EXIT_CODE

  # foxops exists with code `2` if a reconciliation failed in a "known" way,
  # and with `1` if it fails with an unhandled exceptions.
  allow_failure:
    exit_codes:
      - 2
```
