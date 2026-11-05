"""Factories de datos para el formulario de checkout (paso 1) de Sauce Demo.

Sin Faker: los valores son listas fijas y explícitas, así que son 100% reproducibles
(no hay azar ni semilla) y no se agrega ninguna dependencia. Todos son ficticios.
"""


def build_checkout_info(**overrides) -> dict:
    """Datos válidos por defecto; sobrescribe un solo campo por test."""
    info = {"first_name": "Ana", "last_name": "Prueba", "postal_code": "12345"}
    info.update(overrides)
    return info
