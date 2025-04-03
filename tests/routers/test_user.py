from httpx import AsyncClient

from foxops.database.repositories.user.repository import UserRepository
from foxops.models.user import User


async def test_cant_delete_own_user(
    api_client: AsyncClient, user_repository: UserRepository, priviliged_api_user: User
):
    response = await api_client.delete(
        f"/user/{priviliged_api_user.id}",
    )

    assert response.status_code == 400
    assert response.json() == {
        "message": "You can't delete yourself",
    }

    # The user should still exist
    await user_repository.get_by_id(priviliged_api_user.id)
