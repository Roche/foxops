import asyncio
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ruamel.yaml import YAML

from foxops.external.git import GitRepository, TemporaryGitRepository, git_exec
from tests.e2e.helpers import (
    GITLAB_BASE_GROUP_ID,
    ExtendedAsyncGitlabClient,
    GitlabTestGroup,
)

yaml = YAML(typ="safe")


@pytest.fixture(scope="session")
def loop():
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    yield _loop
    _loop.close()


@pytest.fixture(scope="session")
def gitlab_token_test():
    return os.environ["GITLAB_TEST_TOKEN"]


@pytest.fixture(scope="session")
def gitlab_address_test():
    return os.environ["FOXOPS_GITLAB_ADDRESS"]


@pytest.fixture(scope="session")
def gitlab_client(
    loop: asyncio.AbstractEventLoop, gitlab_token_test, gitlab_address_test
):
    try:

        async def create_client():
            return ExtendedAsyncGitlabClient(
                token=gitlab_token_test, base_url=gitlab_address_test
            )

        client = loop.run_until_complete(create_client())
        yield client
        loop.run_until_complete(client.session.close())
    except Exception as exc:
        print(exc)


@pytest.fixture(scope="function")
def unique_test_id():
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def gitlab_test_group(
    loop: asyncio.AbstractEventLoop,
    gitlab_client: ExtendedAsyncGitlabClient,
    unique_test_id: str,
    logger,
):
    test_group = loop.run_until_complete(
        gitlab_client.group_create(
            group_name=unique_test_id,
            group_path=unique_test_id,
            parent_id=GITLAB_BASE_GROUP_ID,
        )
    )
    logger.info(
        f"created test group {unique_test_id} (GitLab Group Id: {test_group['id']})"
    )

    yield GitlabTestGroup(test_group["id"], test_group["full_path"])

    loop.run_until_complete(gitlab_client.group_delete(test_group["id"]))
    logger.info(
        f"deleted test group {unique_test_id} (GitLab Group Id: {test_group['id']})"
    )


@dataclass
class TemplateRepo:
    gitlab_project: dict[str, Any]
    tmp_local_git_repository: TemporaryGitRepository
    local_git_repository: GitRepository


@scenario(
    "Reconciliation.feature",
    "Update incarnation repository when new template version exists",
)
def test_update_incarnation_repository_when_new_template_version_exists():
    """Update incarnation repository when new template version exists."""
    pass


@scenario(
    "Reconciliation.feature", "Update incarnation repository when template data changed"
)
def test_update_incarnation_repository_when_template_data_changed():
    """Update incarnation repository when template data changed."""
    pass


@given(
    parsers.parse('I have a template repository at "{gitops_template_repo_name:S}"'),
    target_fixture="template_repo",
)
def i_have_a_template_repository_at_gitopstemplate(
    loop: asyncio.AbstractEventLoop,
    gitops_template_repo_name,
    gitlab_client,
    gitlab_test_group,
    gitlab_token_test,
    logger,
):
    """I have a template repository at "gitops-template"."""
    project_create_task = gitlab_client.project_create(
        group_id=gitlab_test_group.id,
        path=gitops_template_repo_name,
        initialize_with_readme=True,
    )
    project = loop.run_until_complete(project_create_task)
    logger.debug(f"created template repo project at {project['id']}")

    tmp_local_git_repository = TemporaryGitRepository(
        logger=logger,
        source=project["http_url_to_repo"],
        username="__token__",
        password=gitlab_token_test,
    )
    local_git_repository = loop.run_until_complete(
        tmp_local_git_repository.__aenter__()
    )
    loop.run_until_complete(
        git_exec(
            "switch",
            project["default_branch"],
            cwd=local_git_repository.directory,
        )
    )
    logger.debug(f"cloned template repository into {local_git_repository.directory}")

    shutil.copytree(
        "tests/e2e/testdata/template-repo",
        local_git_repository.directory,
        dirs_exist_ok=True,
    )
    logger.debug("copied template-repo template into local template-repo directory")

    loop.run_until_complete(local_git_repository.commit_all(message="Initial commit"))
    loop.run_until_complete(local_git_repository.push())
    logger.debug("committed and pushed template-repo contents to GitLab")

    loop.run_until_complete(
        gitlab_client.tag_create(project["id"], "v0.0.1", project["default_branch"])
    )
    loop.run_until_complete(
        git_exec("push", "--tags", cwd=local_git_repository.directory)
    )
    logger.debug("created tag v0.0.1")

    return TemplateRepo(
        gitlab_project=project,
        tmp_local_git_repository=tmp_local_git_repository,
        local_git_repository=local_git_repository,
    )


