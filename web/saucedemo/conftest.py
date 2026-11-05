"""Fixtures de Sauce Demo (https://www.saucedemo.com). Aplican solo a web/saucedemo/."""
import os

import pytest

BASE_URL = os.getenv("SAUCEDEMO_BASE_URL", "https://www.saucedemo.com")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def credentials() -> dict:
    return {
        "user": os.getenv("SAUCEDEMO_USER", "standard_user"),
        "password": os.getenv("SAUCEDEMO_PASSWORD", "secret_sauce"),
    }
