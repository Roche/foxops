# type: ignore

from pathlib import Path

import pytest
import tenacity

from foxops.engine import IncarnationState
from foxops.engine.models import TemplateConfig
from foxops.errors import RetryableError
from foxops.external.gitlab import AsyncGitlabClient, GitlabNotFoundException
from foxops.models import (
    DesiredIncarnationStateConfig,
    IncarnationRemoteGitRepositoryState,
    yaml,
)
from foxops.v1_reconciliation import (
    ReconciliationState,
    get_actual_incarnation_state,
    reconcile,
    reconcile_project,
)


@pytest.fixture()
def gitlab_client_mock(mocker):
    gitlab_client = mocker.AsyncMock(
        name="GitLab Client AsyncMock", spec=AsyncGitlabClient
    )
    gitlab_client.token = None
    return gitlab_client


@pytest.mark.asyncio
async def test_project_state_if_gitlab_project_does_not_exist(
    mocker, gitlab_client_mock
):
    # GIVEN
    gitlab_client_mock.project_get.side_effect = GitlabNotFoundException(message="any")

    # WHEN
    actual_project_state = await get_actual_incarnation_state(
        gitlab_client_mock, mocker.Mock()
    )

    # THEN
    assert actual_project_state is None


@pytest.mark.asyncio
async def test_project_state_if_gitlab_project_exists_but_no_template(
    mocker, gitlab_client_mock
):
    # GIVEN
    gitlab_client_mock.project_get.return_value = {
        "id": 1,
        "default_branch": "main",
        "http_url_to_repo": "some.url",
    }
    gitlab_client_mock.project_repository_files_get_content.side_effect = (
        GitlabNotFoundException(message="any")
    )

    # WHEN
    actual_project_state = await get_actual_incarnation_state(
        gitlab_client_mock, mocker.Mock(target_directory=Path("dir"))
    )

    # THEN
    assert actual_project_state.gitlab_project_id == 1
    assert actual_project_state.remote_url == "some.url"
    assert actual_project_state.default_branch == "main"
    assert actual_project_state.incarnation_directory == Path("dir")


@pytest.mark.asyncio
async def test_project_state_with_content_template_if_template_initialized(
    mocker, gitlab_client_mock
):
    # GIVEN
    gitlab_client_mock.project_get.return_value = {
        "id": 1,
        "default_branch": "main",
        "http_url_to_repo": "some.url",
    }
    gitlab_client_mock.project_repository_files_get_content.return_value = b"""
template_data:
  author: John Doe
  three: '3'
template_repository: any-repository-url
template_repository_version: any-version
template_repository_version_hash: any-version-hash
"""

    # WHEN
    actual_project_state = await get_actual_incarnation_state(
        gitlab_client_mock, mocker.Mock(target_directory=Path("dir"))
    )

    # THEN
    assert (
        actual_project_state.incarnation_state.template_repository
        == "any-repository-url"
    )
    assert (
        actual_project_state.incarnation_state.template_repository_version
        == "any-version"
    )
    assert actual_project_state.incarnation_state.template_data == {
        "author": "John Doe",
        "three": "3",
    }


@pytest.mark.asyncio
async def test_reconcile_project_should_fail_if_project_does_not_exist(
    mocker, gitlab_client_mock
):
    # GIVEN
    desired_incarnation_state_config = DesiredIncarnationStateConfig(
        gitlab_project="any-project",
        template_repository="any-repository",
        template_repository_version="any-version",
        template_data={},
    )
    mocker.patch(
        "foxops.reconciliation.get_actual_incarnation_state",
        return_value=None,
    )

    # WHEN
    reconciliation_state = await reconcile_project(
        gitlab_client_mock, desired_incarnation_state_config
    )

    # THEN
    assert reconciliation_state is ReconciliationState.FAILED


@pytest.mark.asyncio
async def test_reconciliation_should_warn_that_templates_cannot_be_changed(
    mocker,
    gitlab_client_mock,
):
    # GIVEN
    actual_incarnation_state = IncarnationRemoteGitRepositoryState(
        gitlab_project_id=1,
        remote_url="any-url",
        default_branch="any-branch",
        incarnation_directory=Path("dir"),
        incarnation_state=IncarnationState(
            template_repository="any-repository",
            template_repository_version="any-version",
            template_repository_version_hash="any-version-hash",
            template_data={},
        ),
    )
    desired_incarnation_state = DesiredIncarnationStateConfig(
        gitlab_project="any-project",
        target_directory=Path("dir"),
        template_repository="ANOTHER-repository",
        template_repository_version="any-version",
        template_data={},
    )
    mocker.patch(
        "foxops.reconciliation.get_actual_incarnation_state",
        return_value=actual_incarnation_state,
    )
    mocker.patch("foxops.reconciliation.TemporaryGitRepository")

    # WHEN
    reconciliation_state = await reconcile_project(
        gitlab_client_mock, desired_incarnation_state
    )

    # THEN
    assert reconciliation_state is ReconciliationState.UNSUPPORTED