@given(
    parsers.parse('I want an incarnation repository at "{gitops_repo_name:S}"'),
    target_fixture="gitops_desired_incarnation_states",
)
def i_want_an_incarnation_repository_at_gitopsrepo(
    gitops_repo_name,
    gitlab_client,
    gitlab_test_group,
    loop: asyncio.AbstractEventLoop,
    template_repo,
):
    """I want an incarnation repository at "gitops-repo"."""

    project_create_task = gitlab_client.project_create(
        group_id=gitlab_test_group.id,
        path=gitops_repo_name,
        initialize_with_readme=False,
    )
    loop.run_until_complete(project_create_task)

    desired_incarnation_states = f"""
incarnations:
  - gitlab_project: {gitlab_test_group.path}/{gitops_repo_name}
    template_repository: {template_repo.gitlab_project['http_url_to_repo']}
    template_repository_version: v0.0.1
    template_data:
      name: {gitops_repo_name}
      version: v1.0.0
"""
    return desired_incarnation_states


@given("I reconcile", target_fixture="reconciliation_result")
@when("I reconcile", target_fixture="reconciliation_result")
def i_reconcile(
    gitlab_address_test,
    gitlab_token_test,
    gitops_desired_incarnation_states,
    tmp_path,
    logger,
):
    """I reconcile."""
    project_definition_config = tmp_path / "incarnaions.yaml"
    project_definition_config.write_text(gitops_desired_incarnation_states)

    try:
        reconcile_output = subprocess.check_output(
            [
                "coverage",
                "run",
                "--parallel-mode",
                "--branch",
                "--source",
                "foxops",
                "--module",
                "foxops",
                "--verbose",
                "--json-logs",
                "reconcile",
                "--parallelism",
                "1",
                str(project_definition_config),
            ],
            env={
                "FOXOPS_GITLAB_ADDRESS": gitlab_address_test,
                "FOXOPS_GITLAB_TOKEN": gitlab_token_test,
                # FIXME(TF): "foxops" and "copier" might not be installed into the system,
                #            and therefore not in shells default `$PATH`, but in a virtualenv
                #            which's bin path is injected in `$PATH` in the currently running shell,
                #            therefore we pass along the `$PATH`.
                "PATH": os.environ["PATH"],
            },
        )
    except subprocess.CalledProcessError as exc:
        logger.error(f"reconcile failed with {exc.returncode} logs:")
        print(exc.output.decode("utf-8"))
        raise

    reconciliation_result = reconcile_output.decode("utf-8")
    logger.debug("Reconciliation logs:")
    print(reconciliation_result)
    return reconciliation_result


@when(
    parsers.parse(
        'I update the template repository at "{gitops_template_repo_name:S}"'
    ),
    target_fixture="update_in_template_repo",
)
def i_update_the_template_repository_at_gitopstemplate(
    loop: asyncio.AbstractEventLoop,
    gitops_template_repo_name: str,
    template_repo: TemplateRepo,
    gitlab_client,
    logger,
):
    """I update the template repository at "gitops-template"."""
    subprocess.check_call(
        "echo 'NEW FILE CONTENT' > template/UPDATE.md",
        shell=True,
        cwd=template_repo.local_git_repository.directory,
    )
    logger.debug(
        f"added UPDATE.md file to template repository at {template_repo.local_git_repository.directory}"
    )
    loop.run_until_complete(
        template_repo.local_git_repository.commit_all(message="Update")
    )
    loop.run_until_complete(template_repo.local_git_repository.push())
    loop.run_until_complete(
        gitlab_client.tag_create(
            template_repo.gitlab_project["id"],
            "v0.0.2",
            template_repo.gitlab_project["default_branch"],
        )
    )
    loop.run_until_complete(
        git_exec("push", "--tags", cwd=template_repo.local_git_repository.directory)
    )
    logger.debug("created tag v0.0.2")
    return {"new_version": "v0.0.2", "new_file": Path("UPDATE.md")}


