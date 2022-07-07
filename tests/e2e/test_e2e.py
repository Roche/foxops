import os
import shutil
import subprocess
import textwrap
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator

import pytest
from aiopath import AsyncPath
from dictdiffer import diff
from ruamel.yaml import YAML

from foxops.external.git import GitRepository, TemporaryGitRepository, git_exec
from foxops.external.gitlab import GitlabNotFoundException
from foxops.logging import get_logger
from foxops.reconciliation import generate_foxops_branch_name
from tests.e2e.helpers import (
    GITLAB_BASE_GROUP_ID,
    ExtendedAsyncGitlabClient,
    GitlabTestGroup,
)

yaml = YAML(typ="safe")


logger = get_logger(__name__)


@dataclass(frozen=True)
class TemplateRepo:
    gitlab_project: dict[str, Any]
    version: str
    temporary_git_repository: TemporaryGitRepository
    local_temporary_git_repository: GitRepository


@pytest.fixture(scope="function")
async def gitlab_token_test():
    return os.environ["GITLAB_TEST_TOKEN"]


@pytest.fixture(scope="function")
async def gitlab_address_test():
    return os.environ["FOXOPS_GITLAB_ADDRESS"]


@pytest.fixture(scope="function")
async def gitlab_client(gitlab_token_test, gitlab_address_test):
    try:

        client = ExtendedAsyncGitlabClient(
            token=gitlab_token_test, base_url=gitlab_address_test
        )
        yield client

        await client.session.close()
    except Exception as exc:
        print(exc)


