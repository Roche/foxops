from contextvars import ContextVar

import pytest
from pytest_mock import MockFixture

import foxops.engine as fengine
from foxops.errors import (
    IncarnationAlreadyInitializedError,
    IncarnationRepositoryNotFound,
    ReconciliationError,
)
from foxops.external.git import GitRepository
from foxops.hosters import Hoster
from foxops.models import DesiredIncarnationState
from foxops.reconciliation import initialize_incarnation


@pytest.mark.asyncio
async def should_err_if_incarnation_repository_does_not_exist(
    mocker: MockFixture, test_dis: DesiredIncarnationState
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.side_effect = IncarnationRepositoryNotFound(
        test_dis.incarnation_repository
    )

    # THEN
    expected_error_msg = "remote Incarnation repository at '.*' doesn't exist"
    with pytest.raises(ReconciliationError, match=expected_error_msg):
        # WHEN
        await initialize_incarnation(hoster, test_dis)


@pytest.mark.asyncio
async def should_err_if_incarnation_is_already_initialized(
    mocker: MockFixture, test_dis: DesiredIncarnationState
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = mocker.MagicMock(
        spec=fengine.IncarnationState,
        template_repository="",
        template_repository_version="",
        template_data={},
    )

    # THEN
    expected_error_msg = "already initialized"
    with pytest.raises(IncarnationAlreadyInitializedError, match=expected_error_msg):
        # WHEN
        await initialize_incarnation(hoster, test_dis)


@pytest.mark.asyncio
async def should_err_if_incarnation_is_already_initialized_reporting_a_config_mismatch(
    mocker: MockFixture, test_dis: DesiredIncarnationState
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = fengine.IncarnationState(
        template_repository="",
        template_repository_version="",
        template_repository_version_hash="",
        template_data={},
    )

    # THEN
    expected_error_msg = "already initialized"
    with pytest.raises(
        IncarnationAlreadyInitializedError, match=expected_error_msg
    ) as exc:
        # WHEN
        await initialize_incarnation(hoster, test_dis)

    assert exc.value.has_mismatch is True


@pytest.mark.asyncio
async def should_err_if_incarnation_is_already_initialized_reporting_no_config_mismatch(
    mocker: MockFixture, test_dis: DesiredIncarnationState
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = fengine.IncarnationState(
        template_repository=test_dis.template_repository,
        template_repository_version=test_dis.template_repository_version,
        template_repository_version_hash="does-not-matter",
        template_data=test_dis.template_data,
    )

    # THEN
    expected_error_msg = "already initialized"
    with pytest.raises(
        IncarnationAlreadyInitializedError, match=expected_error_msg
    ) as exc:
        # WHEN
        await initialize_incarnation(hoster, test_dis)

    assert exc.value.has_mismatch is False


@pytest.mark.asyncio
async def should_initialize_incarnation_without_merge_request(
    mocker: MockFixture,
    test_dis: DesiredIncarnationState,
    test_template_repository: GitRepository,
    test_empty_incarnation_repository: GitRepository,
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = None
    hoster.get_repository_metadata.return_value = {"default_branch": "main"}
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_empty_incarnation_repository,
        test_template_repository,
    ]

    # WHEN
    sha = await initialize_incarnation(hoster, test_dis)

    # THEN
    assert sha == (await test_empty_incarnation_repository.head())
    assert await test_empty_incarnation_repository.current_branch() == "main"
    assert (
        test_empty_incarnation_repository.directory
        / test_dis.target_directory
        / "README.md"
    ).exists()


@pytest.mark.asyncio
async def should_initialize_incarnation_with_merge_request(
    mocker: MockFixture,
    test_dis: DesiredIncarnationState,
    test_template_repository: GitRepository,
    test_non_empty_incarnation_repository: GitRepository,
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = None
    hoster.get_repository_metadata.return_value = {"default_branch": "main"}
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_non_empty_incarnation_repository,
        test_template_repository,
    ]
    hoster.has_pending_incarnation_branch.return_value = None

    merge_request_called = ContextVar("merge_request_called", default=False)

    async def __mocked_merge_request(*_, **__):
        merge_request_called.set(True)
        return await test_non_empty_incarnation_repository.head()

    hoster.merge_request = __mocked_merge_request

    # WHEN
    sha = await initialize_incarnation(hoster, test_dis)

    # THEN
    assert sha == (await test_non_empty_incarnation_repository.head())
    assert (await test_non_empty_incarnation_repository.current_branch()).startswith(
        "foxops/initialize-to-"
    )
    assert (
        test_non_empty_incarnation_repository.directory
        / test_dis.target_directory
        / "README.md"
    ).exists()
    assert merge_request_called.get()


@pytest.mark.asyncio
async def should_not_initialize_with_merge_request_if_branch_is_pending(
    mocker: MockFixture,
    test_dis: DesiredIncarnationState,
    test_template_repository: GitRepository,
    test_non_empty_incarnation_repository: GitRepository,
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = None
    hoster.get_repository_metadata.return_value = {"default_branch": "main"}
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_non_empty_incarnation_repository,
        test_template_repository,
    ]

    async def __mocked_has_pending_incarnation_branch(*_, **__):
        return await test_non_empty_incarnation_repository.head()

    hoster.has_pending_incarnation_branch = __mocked_has_pending_incarnation_branch

    # WHEN
    sha = await initialize_incarnation(hoster, test_dis)

    # THEN
    assert sha == (await test_non_empty_incarnation_repository.head())
    hoster.merge_request.assert_not_called()


@pytest.mark.asyncio
async def should_err_if_fengine_initialization_fails(
    mocker: MockFixture,
    test_dis: DesiredIncarnationState,
    test_template_repository: GitRepository,
    test_empty_incarnation_repository: GitRepository,
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value = None
    hoster.get_repository_metadata.return_value = {"default_branch": "main"}
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_empty_incarnation_repository,
        test_template_repository,
    ]

    # WHEN
    # NOTE: we now have a missing template variable ...
    test_dis.template_data = {}

    # THEN
    with pytest.raises(Exception):
        await initialize_incarnation(hoster, test_dis)
