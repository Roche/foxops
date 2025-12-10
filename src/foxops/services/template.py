from foxops.engine.models.template_config import TemplateConfig
from foxops.hosters import Hoster


class TemplateService:
    def __init__(self, hoster: Hoster) -> None:
        self.hoster = hoster

    async def get_template_variables(self, template_repository: str, template_version: str) -> dict[str, str]:
        async with self.hoster.cloned_repository(template_repository, refspec=template_version) as repo:
            template_config = TemplateConfig.from_path(repo.directory / "fengine.yaml")

        return {k: v.get("default", "") for k, v in template_config.model_dump().get("variables", {}).items()}
