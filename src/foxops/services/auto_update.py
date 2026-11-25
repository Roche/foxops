import asyncio
from datetime import datetime, timezone

from foxops.database.repositories.change.repository import ChangeRepository
from foxops.logger import get_logger
from foxops.services.change import (
    ChangeRejectedDueToNoChanges,
    ChangeRejectedDueToPreviousUnfinishedChange,
    ChangeService,
)

logger = get_logger("auto_update")


class AutoUpdateService:
    def __init__(self, change_service: ChangeService, change_repository: ChangeRepository) -> None:
        self._change_service = change_service
        self._change_repository = change_repository
        self._last_run: dict[int, datetime] = {}

    async def run_once(self) -> None:
        now = datetime.now(timezone.utc)
        async for incarnation in self._change_repository.list_incarnations_with_changes_summary():
            if incarnation.auto_update_interval_seconds == 0:
                continue

            last_run = self._last_run.get(incarnation.id, datetime.min.replace(tzinfo=timezone.utc))
            elapsed = (now - last_run).total_seconds()
            if elapsed < incarnation.auto_update_interval_seconds:
                continue

            log = logger.bind(
                incarnation_id=incarnation.id,
                incarnation_repository=incarnation.incarnation_repository,
                target_directory=incarnation.target_directory,
                requested_version=incarnation.requested_version,
            )
            try:
                await self._change_service.create_change_merge_request(
                    incarnation_id=incarnation.id,
                    requested_version=incarnation.requested_version,
                    requested_data={},
                    automerge=True,
                    patch=True,
                )
                log.info("auto-update triggered")
            except ChangeRejectedDueToNoChanges:
                log.debug("auto-update: already up to date")
            except ChangeRejectedDueToPreviousUnfinishedChange:
                log.debug("auto-update: previous change still in progress, will retry")
                continue
            except Exception:
                log.exception("auto-update failed")
                continue

            self._last_run[incarnation.id] = now

    async def run_loop(self, tick_seconds: int = 60) -> None:
        while True:
            await self.run_once()
            await asyncio.sleep(tick_seconds)
