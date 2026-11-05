"""Tests de GET /pet/* de Petstore v3 (solo lectura sobre una API pública compartida)."""
import pytest

from api.petstore.schemas.pet import PET_STATUSES, validate_pet

NONEXISTENT_ID = 999999999999999
INJECTION = "1' OR '1'='1"
XSS = "<script>alert(1)</script>"


def _tagged_pet(pets):
    """Busca un pet real que tenga tags (sin crear datos); None si no hay."""
    for status in PET_STATUSES:
        resp = pets.find_by_status(status)
        if resp.status != 200:
            continue
        for pet in resp.json():
            tags = pet.get("tags") or []
            if tags and isinstance(tags[0], dict) and tags[0].get("name"):
                return pet
    return None


# ---------- GET /pet/{petId} ----------

@pytest.mark.smoke
def test_get_pet_by_id_returns_200_and_same_id(pets, known_pet):
    """Escenario: Obtener una mascota existente por id"""
    resp = pets.get(known_pet["id"])
    assert resp.status == 200
    assert resp.json()["id"] == known_pet["id"]
    assert resp.json()["name"] == known_pet["name"]


@pytest.mark.regression
def test_get_pet_by_id_matches_contract(pets, known_pet):
    """Escenario: La mascota por id cumple el contrato"""
    resp = pets.get(known_pet["id"])
    assert resp.status == 200
    assert "application/json" in resp.headers["content-type"]
    assert validate_pet(resp.json()) == []


@pytest.mark.regression
def test_get_pet_nonexistent_id_returns_404(pets):
    """Escenario: Id inexistente devuelve 404"""
    resp = pets.get(NONEXISTENT_ID)
    assert resp.status == 404
    assert "not found" in resp.text().lower()


@pytest.mark.regression
def test_get_pet_zero_id_returns_404(pets):
    """Escenario: Id cero devuelve 404"""
    resp = pets.get(0)
    assert resp.status == 404
    assert "not found" in resp.text().lower()


@pytest.mark.regression
@pytest.mark.parametrize("bad_id", ["abc", "1.5", "99999999999999999999999"])
def test_get_pet_invalid_id_returns_400(pets, bad_id):
    """Escenario: Id no numérico devuelve 400"""
    resp = pets.get(bad_id)
    assert resp.status == 400
    body = resp.json()
    assert body["code"] == 400
    assert isinstance(body["message"], str) and body["message"]


@pytest.mark.regression
@pytest.mark.parametrize("payload", [INJECTION, XSS, "../../etc/passwd"])
def test_get_pet_special_chars_id_not_server_error(pets, payload):
    """Escenario: Id con caracteres especiales no provoca error de servidor"""
    resp = pets.get(payload)
    assert resp.status in (400, 404)
    # El mensaje JSON puede reflejar la entrada, pero nunca como HTML.
    assert "text/html" not in resp.headers.get("content-type", "")


# ---------- GET /pet/findByStatus ----------

@pytest.mark.smoke
@pytest.mark.parametrize("status", PET_STATUSES)
def test_find_by_status_valid_returns_pets_with_that_status(pets, status):
    """Escenario: Buscar por status válido"""
    resp = pets.find_by_status(status)
    assert resp.status == 200
    data = resp.json()
    assert isinstance(data, list)
    assert all(p.get("status") == status for p in data)


@pytest.mark.regression
def test_find_by_status_items_have_minimum_structure(pets):
    """Escenario: Buscar por status devuelve pets con la estructura mínima"""
    resp = pets.find_by_status("available")
    assert resp.status == 200
    data = resp.json()
    assert isinstance(data, list) and data
    # Solo campos que asigna la API (id, status): los que escriben otros usuarios
    # pueden venir contaminados y se cubren en el test del 100% (xfail).
    malformed = [
        p for p in data
        if not (isinstance(p, dict) and isinstance(p.get("id"), int) and p.get("status") in PET_STATUSES)
    ]
    assert malformed == []


@pytest.mark.regression
@pytest.mark.xfail(
    reason="Datos contaminados en el servicio compartido: hay pets sin name o con tags que son str "
           "en vez de objeto Tag (la API los acepta y los devuelve)",
    strict=False,
)
def test_find_by_status_all_items_match_contract(pets):
    """Escenario: Buscar por status devuelve pets con el contrato correcto (100% de los elementos)"""
    resp = pets.find_by_status("available")
    assert resp.status == 200
    errors = [e for i, p in enumerate(resp.json()[:50]) for e in validate_pet(p, f"[{i}]")]
    assert errors == []


