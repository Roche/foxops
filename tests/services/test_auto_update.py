from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from foxops.database.repositories.change.model import (
    ChangeType,
    IncarnationWithChangesSummary,
)
from foxops.services.auto_update import AutoUpdateService
from foxops.services.change import (
    ChangeRejectedDueToNoChanges,
    ChangeRejectedDueToPreviousUnfinishedChange,
)


def _make_incarnation(
    id: int = 1,
    auto_update_interval_seconds: int = 3600,
    requested_version: str = "main",
) -> IncarnationWithChangesSummary:
    return IncarnationWithChangesSummary(
        id=id,
        incarnation_repository="repo/incarnation",
        target_directory=".",
        template_repository="repo/template",
        auto_update_interval_seconds=auto_update_interval_seconds,
        revision=1,
        type=ChangeType.DIRECT,
        commit_sha="abc123",
        requested_version=requested_version,
        merge_request_id=None,
        created_at=datetime.now(timezone.utc),
    )


async def _as_async_iter(items):
    for item in items:
        yield item


@pytest.fixture
def change_service():
    svc = MagicMock()
    svc.create_change_merge_request = AsyncMock()
    return svc


@pytest.fixture
def change_repository():
    repo = MagicMock()
    return repo


@pytest.fixture
def auto_update_service(change_service, change_repository):
    return AutoUpdateService(change_service=change_service, change_repository=change_repository)


async def test_skips_incarnation_with_zero_interval(auto_update_service, change_service, change_repository):
    incarnation = _make_incarnation(auto_update_interval_seconds=0)
    change_repository.list_incarnations_with_changes_summary = MagicMock(return_value=_as_async_iter([incarnation]))

    await auto_update_service.run_once()

    change_service.create_change_merge_request.assert_not_called()


async def test_skips_incarnation_not_yet_due(auto_update_service, change_service, change_repository):
    incarnation = _make_incarnation(auto_update_interval_seconds=3600)
    change_repository.list_incarnations_with_changes_summary = MagicMock(return_value=_as_async_iter([incarnation]))
    # Record a last_run that is only 10 seconds ago
    auto_update_service._last_run[incarnation.id] = datetime.now(timezone.utc) - timedelta(seconds=10)

    await auto_update_service.run_once()

    change_service.create_change_merge_request.assert_not_called()


async def test_triggers_change_for_due_incarnation(auto_update_service, change_service, change_repository):
    incarnation = _make_incarnation(auto_update_interval_seconds=3600, requested_version="main")
    change_repository.list_incarnations_with_changes_summary = MagicMock(return_value=_as_async_iter([incarnation]))
    # Never run before — last_run defaults to epoch, so it's always due

    await auto_update_service.run_once()

    change_service.create_change_merge_request.assert_awaited_once_with(
        incarnation_id=incarnation.id,
        requested_version="main",
        requested_data={},
        automerge=True,
        patch=True,
    )


async def test_updates_last_run_after_successful_change(auto_update_service, change_service, change_repository):
    incarnation = _make_incarnation(auto_update_interval_seconds=3600)
    change_repository.list_incarnations_with_changes_summary = MagicMock(return_value=_as_async_iter([incarnation]))

    before = datetime.now(timezone.utc)
    await auto_update_service.run_once()
    after = datetime.now(timezone.utc)

    last_run = auto_update_service._last_run[incarnation.id]
    assert before <= last_run <= after


async def test_updates_last_run_when_no_changes(auto_update_service, change_service, change_repository):
    incarnation = _make_incarnation(auto_update_interval_seconds=3600)
    change_repository.list_incarnations_with_changes_summary = MagicMock(return_value=_as_async_iter([incarnation]))
    change_service.create_change_merge_request.side_effect = ChangeRejectedDueToNoChanges()

    await auto_update_service.run_once()

    assert incarnation.id in auto_update_service._last_run


async def test_does_not_update_last_run_when_previous_change_unfinished(
    auto_update_service, change_service, change_repository
):
    incarnation = _make_incarnation(auto_update_interval_seconds=3600)
    change_repository.list_incarnations_with_changes_summary = MagicMock(return_value=_as_async_iter([incarnation]))
    change_service.create_change_merge_request.side_effect = ChangeRejectedDueToPreviousUnfinishedChange()

    await auto_update_service.run_once()

    assert incarnation.id not in auto_update_service._last_run
