from fastapi import APIRouter, Depends

from foxops.dependencies import get_template_service
from foxops.services.template import TemplateService

router = APIRouter(prefix="/api/templates", tags=["template"])


@router.get("/variables")
async def get_template_variables(
    template_repository: str,
    template_version: str,
    template_service: TemplateService = Depends(get_template_service),
):
    return await template_service.get_template_variables(template_repository, template_version)
