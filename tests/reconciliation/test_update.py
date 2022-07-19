import os
from contextvars import ContextVar

import pytest
from pytest_mock import MockFixture

import foxops.engine as fengine
from foxops.errors import ReconciliationError
from foxops.external.git import GitRepository, git_exec
from foxops.hosters import Hoster
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    Incarnation,
)
from foxops.reconciliation import update_incarnation


@pytest.mark.asyncio
async def should_not_update_if_branch_is_pending(
    mocker: MockFixture,
    test_dis: DesiredIncarnationState,
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.get_incarnation_state.return_value.template_data = {}
    hoster.has_pending_incarnation_branch.return_value = "any-hash"
    incarnation_mock = mocker.MagicMock(spec=Incarnation)
    incarnation_mock.incarnation_repository = test_dis.incarnation_repository
    incarnation_mock.target_directory = test_dis.target_directory

    dis_patch = DesiredIncarnationStatePatch(
        template_repository_version="v2.0.0", automerge=False
    )

    # WHEN
    update_branch_sha = await update_incarnation(hoster, incarnation_mock, dis_patch)

    # THEN
    assert update_branch_sha == "any-hash"


@pytest.mark.asyncio
async def should_err_if_incarnation_not_initialized(
    mocker: MockFixture,
    test_dis: DesiredIncarnationState,
):
    # GIVEN
    hoster = mocker.MagicMock(spec=Hoster)
    hoster.has_pending_incarnation_branch.return_value = None
    hoster.get_incarnation_state.return_value = None

    incarnation_mock = mocker.MagicMock(spec=Incarnation)
    incarnation_mock.incarnation_repository = test_dis.incarnation_repository
    incarnation_mock.target_directory = test_dis.target_directory

    dis_patch = DesiredIncarnationStatePatch(
        template_repository_version="v2.0.0", automerge=False
    )

    # THEN
    expected_error_msg = "not initialized"
    with pytest.raises(ReconciliationError, match=expected_error_msg):
        # WHEN
        await update_incarnation(hoster, incarnation_mock, dis_patch)


@pytest.mark.asyncio
async def should_update_incarnation_to_new_version_in_merge_request(
    mocker: MockFixture,
    test_template_repository: GitRepository,
    test_initialized_incarnation: tuple[
        Incarnation, fengine.IncarnationState, DesiredIncarnationState, GitRepository
    ],
):
    # GIVEN
    (
        test_incarnation,
        test_incarnation_state,
        _,
        test_incarnation_repository,
    ) = test_initialized_incarnation

    await __add_new_template_version(test_template_repository)

    hoster = mocker.MagicMock(spec=Hoster)
    hoster.has_pending_incarnation_branch.return_value = None
    hoster.get_incarnation_state.return_value = test_incarnation_state
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_incarnation_repository,
        test_template_repository,
    ]

    merge_request_called = ContextVar("merge_request_called", default=False)

    async def __mocked_merge_request(*_, **__):
        merge_request_called.set(True)
        return await test_incarnation_repository.head()

    hoster.merge_request = __mocked_merge_request

    dis_patch = DesiredIncarnationStatePatch(
        template_repository_version="v2.0.0", automerge=False
    )

    # WHEN
    sha = await update_incarnation(hoster, test_incarnation, dis_patch)

    # THEN
    assert sha == (await test_incarnation_repository.head())
    assert (await test_incarnation_repository.current_branch()).startswith(
        "foxops/update-to-"
    )
    assert merge_request_called.get()


@pytest.mark.asyncio
async def should_update_incarnation_to_new_template_data_in_merge_request(
    mocker: MockFixture,
    test_template_repository: GitRepository,
    test_initialized_incarnation: tuple[
        Incarnation, fengine.IncarnationState, DesiredIncarnationState, GitRepository
    ],
):
    # GIVEN
    (
        test_incarnation,
        test_incarnation_state,
        _,
        test_incarnation_repository,
    ) = test_initialized_incarnation

    await __add_new_template_version(test_template_repository)

    hoster = mocker.MagicMock(spec=Hoster)
    hoster.has_pending_incarnation_branch.return_value = None
    hoster.get_incarnation_state.return_value = test_incarnation_state
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_incarnation_repository,
        test_template_repository,
    ]

    merge_request_called = ContextVar("merge_request_called", default=False)

    async def __mocked_merge_request(*_, **__):
        merge_request_called.set(True)
        return await test_incarnation_repository.head()

    hoster.merge_request = __mocked_merge_request

    dis_patch = DesiredIncarnationStatePatch(
        template_data={"name": "new-name"}, automerge=False
    )

    # WHEN
    sha = await update_incarnation(hoster, test_incarnation, dis_patch)

    # THEN
    assert sha == (await test_incarnation_repository.head())
    assert (await test_incarnation_repository.current_branch()).startswith(
        "foxops/update-to-"
    )
    assert merge_request_called.get()


@pytest.mark.asyncio
async def should_no_op_if_there_is_no_update_to_be_done(
    mocker: MockFixture,
    test_template_repository: GitRepository,
    test_initialized_incarnation: tuple[
        Incarnation, fengine.IncarnationState, DesiredIncarnationState, GitRepository
    ],
):
    # GIVEN
    (
        test_incarnation,
        test_incarnation_state,
        _,
        test_incarnation_repository,
    ) = test_initialized_incarnation

    hoster = mocker.MagicMock(spec=Hoster)
    hoster.has_pending_incarnation_branch.return_value = None
    hoster.get_incarnation_state.return_value = test_incarnation_state
    # NOTE: the order here has to match. A better option for the future is to implement
    #       a more sophisticated fake hoster.
    hoster.cloned_repository().__aenter__.side_effect = [
        test_incarnation_repository,
        test_template_repository,
    ]

    dis_patch = DesiredIncarnationStatePatch(automerge=False)

    # WHEN
    sha = await update_incarnation(hoster, test_incarnation, dis_patch)

    # THEN
    assert sha is None
    hoster.merge_request.assert_not_called()


async def __add_new_template_version(template_repository: GitRepository):
    (template_repository.directory / "template" / "file_from_update.txt").write_text(
        "{{ name }}"
    )
    await template_repository.commit_all("New file")
    await git_exec("tag", "v2.0.0", cwd=template_repository.directory)
