"""Contrato de Pet según la OpenAPI de Petstore v3."""
PET_STATUSES = ("available", "pending", "sold")

# campo -> (tipo esperado, obligatorio)
PET_SCHEMA = {
    "id": (int, False),
    "name": (str, True),
    "category": (dict, False),
    "photoUrls": (list, True),
    "tags": (list, False),
    "status": (str, False),
}
CATEGORY_SCHEMA = {"id": (int, False), "name": (str, False)}
TAG_SCHEMA = {"id": (int, False), "name": (str, False)}


def _check(obj, schema: dict, where: str) -> list[str]:
    if not isinstance(obj, dict):
        return [f"{where}: se esperaba objeto, llegó {type(obj).__name__}"]
    errors = []
    for field, (typ, required) in schema.items():
        if field not in obj:
            if required:
                errors.append(f"{where}.{field}: obligatorio ausente")
            continue
        value = obj[field]
        # bool es subclase de int: se rechaza explícitamente
        if not isinstance(value, typ) or (typ is int and isinstance(value, bool)):
            errors.append(f"{where}.{field}: tipo {type(value).__name__}, esperado {typ.__name__}")
    return errors


def validate_pet(pet, where: str = "pet", deep: bool = True) -> list[str]:
    """Devuelve la lista de violaciones del contrato (vacía si es válido)."""
    errors = _check(pet, PET_SCHEMA, where)
    if not isinstance(pet, dict):
        return errors
    if deep and isinstance(pet.get("category"), dict):
        errors += _check(pet["category"], CATEGORY_SCHEMA, f"{where}.category")
    if deep and isinstance(pet.get("tags"), list):
        for i, tag in enumerate(pet["tags"]):
            errors += _check(tag, TAG_SCHEMA, f"{where}.tags[{i}]")
    if isinstance(pet.get("photoUrls"), list):
        errors += [f"{where}.photoUrls[{i}]: no es str"
                   for i, u in enumerate(pet["photoUrls"]) if not isinstance(u, str)]
    if "status" in pet and pet["status"] not in PET_STATUSES:
        errors.append(f"{where}.status: fuera del enum: {pet['status']!r}")
    return errors