@pytest.mark.asyncio
async def test_reconcile_projects_does_not_abort_if_single_project_fails(
    mocker, gitlab_client_mock
):
    # GIVEN
    reconcile_project_mock = mocker.patch("foxops.reconciliation.reconcile_project")
    desired_incarnation_state_configs = [
        DesiredIncarnationStateConfig(
            gitlab_project="first-project",
            target_directory=Path("dir"),
            template_repository="any-repository",
            template_repository_version="any-version",
            template_data={},
        ),
        DesiredIncarnationStateConfig(
            gitlab_project="second-project",
            target_directory=Path("dir"),
            template_repository="any-repository",
            template_repository_version="any-version",
            template_data={},
        ),
        DesiredIncarnationStateConfig(
            gitlab_project="third-project",
            target_directory=Path("dir"),
            template_repository="any-repository",
            template_repository_version="any-version",
            template_data={},
        ),
    ]

    reconcile_project_mock.side_effect = [
        Exception("boohoo"),
        ReconciliationState.CHANGED,
        ReconciliationState.UNCHANGED,
    ]

    # WHEN
    reconciliation_states = await reconcile(
        gitlab_client_mock,
        desired_incarnation_state_configs,
        parallelism=1,
    )

    # THEN
    assert reconciliation_states == [
        ReconciliationState.FAILED,
        ReconciliationState.CHANGED,
        ReconciliationState.UNCHANGED,
    ]


@pytest.mark.asyncio
async def test_reconcile_project_should_not_require_change_when_default_variable_is_used(
    mocker, gitlab_client_mock
):
    """
    Verify that no change is required when reconciliation is performed without specifying
    an optional variable which is recorded in the actual state with the default value.
    """
    # GIVEN
    desired_incarnation_state_config = DesiredIncarnationStateConfig(
        gitlab_project="any-project",
        template_repository="any-repository",
        template_repository_version="any-version",
        template_data={},
    )
    actual_incarnation_state_config = IncarnationRemoteGitRepositoryState(
        gitlab_project_id=1,
        remote_url="any-url",
        default_branch="any-branch",
        incarnation_directory=Path("dir"),
        incarnation_state=IncarnationState(
            template_repository="any-repository",
            template_repository_version="any-version",
            template_repository_version_hash="any-version-hash",
            template_data={"optional": "default"},
        ),
    )
    template_config = """
optional:
    type: str
    description: "Optional variable"
    default: "default"
    """
    mocker.patch(
        "foxops.reconciliation.get_actual_incarnation_state",
        return_value=actual_incarnation_state_config,
    )
    mocker.patch(
        "foxops.engine.update.load_template_config",
        return_value=TemplateConfig(variables=yaml.load(template_config)),
    )
    git_repository_mock = mocker.patch("foxops.reconciliation.TemporaryGitRepository")
    git_repository_mock.return_value.__aenter__.return_value.head.return_value = (
        "any-version-hash"
    )

    # WHEN
    reconciliation_state = await reconcile_project(
        gitlab_client_mock, desired_incarnation_state_config
    )

    # THEN
    assert reconciliation_state is ReconciliationState.UNCHANGED


async def test_project_reconciliation_is_retried_for_retryable_errors(mocker):
    # GIVEN
    uuid_mock = mocker.patch("uuid.uuid4", side_effect=RetryableError)

    # WHEN
    with pytest.raises(tenacity.RetryError):
        await reconcile_project(mocker.MagicMock(), mocker.MagicMock())

    # THEN
    assert uuid_mock.call_count == 4


async def test_project_reconciliation_is_not_retried_for_non_retryable_errors(mocker):
    # GIVEN
    class _TestException(Exception):
        ...

    uuid_mock = mocker.patch("uuid.uuid4", side_effect=_TestException)

    # WHEN
    with pytest.raises(_TestException):
        await reconcile_project(mocker.MagicMock(), mocker.MagicMock())

    # THEN
    assert uuid_mock.call_count == 1
