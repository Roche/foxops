import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def set_settings_env(static_api_token: str):
    os.environ["FOXOPS_GITLAB_ADDRESS"] = "https://nonsense.com/api/v4"
    os.environ["FOXOPS_GITLAB_TOKEN"] = "nonsense"
    os.environ["FOXOPS_STATIC_TOKEN"] = static_api_token
