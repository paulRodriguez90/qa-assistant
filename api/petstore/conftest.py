"""Fixtures del servicio Petstore (API pública compartida, solo lectura)."""
import os

import pytest

from api.petstore.clients.pet_client import PetClient
from api.petstore.schemas.pet import validate_pet

BASE_URL = os.getenv("PETSTORE_BASE_URL", "https://petstore3.swagger.io/api/v3")
REQUEST_TIMEOUT_MS = 15_000
MAX_KNOWN_PET_CANDIDATES = 10


def _new_context(playwright, api_key: str = ""):
    headers = {"Accept": "application/json"}
    if api_key:
        headers["api_key"] = api_key
    return playwright.request.new_context(
        base_url=BASE_URL + "/", extra_http_headers=headers, timeout=REQUEST_TIMEOUT_MS
    )


@pytest.fixture(scope="session")
def api_context(playwright):
    # La spec declara api_key; el token (si existe) solo viene del entorno.
    ctx = _new_context(playwright, os.getenv("PETSTORE_API_TOKEN", ""))
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def anon_context(playwright):
    """Contexto sin credenciales, para pruebas de seguridad."""
    ctx = _new_context(playwright)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def pets(api_context) -> PetClient:
    return PetClient(api_context)


@pytest.fixture(scope="session")
def anon_pets(anon_context) -> PetClient:
    return PetClient(anon_context)


@pytest.fixture(scope="session")
def pet_candidates(pets) -> list[dict]:
    """Pets reales de findByStatus que cumplen el contrato (sin crear datos).

    El servicio es compartido: se descartan los pets contaminados por otros usuarios.
    """
    resp = pets.find_by_status("available")
    assert resp.status == 200, f"findByStatus devolvió {resp.status}"
    candidates = [p for p in resp.json() if "id" in p and validate_pet(p) == []]
    if not candidates:
        pytest.skip("No hay pets 'available' válidos en el servicio compartido")
    return candidates


@pytest.fixture
def known_pet(pets, pet_candidates) -> dict:
    """Pet válido confirmado con un GET justo antes de cada test.

    Evita usar un pet que otro usuario borró o modificó durante la sesión
    (daría 404 y un xfail por la razón equivocada).
    """
    for candidate in pet_candidates[:MAX_KNOWN_PET_CANDIDATES]:
        resp = pets.get(candidate["id"])
        if resp.status == 200 and validate_pet(resp.json()) == []:
            return resp.json()
    pytest.skip("Ningún pet candidato sigue disponible y válido en el servicio compartido")
