# QA Assistant: reglas del proyecto

Este repo es un framework de agentes de QA. Claude Code lee este archivo en cada sesión,
así que aquí van las reglas que **todos** los agentes deben respetar, sea cual sea el tipo
de prueba. Las reglas específicas están en el `CLAUDE.md` de cada carpeta:

| Carpeta   | Tipo de prueba | Reglas            |
|-----------|----------------|-------------------|
| `web/`    | E2E de navegador (Playwright) | `web/CLAUDE.md` |
| `api/`    | API REST/HTTP  | `api/CLAUDE.md`   |
| `mobile/` | Apps móviles   | `mobile/CLAUDE.md`|

## Estructura
- Cada sistema bajo prueba vive en su propia carpeta: `<tipo>/<nombre>/`
  (por ejemplo `web/saucedemo/`). `<nombre>` en `snake_case`, sin guiones (es un paquete Python).
- Dentro de cada sistema:
  - `conftest.py` con sus fixtures propias, incluida su `BASE_URL`.
  - `tests/features/*.feature`: casos en Gherkin, como documentación de qué se prueba.
  - `tests/<nivel>/test_*.py`: tests ejecutables.
- Todas las carpetas llevan `__init__.py` para que los nombres de test no choquen entre sistemas.
- Imports absolutos desde la raíz: `from web.saucedemo.pages.login_page import LoginPage`.

## Stack común
- Python 3.11+ y Pytest. `conftest.py` raíz solo carga `.env` (vía `python-dotenv`).

## Convenciones comunes
- Un test, un comportamiento. Nombres: `test_<accion>_<resultado_esperado>`.
- Cada escenario Gherkin tiene su test, con el nombre del escenario en el docstring.
- Marcar los tests con `@pytest.mark.smoke` o `@pytest.mark.regression`.
- Prohibido `time.sleep`: usa las esperas del framework de cada tipo de prueba.
- Configuración por variables de entorno con prefijo del sistema
  (`SAUCEDEMO_BASE_URL`, `SAUCEDEMO_USER`...) y un valor por defecto seguro en su `conftest.py`.
  Documenta cada variable nueva en `.env.example`.
- Datos de prueba sin información real (ni personas, ni tarjetas reales).

## Comandos
- Instalar: `pip install -r requirements.txt && playwright install chromium`
- Correr todo: `pytest`
- Un tipo o un sistema: `pytest web` · `pytest web/saucedemo`
- Solo smoke: `pytest -m smoke`

## Límites
- Los agentes proponen; una persona revisa y hace merge. Nunca hacer push a `main`.
- No leer ni escribir `.env`.
