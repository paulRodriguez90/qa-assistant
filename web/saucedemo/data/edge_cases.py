"""Casos límite del formulario de checkout, listos para pytest.mark.parametrize.

Cada caso es pytest.param(first, last, postal, id=...). Datos ficticios; las cadenas de
seguridad son payloads inertes de uso común en pruebas.
"""
import pytest

from web.saucedemo.data.factories import build_checkout_info

_OK = build_checkout_info()
_F, _L, _P = _OK["first_name"], _OK["last_name"], _OK["postal_code"]


def _case(case_id: str, **overrides):
    d = build_checkout_info(**overrides)
    return pytest.param(d["first_name"], d["last_name"], d["postal_code"], id=case_id)


# Datos que la app debe aceptar (llegan al paso 2).
VALID_CASES = [
    _case("base_valido"),
    _case("tildes_y_enie", first_name="José Ángel", last_name="Muñoz Peña"),
    _case("dieresis_y_unicode", first_name="Jürgen", last_name="Öztürk-Çelik"),
    _case("apostrofo_y_guion", first_name="Mary-Jane", last_name="O'Brien"),
    _case("un_solo_caracter", first_name="A", last_name="B", postal_code="1"),
    _case("muy_largos_200", first_name="N" * 200, last_name="A" * 200, postal_code="9" * 200),
    _case("muy_largos_1000", first_name="N" * 1000, last_name="A" * 1000, postal_code="9" * 1000),
    _case("espacios_internos", first_name="Ana  María   Luisa", last_name="De la Cruz"),
    _case("emoji", first_name="Ana 😀", last_name="Prueba 🚀"),
    _case("unicode_no_latino", first_name="李", last_name="Иванов"),
    _case("cp_con_letras_uk", postal_code="SW1A 1AA"),
    _case("cp_canada", postal_code="K1A 0B1"),
    _case("cp_brasil", postal_code="01310-100"),
    _case("cp_ceros_izquierda", postal_code="00501"),
    _case("cp_japon", postal_code="100-0001"),
    _case("cp_solo_letras", postal_code="ABCDE"),
    _case("cp_simbolos", postal_code="#12-34/B"),
    _case("cp_negativo_decimal", postal_code="-1.5"),
]

# Un campo obligatorio vacío: (first, last, postal, mensaje de error esperado).
REQUIRED_FIELD_CASES = [
    pytest.param("", _L, _P, "Error: First Name is required", id="first_name_vacio"),
    pytest.param(_F, "", _P, "Error: Last Name is required", id="last_name_vacio"),
    pytest.param(_F, _L, "", "Error: Postal Code is required", id="postal_code_vacio"),
    pytest.param("", "", "", "Error: First Name is required", id="todos_vacios_prioriza_first_name"),
    pytest.param(_F, "", "", "Error: Last Name is required", id="last_y_postal_vacios_prioriza_last_name"),
]

# Solo espacios: la app NO hace trim (se verificó ejecutando); ver test_checkout.py.
WHITESPACE_CASES = [
    _case("first_name_solo_espacios", first_name="   "),
    _case("last_name_solo_espacios", last_name="   "),
    _case("postal_code_solo_espacios", postal_code="   "),
]

# Seguridad básica: no debe ejecutarse script ni romperse la página.
SECURITY_CASES = [
    _case("xss_script", first_name="<script>alert('xss')</script>"),
    _case("xss_img_onerror", last_name='<img src=x onerror=alert("xss")>'),
    _case("xss_en_postal", postal_code='"><svg onload=alert(1)>'),
    _case("sqli_or_1_1", first_name="' OR 1=1 --", last_name="'; DROP TABLE users; --"),
    _case("caracteres_especiales", first_name="& ; < > \" '", last_name="%s %n {{7*7}}"),
]
