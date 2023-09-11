from pydantic import BaseModel, ConfigDict

from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.hosters import Hoster


class Incarnation(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str

    model_config = ConfigDict(from_attributes=True)


class IncarnationService:
    def __init__(self, incarnation_repository: IncarnationRepository, hoster: Hoster) -> None:
        self.incarnation_repository = incarnation_repository
        self.hoster = hoster

    async def create(
        self,
        incarnation_repository: str,
        target_directory: str,
        template_repository: str,
    ) -> Incarnation:
        # verify that the incarnation repository exists
        await self.hoster.get_repository_metadata(incarnation_repository)

        # TODO: verify that the target directory is empty
        # TODO: verify that the template repository exists

        incarnation_in_db = await self.incarnation_repository.create(
            incarnation_repository=incarnation_repository,
            target_directory=target_directory,
            template_repository=template_repository,
        )
        return Incarnation.model_validate(incarnation_in_db)

    async def get_by_id(self, id_: int) -> Incarnation:
        incarnation_in_db = await self.incarnation_repository.get_by_id(id_)
        return Incarnation.model_validate(incarnation_in_db)

    async def delete(self, incarnation: Incarnation) -> None:
        await self.incarnation_repository.delete_by_id(incarnation.id)