@pytest.mark.regression
def test_find_by_status_multiple_values_returns_union(pets):
    """Escenario: Buscar por varios status a la vez"""
    resp = pets.find_by_status(["available", "sold"])
    assert resp.status == 200
    data = resp.json()
    assert isinstance(data, list)
    assert {p.get("status") for p in data} <= {"available", "sold"}


@pytest.mark.regression
@pytest.mark.parametrize("bad_status", ["bogus", "AVAILABLE", " "])
def test_find_by_status_invalid_value_returns_400(pets, bad_status):
    """Escenario: Status inválido devuelve 400"""
    resp = pets.find_by_status(bad_status)
    assert resp.status == 400
    body = resp.json()
    assert body["code"] == 400
    assert "status" in body["message"]


@pytest.mark.regression
def test_find_by_status_missing_param_returns_400(pets):
    """Escenario: Status ausente devuelve 400"""
    resp = pets.find_by_status()
    assert resp.status == 400
    body = resp.json()
    assert body["code"] == 400
    assert "status" in body["message"]


@pytest.mark.regression
@pytest.mark.parametrize("payload", ["' OR 1=1--", XSS])
def test_find_by_status_special_chars_returns_400_without_html(pets, payload):
    """Escenario: Status con caracteres especiales es rechazado"""
    resp = pets.find_by_status(payload)
    assert resp.status == 400
    assert "text/html" not in resp.headers.get("content-type", "")


# ---------- GET /pet/findByTags ----------

@pytest.mark.smoke
@pytest.mark.xfail(
    reason="Discrepancia: findByTags responde 500 incluso con un tag existente (spec: 200)",
    strict=True,
)
def test_find_by_tags_existing_tag_returns_matching_pets(pets):
    """Escenario: Buscar por tag existente"""
    pet = _tagged_pet(pets)
    if pet is None:
        pytest.skip("No hay pets con tags en el servicio compartido")
    tag = pet["tags"][0]["name"]
    resp = pets.find_by_tags(tag)
    assert resp.status == 200
    data = resp.json()
    assert isinstance(data, list) and data
    # No se exige el contrato completo: el servicio tiene pets contaminados por otros usuarios.
    assert all(
        tag in [t.get("name") for t in p.get("tags", []) if isinstance(t, dict)] for p in data
    )


@pytest.mark.regression
def test_find_by_tags_missing_param_returns_400(pets):
    """Escenario: Tags ausente devuelve 400"""
    resp = pets.find_by_tags()
    assert resp.status == 400
    body = resp.json()
    assert body["code"] == 400
    assert "tags" in body["message"]


@pytest.mark.regression
def test_find_by_tags_empty_value_returns_400(pets):
    """Escenario: Tags vacío devuelve 400"""
    resp = pets.find_by_tags("")
    assert resp.status == 400
    assert "tags" in resp.text().lower()


@pytest.mark.regression
@pytest.mark.xfail(
    reason="Discrepancia: findByTags responde 500 ante cualquier valor de tags (spec: 200 o 400)",
    strict=True,
)
@pytest.mark.parametrize("payload", [XSS, "' OR 1=1--"])
def test_find_by_tags_special_chars_not_server_error(pets, payload):
    """Escenario: Tags con caracteres especiales no provoca error de servidor"""
    resp = pets.find_by_tags(payload)
    assert resp.status < 500
    assert "<script>" not in resp.text()


# ---------- Seguridad (la spec exige api_key u OAuth2 en estos GET) ----------

@pytest.mark.regression
@pytest.mark.xfail(
    reason="Discrepancia: el demo no exige autenticación; GET sin api_key devuelve 200 (spec: security)",
    strict=True,
)
def test_get_pet_without_api_key_is_rejected(anon_pets, known_pet):
    """Escenario: Petición sin credenciales es rechazada según la spec"""
    resp = anon_pets.get(known_pet["id"])
    assert resp.status in (401, 403)


@pytest.mark.regression
@pytest.mark.xfail(
    reason="Discrepancia: el demo acepta cualquier api_key; con valor inválido devuelve 200",
    strict=True,
)
def test_get_pet_with_invalid_api_key_is_rejected(anon_pets, known_pet):
    """Escenario: api_key inválida es rechazada según la spec"""
    resp = anon_pets.get(known_pet["id"], headers={"api_key": "invalid-key-for-test"})
    assert resp.status in (401, 403)
