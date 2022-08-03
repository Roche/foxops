import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def set_settings_env():
    os.environ["FOXOPS_GITLAB_ADDRESS"] = "https://nonsense.com/api/v4"
    os.environ["FOXOPS_GITLAB_TOKEN"] = "nonsense"