@pytest.fixture(scope="function")
async def unique_test_id():
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
async def gitlab_test_group(
    gitlab_client: ExtendedAsyncGitlabClient,
    unique_test_id: str,
):
    test_group = await gitlab_client.group_create(
        group_name=unique_test_id,
        group_path=unique_test_id,
        parent_id=GITLAB_BASE_GROUP_ID,
    )

    logger.info(
        f"created test group {unique_test_id} (GitLab Group Id: {test_group['id']})"
    )

    yield GitlabTestGroup(test_group["id"], test_group["full_path"])

    await gitlab_client.group_delete(test_group["id"])
    logger.info(
        f"deleted test group {unique_test_id} (GitLab Group Id: {test_group['id']})"
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_in_root_of_empty_incarnation(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation in the root of an incarnation repository."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_files_in_repository(
        branch=incarnation_repository_project["default_branch"],
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[(Path("README.md"), """Jon is of age 18""")],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_with_fvars(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation with fvars."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )
    async with incarnation_customization(
        incarnation_repository_project, gitlab_token_test
    ) as local_temporary_incarnation_repository:
        (local_temporary_incarnation_repository.directory / "default.fvars").write_text(
            "author=Jon"
        )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_files_in_repository(
        branch=incarnation_repository_project["default_branch"],
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[(Path("README.md"), """Jon is of age 18""")],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_in_root_of_nonempty_incarnation(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation in the root of an incarnation repository."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=True,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    rev_before_reconcile = await gitlab_client.get_branch_revision(
        incarnation_repository_project["path_with_namespace"],
        incarnation_repository_project["default_branch"],
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    rev_after_reconcile = await gitlab_client.get_branch_revision(
        incarnation_repository_project["path_with_namespace"],
        incarnation_repository_project["default_branch"],
    )

    # THEN
    expected_initialization_branch = generate_foxops_branch_name(
        "initialize-to", Path("."), "v1.0.0"
    )
    existing_branches = await gitlab_client.project_repository_branches_list(
        incarnation_repository_project["path_with_namespace"],
        expected_initialization_branch,
    )
    assert len(existing_branches) == 1
    assert existing_branches[0]["name"] == expected_initialization_branch
    await assert_files_in_repository(
        branch=expected_initialization_branch,
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[(Path("README.md"), """Jon is of age 18""")],
        gitlab_client=gitlab_client,
    )

    assert rev_before_reconcile == rev_after_reconcile


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_with_automerge_in_root_of_nonempty_incarnation(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation in the root of an incarnation repository."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=True,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
            automerge=True,
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    rev_before_reconcile = await gitlab_client.get_branch_revision(
        incarnation_repository_project["path_with_namespace"],
        incarnation_repository_project["default_branch"],
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    rev_after_reconcile = await gitlab_client.get_branch_revision(
        incarnation_repository_project["path_with_namespace"],
        incarnation_repository_project["default_branch"],
    )

    # THEN
    await assert_files_in_repository(
        branch=incarnation_repository_project["default_branch"],
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[(Path("README.md"), """Jon is of age 18""")],
        gitlab_client=gitlab_client,
    )

    assert rev_before_reconcile != rev_after_reconcile


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_in_root_of_nonempty_incarnation_with_fvars(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation in the root of an incarnation repository."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=True,
    )
    async with incarnation_customization(
        incarnation_repository_project, gitlab_token_test
    ) as local_temporary_incarnation_repository:
        (local_temporary_incarnation_repository.directory / "default.fvars").write_text(
            "author=Jon"
        )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    rev_before_reconcile = await gitlab_client.get_branch_revision(
        incarnation_repository_project["path_with_namespace"],
        incarnation_repository_project["default_branch"],
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    rev_after_reconcile = await gitlab_client.get_branch_revision(
        incarnation_repository_project["path_with_namespace"],
        incarnation_repository_project["default_branch"],
    )

    # THEN
    expected_initialization_branch = generate_foxops_branch_name(
        "initialize-to", Path("."), "v1.0.0"
    )
    existing_branches = await gitlab_client.project_repository_branches_list(
        incarnation_repository_project["path_with_namespace"],
        expected_initialization_branch,
    )
    assert len(existing_branches) == 1
    assert existing_branches[0]["name"] == expected_initialization_branch
    await assert_files_in_repository(
        branch=expected_initialization_branch,
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[(Path("README.md"), """Jon is of age 18""")],
        gitlab_client=gitlab_client,
    )

    assert rev_before_reconcile == rev_after_reconcile


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_with_wrong_variables_errors(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can not be initialized as incarnation if the template data doesn't match."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon"},  # missing `age`
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    # THEN
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        # WHEN
        reconcile(
            desired_incarnation_state_config_path,
            gitlab_address_test,
            gitlab_token_test,
            tmp_path,
        )

    assert (
        "the template required the variables ['age', 'author'] but the provided template data for the incarnation where ['author']."
        in excinfo.value.output.decode("utf-8")
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_in_subdir_incarnation(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation in a sub directory within an incarnation repository."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("subdir"),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_files_in_repository(
        branch=incarnation_repository_project["default_branch"],
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[(Path("subdir/README.md"), """Jon is of age 18""")],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_initialize_template_in_subdirs_incarnation(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that a template can be initialized as incarnation in multiple sub directories within an incarnation repository."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )
    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    # there's an existing subdir incarnation in the repo already
    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("subdir1"),
        )
    )

    with TemporaryDirectory() as tmp_path2:
        tmp_path2 = Path(tmp_path2)

        desired_incarnation_state_config_path = Path(tmp_path2, "incarnations.yaml")
        desired_incarnation_state_config_path.write_text(
            "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
        )

        reconcile(
            desired_incarnation_state_config_path,
            gitlab_address_test,
            gitlab_token_test,
            tmp_path2,
        )

    # this is the subdir incarnation which should be added
    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Ygritte", "age": "17"},
            incarnation_target_directory=Path("subdir2"),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )

    # WHEN
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_files_in_repository(
        branch=incarnation_repository_project["default_branch"],
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[
            (Path("subdir2/README.md"), """Ygritte is of age 17"""),
        ],
        gitlab_client=gitlab_client,
    )
    await assert_files_in_repository(
        branch=incarnation_repository_project["default_branch"],
        repository=incarnation_repository_project["path_with_namespace"],
        expected_files=[
            (Path("subdir1/README.md"), """Jon is of age 18"""),
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_change_single_file(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation can be updated when single file in template changed."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).write_text("{{ author }} is of age {{ age }}. UPDATED, fuck yeah.")
    await create_template_version(
        template_repository=template_repository,
        new_template_version="v2.0.0",
        gitlab_client=gitlab_client,
    )
    # FIXME(TF): oh my ... don't @ me.
    desired_incarnation_state_config_path.write_text(
        desired_incarnation_state_config_path.read_text().replace(
            "template_repository_version: v1.0.0",
            "template_repository_version: v2.0.0",
        )
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_merge_request_with_file_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        expected_incarnation_merge_request_changes=[
            {
                "old_path": "README.md",
                "new_path": "README.md",
                "diff": """
@@ -1 +1 @@
-Jon is of age 18
\\ No newline at end of file
+Jon is of age 18. UPDATED, fuck yeah.
\\ No newline at end of file
""".lstrip(),
            },
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_change_single_file_with_fvars_change(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation can be updated when single file changed because of fvars update."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )
    async with incarnation_customization(
        incarnation_repository_project, gitlab_token_test
    ) as local_temporary_incarnation_repository:
        (local_temporary_incarnation_repository.directory / "default.fvars").write_text(
            "author=Jon"
        )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    async with incarnation_customization(
        incarnation_repository_project, gitlab_token_test
    ) as local_temporary_incarnation_repository:
        (local_temporary_incarnation_repository.directory / "default.fvars").write_text(
            "author=Jon the overridden"
        )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_merge_request_with_file_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        expected_incarnation_merge_request_changes=[
            {
                "old_path": "README.md",
                "new_path": "README.md",
                "diff": """
@@ -1 +1 @@
-Jon is of age 18
\\ No newline at end of file
+Jon the overridden is of age 18
\\ No newline at end of file
""".lstrip(),
            },
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_delete_single_file(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation can be updated when single file in template was deleted."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).unlink()
    await create_template_version(
        template_repository=template_repository,
        new_template_version="v2.0.0",
        gitlab_client=gitlab_client,
    )
    # FIXME(TF): oh my ... don't @ me.
    desired_incarnation_state_config_path.write_text(
        desired_incarnation_state_config_path.read_text().replace(
            "template_repository_version: v1.0.0",
            "template_repository_version: v2.0.0",
        )
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_merge_request_with_file_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        expected_incarnation_merge_request_changes=[
            {
                "old_path": "README.md",
                "deleted_file": True,
                "diff": """
@@ -1 +0,0 @@
-Jon is of age 18
\\ No newline at end of file
""".lstrip(),
            },
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_rename_single_file(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation can be updated when single file in template was renamed."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).rename(
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "NEW_README.md"
    )
    await create_template_version(
        template_repository=template_repository,
        new_template_version="v2.0.0",
        gitlab_client=gitlab_client,
    )
    # FIXME(TF): oh my ... don't @ me.
    desired_incarnation_state_config_path.write_text(
        desired_incarnation_state_config_path.read_text().replace(
            "template_repository_version: v1.0.0",
            "template_repository_version: v2.0.0",
        )
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_merge_request_with_file_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        expected_incarnation_merge_request_changes=[
            {
                "old_path": "README.md",
                "new_path": "NEW_README.md",
                "diff": "",
            },
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_change_same_file_template_incarnation(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation can be updated when single file in template changed which also changed the same way in the incarnation."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).write_text("{{ author }} is of age {{ age }}. UPDATED, fuck yeah.")
    await create_template_version(
        template_repository=template_repository,
        new_template_version="v2.0.0",
        gitlab_client=gitlab_client,
    )
    async with incarnation_customization(
        incarnation_repository_project, gitlab_token_test
    ) as local_temporary_incarnation_repository:
        (local_temporary_incarnation_repository.directory / "README.md").write_text(
            "Jon is of age 18. UPDATED, fuck yeah."
        )

    # FIXME(TF): oh my ... don't @ me.
    desired_incarnation_state_config_path.write_text(
        desired_incarnation_state_config_path.read_text().replace(
            "template_repository_version: v1.0.0",
            "template_repository_version: v2.0.0",
        )
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    changes = await get_merge_request_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        gitlab_client=gitlab_client,
    )
    assert all(x["old_path"] != "README.md" for x in changes)


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_moving_branch_name(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation can be updated when template version is a moving branch."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    # NOTE(TF): actually make the incarnation point to the branch instead of the tag
    patched_template_repository = TemplateRepo(
        gitlab_project=template_repository.gitlab_project,
        version=template_repository.gitlab_project["default_branch"],
        temporary_git_repository=template_repository.temporary_git_repository,
        local_temporary_git_repository=template_repository.local_temporary_git_repository,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=patched_template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        patched_template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).write_text("{{ author }} is of age {{ age }}. UPDATED, fuck yeah.")
    await create_template_version(
        template_repository=patched_template_repository,
        new_template_version=None,  # we don't want a new tag
        gitlab_client=gitlab_client,
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    await assert_merge_request_with_file_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        expected_incarnation_merge_request_changes=[
            {
                "old_path": "README.md",
                "new_path": "README.md",
                "diff": """
@@ -1 +1 @@
-Jon is of age 18
\\ No newline at end of file
+Jon is of age 18. UPDATED, fuck yeah.
\\ No newline at end of file
""".lstrip(),
            },
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_with_conflict_is_correctly_detected_and_presented(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation update with a conflict is correctly detected and presented."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).write_text("{{ author }} is of age '{{ age }}'")
    await create_template_version(
        template_repository=template_repository,
        new_template_version="v2.0.0",
        gitlab_client=gitlab_client,
    )
    async with incarnation_customization(
        incarnation_repository_project, gitlab_token_test
    ) as local_temporary_incarnation_repository:
        (local_temporary_incarnation_repository.directory / "README.md").write_text(
            "Jon is of age 30"
        )

    # FIXME(TF): oh my ... don't @ me.
    desired_incarnation_state_config_path.write_text(
        desired_incarnation_state_config_path.read_text().replace(
            "template_repository_version: v1.0.0",
            "template_repository_version: v2.0.0",
        )
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    merge_request = await get_merge_request_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        gitlab_client=gitlab_client,
    )
    assert merge_request["state"] != "merged"
    assert merge_request["merge_when_pipeline_succeeds"] is False
    assert "CONFLICT" in merge_request["title"]
    assert "README.md" in merge_request["description"]
    assert "conflict" in merge_request["description"]
    assert "rejection files" in merge_request["description"]

    await assert_merge_request_with_file_changes_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        expected_incarnation_merge_request_changes=[
            {
                "old_path": "README.md.rej",
                "new_path": "README.md.rej",
            },
        ],
        gitlab_client=gitlab_client,
    )


@pytest.mark.non_gherkin
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_incarnation_mr_is_automerged(
    gitlab_client, gitlab_test_group, gitlab_address_test, gitlab_token_test, tmp_path
):
    """Verify that an incarnation Merge Request is automerged if configured as such."""
    # GIVEN
    template_repository = await setup_template_repository(
        template_repository_name="template",
        template_version="v1.0.0",
        template_files=[(Path("README.md"), """{{ author }} is of age {{ age }}""")],
        template_variables={"author": "str", "age": "int"},
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        gitlab_token_test=gitlab_token_test,
    )

    incarnation_repository_project = await setup_incarnation_repository(
        incarnation_repository_name="incarnation",
        gitlab_client=gitlab_client,
        gitlab_test_group=gitlab_test_group,
        initialize_with_readme=False,
    )

    desired_incarnation_state_config = (
        await setup_incarnation_from_template_in_repository(
            template_repository=template_repository,
            incarnation_repository_project=incarnation_repository_project,
            incarnation_variables={"author": "Jon", "age": "18"},
            incarnation_target_directory=Path("."),
            automerge=True,
        )
    )
    desired_incarnation_state_config_path = Path(tmp_path, "incarnations.yaml")
    desired_incarnation_state_config_path.write_text(
        "incarnations:\n" + textwrap.indent(desired_incarnation_state_config, "  ")
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # WHEN
    (
        template_repository.local_temporary_git_repository.directory
        / "template"
        / "README.md"
    ).write_text("{{ author }} is of age {{ age }}. UPDATED, fuck yeah.")
    await create_template_version(
        template_repository=template_repository,
        new_template_version="v2.0.0",
        gitlab_client=gitlab_client,
    )
    # FIXME(TF): oh my ... don't @ me.
    desired_incarnation_state_config_path.write_text(
        desired_incarnation_state_config_path.read_text().replace(
            "template_repository_version: v1.0.0",
            "template_repository_version: v2.0.0",
        )
    )
    reconcile(
        desired_incarnation_state_config_path,
        gitlab_address_test,
        gitlab_token_test,
        tmp_path,
    )

    # THEN
    assert await get_merge_request_in_incarnation(
        incarnation_repository=incarnation_repository_project["path_with_namespace"],
        gitlab_client=gitlab_client,
        state="merged",
    )


async def setup_template_repository(
    template_repository_name: str,
    template_version: str,
    template_files: list[tuple[Path, str]],
    template_variables: dict[str, str],
    gitlab_client,
    gitlab_test_group,
    gitlab_token_test,
) -> TemplateRepo:
    logger.info("setup template repository")

    project = await gitlab_client.project_create(
        group_id=gitlab_test_group.id,
        path=template_repository_name,
        initialize_with_readme=True,
    )
    logger.debug(f"created template repository at {project['path_with_namespace']}")

    logger.debug("clone template repository to add template files")
    temporary_git_repository = TemporaryGitRepository(
        logger=logger,
        source=project["http_url_to_repo"],
        username="__token__",
        password=gitlab_token_test,
    )
    local_temporary_git_repository = await temporary_git_repository.__aenter__()
    await git_exec(
        "switch",
        project["default_branch"],
        cwd=local_temporary_git_repository.directory,
    )
    logger.debug(
        f"cloned template repository into {local_temporary_git_repository.directory}"
    )

    for template_file_path, template_file_contents in template_files:
        path = AsyncPath(
            local_temporary_git_repository.directory / "template" / template_file_path
        )
        await path.parent.mkdir(parents=True, exist_ok=True)
        await path.write_text(template_file_contents)

    foxops_config_path = local_temporary_git_repository.directory / "fengine.yaml"
    foxops_config = {
        "required_foxops_version": "v1.0.0",
        "variables": {
            k: {"type": v, "description": "nope"} for k, v in template_variables.items()
        },
    }
    with foxops_config_path.open("w") as f:
        yaml.dump(foxops_config, f)

    await local_temporary_git_repository.commit_all(message="Initial commit")
    await local_temporary_git_repository.push()
    logger.debug("committed and pushed template repository")

    await gitlab_client.tag_create(
        project["id"], template_version, project["default_branch"]
    )
    await git_exec("push", "--tags", cwd=local_temporary_git_repository.directory)
    logger.debug(f"created and pushed tag {template_version} in template repository")

    return TemplateRepo(
        gitlab_project=project,
        version=template_version,
        temporary_git_repository=temporary_git_repository,
        local_temporary_git_repository=local_temporary_git_repository,
    )


async def create_template_version(
    template_repository: TemplateRepo,
    new_template_version: str | None,
    gitlab_client,
) -> TemplateRepo:
    logger.info("create template version")

    await template_repository.local_temporary_git_repository.commit_all(
        message="Initial commit"
    )
    await template_repository.local_temporary_git_repository.push()
    logger.debug("committed and pushed template repository")

    if new_template_version is not None:
        await gitlab_client.tag_create(
            template_repository.gitlab_project["id"],
            new_template_version,
            template_repository.gitlab_project["default_branch"],
        )
        await git_exec(
            "push",
            "--tags",
            cwd=template_repository.local_temporary_git_repository.directory,
        )
        logger.debug(
            f"created and pushed tag {new_template_version} in template repository"
        )

    return TemplateRepo(
        gitlab_project=template_repository.gitlab_project,
        version=(
            new_template_version
            if new_template_version is not None
            else template_repository.version
        ),
        temporary_git_repository=template_repository.temporary_git_repository,
        local_temporary_git_repository=template_repository.local_temporary_git_repository,
    )


async def setup_incarnation_repository(
    incarnation_repository_name,
    gitlab_client,
    gitlab_test_group,
    initialize_with_readme: bool,
):
    logger.info("setup incarnation repository")

    project = await gitlab_client.project_create(
        group_id=gitlab_test_group.id,
        path=incarnation_repository_name,
        initialize_with_readme=initialize_with_readme,
    )
    return project


async def setup_incarnation_from_template_in_repository(
    template_repository: TemplateRepo,
    incarnation_repository_project,
    incarnation_target_directory: Path,
    incarnation_variables: dict[str, str],
    automerge: bool = False,
) -> str:
    logger.info("setup incarnation from template in repository")

    desired_incarnation_state_config = f"""
- gitlab_project: {incarnation_repository_project['path_with_namespace']}
  target_directory: {incarnation_target_directory}
  automerge: {'true' if automerge else 'false'}
  template_repository: {template_repository.gitlab_project["http_url_to_repo"]}
  template_repository_version: {template_repository.version}
  template_data:
{os.linesep.join(f"{' ' * 4}{key}: {value}" for key, value in incarnation_variables.items())}
    """

    logger.debug(
        f"create incarnation repository at {incarnation_repository_project['path_with_namespace']}"
    )
    return desired_incarnation_state_config


@asynccontextmanager
async def incarnation_customization(
    incarnation_repository_project, gitlab_token_test
) -> AsyncGenerator[GitRepository, None]:
    logger.info("incarnation customization")

    async with TemporaryGitRepository(
        logger=logger,
        source=incarnation_repository_project["http_url_to_repo"],
        username="__token__",
        password=gitlab_token_test,
    ) as local_temporary_incarnation_repository:
        yield local_temporary_incarnation_repository

        await local_temporary_incarnation_repository.commit_all(message="customization")
        await local_temporary_incarnation_repository.push()
        logger.debug("committed and pushed incarnation repository customization")


def reconcile(
    desired_incarnation_state_config_path: Path,
    gitlab_address_test: str,
    gitlab_token_test: str,
    tmp_path: Path,
):
    logger.info("reconcile incarnations")
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
                str(desired_incarnation_state_config_path),
            ],
            env={
                "FOXOPS_GITLAB_ADDRESS": gitlab_address_test,
                "FOXOPS_GITLAB_TOKEN": gitlab_token_test,
                "PATH": os.environ[
                    "PATH"
                ],  # foxops, coverage etc. might not be installed system wide
            },
            cwd=tmp_path,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(f"reconcile failed with {exc.returncode} logs:")
        print(exc.output.decode("utf-8"))
        raise

    reconciliation_result = reconcile_output.decode("utf-8")
    logger.debug("Reconciliation logs:")
    print(reconciliation_result)

    # copy coverage files to current test execution directory
    coverage_file_target_path = Path.cwd()
    for coverage_file in tmp_path.glob(".coverage.*"):
        logger.debug(
            "copy coverage file to test execution directory",
            filename=coverage_file.name,
            target=coverage_file_target_path,
        )
        shutil.move(coverage_file, coverage_file_target_path)

    return reconciliation_result


async def assert_files_in_repository(
    branch: str,
    repository: Path,
    expected_files: list[tuple[Path, str]],
    gitlab_client,
):
    logger.info("asserting files in repository")

    for (
        expected_file_path,
        expected_file_contents,
    ) in expected_files:
        logger.debug(f"checking if file contents of `{expected_file_path}` match ...")
        try:
            actual_file_contents: bytes = (
                await gitlab_client.project_repository_files_get_content(
                    id_=repository,
                    branch=branch,
                    filepath=expected_file_path,
                )
            )
        except GitlabNotFoundException:
            logger.error(
                f"file `{expected_file_path}` not found in incarnation on branch `{branch}` of repository `{repository}`"
            )
            raise
        else:
            assert actual_file_contents.decode("utf-8") == expected_file_contents


async def get_merge_request_in_incarnation(
    incarnation_repository: Path,
    gitlab_client: ExtendedAsyncGitlabClient,
    state="opened",
):
    merge_requests = await gitlab_client.project_merge_requests_list(
        incarnation_repository,
        state=state,
    )
    assert len(merge_requests) == 1, "Only single merge request expected"
    return merge_requests[0]


async def get_merge_request_changes_in_incarnation(
    incarnation_repository: Path,
    gitlab_client: ExtendedAsyncGitlabClient,
) -> list:
    merge_request = await get_merge_request_in_incarnation(
        incarnation_repository=incarnation_repository, gitlab_client=gitlab_client
    )

    changes = (
        await gitlab_client.project_merge_request_changes(
            incarnation_repository,
            merge_request["iid"],
        )
    )["changes"]
    return changes


async def assert_merge_request_with_file_changes_in_incarnation(
    incarnation_repository: Path,
    expected_incarnation_merge_request_changes,
    gitlab_client,
):
    changes = await get_merge_request_changes_in_incarnation(
        incarnation_repository, gitlab_client
    )
    for expected_change in expected_incarnation_merge_request_changes:
        actual_change = next(
            (c for c in changes if c["old_path"] == expected_change["old_path"]), None
        )
        assert (
            actual_change is not None
        ), f"Change `{expected_change['old_path']}` not found. Changes are {changes=}"

        diffs = list(
            diff(
                actual_change,
                expected_change,
            )
        )
        diffs = [d for d in diffs if d[0] != "remove"]
        assert diffs == [], f"Diff is {diffs=}. Changes are {changes=}"