@when(
    parsers.parse(
        'I want the updated template for the repository at "{gitops_repo_name:S}"'
    ),
    target_fixture="gitops_desired_incarnation_states",
)
def i_want_the_updated_template_for_the_repository_at_gitopsrepo(
    gitops_repo_name,
    gitlab_test_group,
    template_repo,
    update_in_template_repo,
):
    """I want the updated template for the repository at "gitops-repo"."""
    desired_incarnation_states = f"""
incarnations:
  - gitlab_project: {gitlab_test_group.path}/{gitops_repo_name}
    template_repository: {template_repo.gitlab_project['http_url_to_repo']}
    template_repository_version: {update_in_template_repo["new_version"]}
    template_data:
      name: {gitops_repo_name}
      version: v1.0.0
"""
    return desired_incarnation_states


@then(
    parsers.parse(
        'I should see a new Merge Request with the updates on GitLab at "{gitops_repo_name:S}"'
    )
)
def i_should_see_a_new_merge_request_with_the_updates_on_gitlab_at_gitopsrepo(
    loop: asyncio.AbstractEventLoop,
    gitops_desired_incarnation_states,
    gitlab_client,
    gitlab_token_test,
    update_in_template_repo,
    logger,
):
    """I should see a new Merge Request with the updates on GitLab at "gitops-repo"."""
    # FIXME(TF): limitation that only one project definition is supported
    gitops_repo_path = Path(
        yaml.load(gitops_desired_incarnation_states)["incarnations"][0][
            "gitlab_project"
        ]
    )
    gitops_repo_project = loop.run_until_complete(
        gitlab_client.project_get(gitops_repo_path)
    )
    merge_requests = loop.run_until_complete(
        gitlab_client.project_merge_requests_list(
            gitops_repo_project["id"], state="opened"
        )
    )
    assert len(merge_requests) == 1
    merge_request = merge_requests[0]

    tmp_local_gitops_repository = TemporaryGitRepository(
        logger=logger,
        source=gitops_repo_project["http_url_to_repo"],
        username="__token__",
        password=gitlab_token_test,
        refspec=merge_request["source_branch"],
    )
    local_gitops_repository = loop.run_until_complete(
        tmp_local_gitops_repository.__aenter__()
    )

    try:
        assert (
            local_gitops_repository.directory / update_in_template_repo["new_file"]
        ).is_file()
    finally:
        loop.run_until_complete(tmp_local_gitops_repository.__aexit__(None, None, None))


@when(
    parsers.parse(
        'I change the template data for the "{gitops_repo_name:S}" repository'
    ),
    target_fixture="gitops_desired_incarnation_states",
)
def i_change_the_template_data_for_the_incarnation_repository(
    gitops_repo_name, gitops_desired_incarnation_states
):
    """I change the template data for the "incarnation" repository."""
    # load current project definition
    incarnations = yaml.load(gitops_desired_incarnation_states)
    # change the template data
    incarnations["incarnations"][0]["template_data"]["name"] += "_CHANGED"
    string_stream = StringIO()
    yaml.dump(incarnations, string_stream)
    return string_stream.getvalue()


@then(
    parsers.parse(
        'I should see a new Merge Request with the changes on GitLab at "{gitops_repo_name:S}"'
    )
)
def i_should_see_a_new_merge_request_with_the_changes_on_gitlab_at_incarnation(
    gitops_repo_name,
    gitops_desired_incarnation_states,
    loop: asyncio.AbstractEventLoop,
    gitlab_client,
    gitlab_token_test,
    logger,
):
    """I should see a new Merge Request with the changes on GitLab at "incarnation"."""
    gitops_repo_path = Path(
        yaml.load(gitops_desired_incarnation_states)["incarnations"][0][
            "gitlab_project"
        ]
    )
    gitops_repo_project = loop.run_until_complete(
        gitlab_client.project_get(gitops_repo_path)
    )
    merge_requests = loop.run_until_complete(
        gitlab_client.project_merge_requests_list(
            gitops_repo_project["id"], state="opened"
        )
    )
    assert len(merge_requests) == 1
    merge_request = merge_requests[0]

    tmp_local_gitops_repository = TemporaryGitRepository(
        logger=logger,
        source=gitops_repo_project["http_url_to_repo"],
        username="__token__",
        password=gitlab_token_test,
        refspec=merge_request["source_branch"],
    )
    local_gitops_repository = loop.run_until_complete(
        tmp_local_gitops_repository.__aenter__()
    )
    try:
        with Path(local_gitops_repository.directory, "README.md").open() as readme_file:
            assert f"# Application {gitops_repo_name}_CHANGED" in readme_file.read()
    finally:
        loop.run_until_complete(tmp_local_gitops_repository.__aexit__(None, None, None))
